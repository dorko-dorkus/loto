from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AdapterRequestError(Exception):
    """Structured HTTP error returned by adapters.

    Attributes
    ----------
    status_code:
        HTTP status code returned by the upstream service.
    retry_after:
        Number of seconds the client should wait before retrying, if
        provided by the service.
    """

    status_code: int
    retry_after: float | None

    def __str__(self) -> str:
        return f"HTTP error {self.status_code}"
