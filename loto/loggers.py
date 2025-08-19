from __future__ import annotations

import contextvars
import json
import logging
from datetime import datetime, timezone
from typing import Any

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default=""
)
seed_var: contextvars.ContextVar[int | None] = contextvars.ContextVar(
    "seed", default=None
)
rule_hash_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "rule_hash", default=None
)


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        record.seed = seed_var.get()
        record.rule_hash = rule_hash_var.get()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data: dict[str, Any] = {
            "time": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname.lower(),
            "msg": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
            "seed": getattr(record, "seed", None),
            "rule_hash": getattr(record, "rule_hash", None),
        }
        return json.dumps(data)


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    handler.addFilter(ContextFilter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
