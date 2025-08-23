from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "loto.db"


@dataclass(frozen=True)
class AuditRecord:
    """Represents a single audit log entry."""

    id: int | None
    user: str
    action: str
    timestamp: str


def add_record(*, user: str, action: str, db_path: Path = DB_PATH) -> None:
    """Insert an audit record into the database."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO audit_records (user, action) VALUES (?, ?)",
            (user, action),
        )
        conn.commit()
    finally:
        conn.close()


def export_records(
    bucket: str,
    prefix: str = "audit",
    *,
    db_path: Path = DB_PATH,
) -> str:
    """Export audit records to S3 with object lock enabled.

    The uploaded object is retained for seven years to satisfy compliance
    requirements.
    """
    import boto3  # imported lazily to avoid hard dependency during normal use

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT id, user, action, timestamp FROM audit_records ORDER BY id"
        ).fetchall()
    finally:
        conn.close()
    body = json.dumps(
        [
            {
                "id": r[0],
                "user": r[1],
                "action": r[2],
                "timestamp": r[3],
            }
            for r in rows
        ]
    ).encode("utf-8")
    s3 = boto3.client("s3")
    key = f"{prefix}/{datetime.now(tz=timezone.utc).isoformat()}.json"
    retain_until = datetime.now(tz=timezone.utc) + timedelta(days=365 * 7)
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=body,
        ObjectLockMode="COMPLIANCE",
        ObjectLockRetainUntilDate=retain_until,
    )
    return key


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Export audit logs to S3")
    parser.add_argument("bucket", help="Destination S3 bucket")
    parser.add_argument("--prefix", default="audit", help="Object prefix")
    args = parser.parse_args()
    export_records(args.bucket, prefix=args.prefix)
