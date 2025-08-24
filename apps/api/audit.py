from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import os
import sqlite3
import time
from pathlib import Path

import structlog

DB_PATH = Path(__file__).resolve().parents[2] / "loto.db"


logger = structlog.get_logger(__name__)


def _redact(value: str) -> str:
    """Redact sensitive tokens from ``value``.

    Environment variables such as ``MAXIMO_APIKEY`` may be logged and must be
    removed prior to export.  Common secrets are replaced with ``[REDACTED]``.
    """

    patterns = [
        os.getenv("MAXIMO_APIKEY"),
        os.getenv("MAXIMO_BASE_URL"),
        "apikey",
        "password",
        "secret",
    ]
    redacted = value
    for p in patterns:
        if p:
            redacted = redacted.replace(p, "[REDACTED]")
    return redacted


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
    retention_years: int | None = None,
    max_attempts: int = 3,
) -> str:
    """Export audit records to S3 with object lock enabled.

    Parameters
    ----------
    bucket:
        Destination S3 bucket.
    prefix:
        Object key prefix.  Keys are further partitioned by ``YYYY/MM/DD``.
    db_path:
        Path to the SQLite database containing ``audit_records``.
    retention_years:
        Optional number of years to retain the uploaded object.  Defaults to the
        ``AUDIT_RETENTION_YEARS`` environment variable or 7 years if unset.
    max_attempts:
        Number of S3 upload attempts on 5xx errors.

    The uploaded object is retained for the configured number of years to
    satisfy compliance requirements.  Records are uploaded as JSON Lines (JSONL)
    format with one JSON object per line.
    """
    import boto3  # imported lazily to avoid hard dependency during normal use
    from botocore.exceptions import ClientError

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT id, user, action, timestamp FROM audit_records ORDER BY id"
        ).fetchall()
    finally:
        conn.close()

    body_lines = [
        json.dumps(
            {
                "id": r[0],
                "user": _redact(r[1]),
                "action": _redact(r[2]),
                "timestamp": r[3],
            }
        )
        for r in rows
    ]
    body = ("\n".join(body_lines) + "\n").encode("utf-8") if body_lines else b""

    now = datetime.now(tz=timezone.utc)
    key = f"{prefix}/{now:%Y/%m/%d}/{now.isoformat()}.jsonl"

    retention_years = retention_years or int(os.getenv("AUDIT_RETENTION_YEARS", "7"))
    retain_until = now + timedelta(days=365 * retention_years)

    logger.info(
        "uploading_audit_records",
        bucket=bucket,
        key=key,
        count=len(rows),
        retain_until=retain_until.isoformat(),
    )

    s3 = boto3.client("s3")
    attempt = 0
    while True:
        attempt += 1
        try:
            s3.put_object(
                Bucket=bucket,
                Key=key,
                Body=body,
                ObjectLockMode="COMPLIANCE",
                ObjectLockRetainUntilDate=retain_until,
            )
            break
        except ClientError as exc:  # pragma: no cover - network errors are rare
            status = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode", 0)
            if 500 <= status < 600 and attempt < max_attempts:
                time.sleep(2 ** (attempt - 1))
                continue
            raise
    return key


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Export audit logs to S3")
    parser.add_argument("bucket", help="Destination S3 bucket")
    parser.add_argument("--prefix", default="audit", help="Object prefix")
    args = parser.parse_args()
    export_records(args.bucket, prefix=args.prefix)
