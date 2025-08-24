from __future__ import annotations

import contextvars
import logging
import os
import sys
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as pkg_version
from typing import Any, MutableMapping

import sentry_sdk
import structlog
from structlog.typing import Processor

# context variables for request scoped metadata
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default=""
)
seed_var: contextvars.ContextVar[int | None] = contextvars.ContextVar(
    "seed", default=None
)
rule_hash_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "rule_hash", default=None
)


def _add_context_vars(
    _: structlog.BoundLogger, __: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    """Inject custom context variables into structlog events."""

    event_dict.setdefault("request_id", request_id_var.get())
    event_dict.setdefault("seed", seed_var.get())
    event_dict.setdefault("rule_hash", rule_hash_var.get())
    return event_dict


def configure_logging() -> None:
    """Configure structured JSON logging using structlog."""

    timestamper = structlog.processors.TimeStamper(fmt="iso")
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        _add_context_vars,
        structlog.processors.add_log_level,
        timestamper,
        structlog.processors.EventRenamer("msg"),
        structlog.processors.JSONRenderer(),
    ]

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processor=structlog.processors.JSONRenderer(),
            foreign_pre_chain=processors[:-1],
        )
    )

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)

    dsn = os.getenv("SENTRY_DSN")
    if dsn:
        release = os.getenv("SENTRY_RELEASE")
        if not release:
            try:
                release = pkg_version("loto")
            except PackageNotFoundError:
                release = "unknown"
        sentry_sdk.init(dsn=dsn, release=release)
