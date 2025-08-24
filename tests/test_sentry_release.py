import importlib
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as pkg_version

import sentry_sdk
from fastapi.testclient import TestClient
from sentry_sdk.envelope import Envelope
from sentry_sdk.transport import Transport


def test_sentry_event_contains_release(monkeypatch):
    events = []

    class DummyTransport(Transport):
        def capture_event(self, event):  # type: ignore[override]
            events.append(event)

        def capture_envelope(self, envelope: Envelope):  # type: ignore[override]
            for item in envelope.items:
                if item.type == "event":
                    events.append(item.get_event())

    orig_init = sentry_sdk.init

    def fake_init(*args, **kwargs):
        kwargs["transport"] = DummyTransport()
        return orig_init(*args, **kwargs)

    monkeypatch.setenv("SENTRY_DSN", "https://example@sentry.invalid/1")
    monkeypatch.delenv("SENTRY_RELEASE", raising=False)
    monkeypatch.setattr(sentry_sdk, "init", fake_init)

    # Re-import app to trigger configure_logging with patched init
    import sys

    sys.modules.pop("apps.api.main", None)
    api_main = importlib.import_module("apps.api.main")

    @api_main.app.get("/boom")
    def boom():
        raise RuntimeError("boom")

    client = TestClient(api_main.app, raise_server_exceptions=False)
    client.get("/boom")

    assert events, "no event captured"
    try:
        expected_release = pkg_version("loto")
    except PackageNotFoundError:
        expected_release = "unknown"
    assert events[0]["release"] == expected_release
