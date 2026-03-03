from __future__ import annotations

import json
import sqlite3
import sys
import types
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, cast

from _pytest.monkeypatch import MonkeyPatch

from apps.api import audit


class ClientError(Exception):
    def __init__(self, response: dict[str, Any], operation: str) -> None:
        super().__init__(response)
        self.response = response
        self.operation_name = operation


class _StubS3:
    """Simple stub that fails once then succeeds."""

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def put_object(self, **kwargs: object) -> dict[str, dict[str, int]]:
        self.calls.append(kwargs)
        if len(self.calls) == 1:
            error_response = {
                "Error": {"Code": "500", "Message": "boom"},
                "ResponseMetadata": {"HTTPStatusCode": 500},
            }
            raise ClientError(error_response, "PutObject")
        return {"ResponseMetadata": {"HTTPStatusCode": 200}}


def _init_db(path: str) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE audit_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            action TEXT NOT NULL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def test_export_records_jsonl_and_retry(tmp_path: Path) -> None:
    db_path = tmp_path / "audit.db"
    _init_db(str(db_path))
    audit.add_record(user="alice", action="login", db_path=db_path)

    stub = _StubS3()
    sys.modules["boto3"] = cast(
        ModuleType, types.SimpleNamespace(client=lambda _name: stub)
    )
    exceptions = types.SimpleNamespace(ClientError=ClientError)
    sys.modules["botocore"] = cast(
        ModuleType,
        types.SimpleNamespace(exceptions=exceptions),
    )
    sys.modules["botocore.exceptions"] = cast(ModuleType, exceptions)

    key = audit.export_records(
        "bucket", prefix="audit-test", db_path=db_path, max_attempts=2
    )

    assert len(stub.calls) == 2
    uploaded = stub.calls[-1]

    body = cast(bytes, uploaded["Body"])
    lines = body.decode().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["user"] == "alice"

    today = datetime.now(timezone.utc)
    assert key.startswith("audit-test/")
    assert f"{today:%Y/%m/%d}" in key

    retain_until = cast(datetime, uploaded["ObjectLockRetainUntilDate"])
    assert retain_until - today >= timedelta(days=365 * 7 - 1)


def test_add_record_missing_table_logs_once_and_skips(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    db_path = tmp_path / "missing.db"
    audit._MISSING_TABLE_LOGGED = False
    events: list[str] = []

    def _fake_info(event: str, **kwargs: object) -> None:
        events.append(event)

    monkeypatch.setattr(audit.logger, "info", _fake_info)

    audit.add_record(user="alice", action="login", db_path=db_path)
    audit.add_record(user="bob", action="logout", db_path=db_path)

    assert events == ["audit_records_table_missing_skip_write"]


def test_add_record_existing_table_persists_row(tmp_path: Path) -> None:
    db_path = tmp_path / "audit.db"
    _init_db(str(db_path))

    audit.add_record(user="alice", action="login", db_path=db_path)

    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT user, action FROM audit_records").fetchone()
    conn.close()

    assert row == ("alice", "login")
