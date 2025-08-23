from fastapi.testclient import TestClient
from fastapi_oidc.types import IDToken

import apps.api.main as main


class Token(IDToken):
    roles: list[str] = []


def _override(roles: list[str]):
    def _inner() -> Token:
        return Token(iss="iss", sub="sub", aud="aud", exp=0, iat=0, roles=roles)

    return _inner


def test_role_dependencies():
    client = TestClient(main.app)
    cases = [
        ("/roles/worker", "worker"),
        ("/roles/supervisor", "supervisor"),
        ("/roles/hsrep", "HS rep"),
        ("/roles/admin", "admin"),
    ]
    for path, role in cases:
        main.app.dependency_overrides[main.authenticate_user] = _override([role])
        assert client.get(path).status_code == 200
        main.app.dependency_overrides[main.authenticate_user] = _override([])
        assert client.get(path).status_code == 403
    main.app.dependency_overrides = {}
