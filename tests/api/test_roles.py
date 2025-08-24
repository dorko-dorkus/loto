import importlib
from fastapi.testclient import TestClient
from fastapi_oidc.types import IDToken

import apps.api.main as main


class Token(IDToken):
    email: str | None = None
    roles: list[str] = []


def _override(roles: list[str]):
    def _inner(*args, **kwargs) -> Token:
        return Token(
            iss="iss",
            sub="sub",
            aud="aud",
            exp=0,
            iat=0,
            roles=roles,
            email="user@example.com",
        )

    return _inner


def test_role_dependencies(monkeypatch):
    importlib.reload(main)
    client = TestClient(main.app)
    cases = [
        ("/roles/worker", "worker"),
        ("/roles/supervisor", "supervisor"),
        ("/roles/hsrep", "HS rep"),
        ("/roles/admin", "admin"),
    ]
    for path, role in cases:
        monkeypatch.setattr(main, "authenticate_user", _override([role]))
        assert (
            client.get(path, headers={"Authorization": "Bearer x"}).status_code == 200
        )
        monkeypatch.setattr(main, "authenticate_user", _override([]))
        assert (
            client.get(path, headers={"Authorization": "Bearer x"}).status_code == 403
        )
