from starlette.requests import HTTPConnection

from patzilla.util.web.identity.config import AuthSettings
from patzilla.web.auth import resolve_user


def test_resolve_user_anonymous():
    conn = HTTPConnection({"type": "http", "headers": []})
    user, cookie_headers = resolve_user(conn, AuthSettings())
    assert user.is_authenticated is False
    assert cookie_headers == []
