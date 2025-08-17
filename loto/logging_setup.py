"""Structured JSON logging utilities for LOTO.

This module configures the root logger to emit JSON formatted log lines and
provides a small convenience wrapper with a ``bind`` method for attaching
context to subsequent log records. It is intentionally lightweight and avoids
external dependencies such as structlog.

Usage
-----
>>> from loto.logging_setup import get_logger, init_logging
>>> init_logging(verbosity=1)
>>> log = get_logger().bind(wo="WO1", asset="A-1", rule_hash="deadbeef")
>>> log.info("starting")
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any, Dict, Mapping, MutableMapping, Optional, cast


class JsonFormatter(logging.Formatter):
    """Format log records as single-line JSON."""

    #: Logging record attributes that should not be included in the JSON output.
    _reserved = {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
    }

    def format(self, record: logging.LogRecord) -> str:  # pragma: no cover - trivial
        data: Dict[str, Any] = {
            "level": record.levelname,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in self._reserved:
                data[key] = value
        return json.dumps(data, ensure_ascii=False)


class ContextLogger(logging.LoggerAdapter):
    """Logger adapter supporting ``bind`` similar to structlog."""

    def bind(self, **new_context: Any) -> "ContextLogger":
        merged = {**(self.extra or {}), **new_context}
        return ContextLogger(self.logger, merged)

    def process(
        self, msg: Any, kwargs: MutableMapping[str, Any]
    ) -> tuple[Any, MutableMapping[str, Any]]:
        """Merge bound context with any ``extra`` provided at log call time."""

        extra: Dict[str, Any] = dict(self.extra or {})
        user_extra = kwargs.get("extra")
        if user_extra is not None:
            extra.update(cast(Mapping[str, Any], user_extra))
        kwargs["extra"] = extra
        return msg, kwargs


def get_logger(name: Optional[str] = None) -> ContextLogger:
    """Return a :class:`ContextLogger` wrapping the named logger."""

    base = logging.getLogger(name)
    return ContextLogger(base, {})


def init_logging(verbosity: int = 0) -> None:
    """Initialise JSON logging for the CLI.

    Parameters
    ----------
    verbosity:
        Verbosity level. ``0`` maps to ``WARNING``; ``1`` maps to ``INFO``;
        ``2`` or higher maps to ``DEBUG``.
    """

    level = logging.WARNING
    if verbosity >= 2:
        level = logging.DEBUG
    elif verbosity == 1:
        level = logging.INFO

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    # ``force=True`` ensures reconfiguration when called multiple times.
    logging.basicConfig(level=level, handlers=[handler], force=True)
