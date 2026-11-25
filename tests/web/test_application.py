"""
Integration tests for the web application, see `patzilla.web.app`.
"""
import datetime
from urllib.parse import parse_qs, urlsplit

import pytest
from fastapi.testclient import TestClient

from patzilla.util.web.identity.config import AuthSettings
from patzilla.util.web.identity.magic_link import request_magic_link
from patzilla.util.web.identity.session import authenticate_session
from patzilla.util.web.identity.store import UserSession
from patzilla.web.app import app_from_config
from patzilla.web.config import read_ini

from tests.util.test_magic_link import memory_db  # noqa: F401  (pytest fixture)


CONFIGURATION = """
[ip_navigator]
vendors = patzilla
datasources = ops, depatisnet, espacenet
development_mode = true

[vendor:patzilla]
organization = PatZilla
productname = PatZilla IP Navigator
productname_html = <span class="header-logo">PatZilla</span>
page_title = Patent search
copyright_html = &copy; The PatZilla Developers
stylesheet_uri = /static/patzilla.css

[auth]
magic_link_enabled = true
magic_link_allow_signup = true
log_magic_link_in_dev = true

[smtp]
hostname = {smtp_hostname}

[email_addressbook]
support = support@example.org
purchase = purchase@example.org

[filter:prefix-middleware]
use = egg:PasteDeploy#prefix

[app:main]
use = egg:patzilla#web
filter-with = prefix-middleware
mongodb.patzilla.uri = mongodb://localhost:27017/patzilla_testing
cache.regions = search, static
cache.search.type = memory
cache.search.expire = 7200
cache.static.type = memory
cache.static.expire = 2592000

[server:main]
use = egg:waitress#main
host = 127.0.0.1
port = 6543
threads = 8
"""

# The routes of the Pyramid application, in matching order, as recorded before the migration.
PYRAMID_ROUTES = [
    ('favicon', []), ('admin-user-create', []), ('login', []), ('auth-magic-verify', []), ('logout', []),
    ('help-hotkeys', []), ('help-ificlaims', []), ('patentsearch', []), ('embedded-item', []),
    ('embedded-list', []), ('patentview', []), ('patentsearch-vanity', []), ('patentsearch-quick', []),
    ('patentsearch-quick2', []), ('static', []), ('auth-magic-verify-root', []), ('logout-root', []),
    ('jump-office', []),
    ('status_espacenet', ['GET', 'HEAD']),
    ('sip-published-data-crawl', ['GET', 'HEAD', 'POST']),
    ('sip-published-data-search', ['GET', 'HEAD', 'POST']),
    ('opaquelinks-token', ['POST']),
    ('opaquelinks-verify', ['POST']),
    ('admin-users-email-service', ['GET', 'HEAD']),
    ('ops-usage', ['GET', 'HEAD']),
    ('analytics-applicants-distinct', ['GET', 'HEAD']),
    ('analytics-daterange', ['GET', 'HEAD']),
    ('analytics-applicant-family', ['GET', 'HEAD']),
    ('drawing', ['GET', 'HEAD']),
    ('pdf', ['GET', 'HEAD']),
    ('depatech-published-data-crawl', ['GET', 'HEAD', 'POST']),
    ('depatech-published-data-search', ['GET', 'HEAD', 'POST']),
    ('status_depatech', ['GET', 'HEAD']),
    ('depatisconnect-abstract', ['GET', 'HEAD']),
    ('depatisconnect-claims', ['GET', 'HEAD']),
    ('depatisconnect-description', ['GET', 'HEAD']),
    ('depatisnet-published-data-crawl', ['GET', 'HEAD', 'POST']),
    ('depatisnet-published-data-search', ['GET', 'HEAD', 'POST']),
    ('dpma-register', ['GET', 'HEAD']),
    ('status_depatisconnect', ['GET', 'HEAD']),
    ('status_depatisnet', ['GET', 'HEAD']),
    ('status_dpmaregister', ['GET', 'HEAD']),
    ('espacenet-abstract', ['GET', 'HEAD']),
    ('espacenet-claims', ['GET', 'HEAD']),
    ('espacenet-description', ['GET', 'HEAD']),
    ('google-published-data-search', ['GET', 'HEAD']),
    ('ificlaims-deliver', ['GET', 'HEAD']),
    ('ificlaims-download', ['GET', 'HEAD']),
    ('ificlaims-published-data-crawl', ['GET', 'HEAD', 'POST']),
    ('ificlaims-published-data-search', ['GET', 'HEAD', 'POST']),
    ('status_ificlaims', ['GET', 'HEAD']),
    ('ops-claims', ['GET', 'HEAD']),
    ('ops-description', ['GET', 'HEAD']),
    ('ops-family-inpadoc', ['GET', 'HEAD']),
    ('ops-fullimage', ['GET', 'HEAD']),
    ('ops-image-info', ['GET', 'HEAD']),
    ('ops-kindcodes', ['GET', 'HEAD']),
    ('ops-pdf', ['GET', 'HEAD']),
    ('ops-published-data-crawl', ['GET', 'HEAD']),
    ('ops-published-data-search', ['GET', 'HEAD']),
    ('ops-register', ['GET', 'HEAD']),
    ('status_ops', ['GET', 'HEAD']),
    ('publicationserver-pdf', ['GET', 'HEAD']),
    ('export-utility-service', ['POST']),
    ('issue-reporter-service', ['POST']),
    ('numberlist-utility-service', ['POST']),
    ('query-expression-utility-service', ['POST']),
    ('identity-auth', ['POST']),
    ('identity-logout', ['POST']),
    ('identity-magic-link', ['POST']),
    ('identity-pwhash', ['GET', 'HEAD']),
    ('identity-session', ['GET', 'HEAD']),
]


@pytest.fixture
def configfile(tmp_path):
    path = tmp_path / "patzilla.ini"
    path.write_text(CONFIGURATION)
    return str(path)


@pytest.fixture
def app(configfile):
    return app_from_config(configfile)


@pytest.fixture
def client(app):
    return TestClient(app, base_url="http://patzilla.example.org")


def test_read_ini(configfile):
    ini = read_ini(configfile)
    assert ini.flavor == "web"
    assert ini.settings["mongodb.patzilla.uri"] == "mongodb://localhost:27017/patzilla_testing"
    assert "use" not in ini.settings
    assert ini.proxy is not None
    assert (ini.server.host, ini.server.port, ini.server.threads) == ("127.0.0.1", 6543, 8)


def test_read_ini_ignores_unsupported_filters(tmp_path):
    path = tmp_path / "patzilla.ini"
    path.write_text(CONFIGURATION.replace("filter-with = prefix-middleware", "filter-with = translogger")
                    + "\n[filter:translogger]\nuse = egg:Paste#translogger\n")
    assert read_ini(str(path)).proxy is None


def test_route_table_matches_pyramid(app):
    """
    The routes must be matched in the same order as before, with the same HTTP methods.
    `portfolio-demo` has been served by traversal before, now it has an explicit route.
    """
    routes = []
    for route in app.router.routes:
        if route.name == "portfolio-demo":
            continue
        methods = sorted(route.methods) if route.path.startswith("/api/") else []
        routes.append((route.name, methods))
    assert routes == PYRAMID_ROUTES


def test_openapi_disabled_by_default(client):
    assert client.get("/api/openapi.json").status_code == 404
    assert client.get("/api/docs").status_code == 404


def test_openapi_enabled(tmp_path):
    path = tmp_path / "patzilla.ini"
    path.write_text(CONFIGURATION.replace("[app:main]\n", "[app:main]\napi.docs = true\n"))
    client = TestClient(app_from_config(str(path)))
    schema = client.get("/api/openapi.json").json()
    assert "/api/identity/session" in schema["paths"]
    assert not any(path.startswith("/navigator") for path in schema["paths"])


def test_lifespan(app):
    with TestClient(app) as client:
        assert client.get("/api/identity/session").status_code == 200
    assert app.state.registry._started is True


def test_pages(client):
    response = client.get("/navigator/login?came_from=https://evil.example")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=UTF-8"
    assert "PatZilla IP Navigator" in response.text
    assert "evil.example" not in response.text

    response = client.get("/navigator/")
    assert response.status_code == 200
    assert "var navigator_configuration" in response.text

    assert client.get("/navigator/help/hotkeys").status_code == 200
    assert client.get("/portfolio-demo?query=foo").status_code == 200


def test_vanity_redirect(client):
    response = client.get("/navigator/pn/EP666666", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "http://patzilla.example.org/?query=pn%3DEP666666"


def test_static_files(client):
    response = client.get("/static/patzilla.css")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "max-age=0, must-revalidate, no-cache, no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert client.get("/static/does-not-exist.css").status_code == 404


def test_not_found(client):
    response = client.get("/api/nonexistent", headers={"Accept": "application/json"})
    assert response.status_code == 404
    assert response.json() == {
        "message": "The resource could not be found.\n\n\n/api/nonexistent\n\n",
        "code": "404 Not Found",
        "title": "Not Found",
    }


def test_proxy_headers(client):
    """
    The reverse proxy middleware evaluates `X-Forwarded-*` headers, like `PasteDeploy#prefix` did.
    """
    response = client.get("/navigator/pn/EP666666", follow_redirects=False, headers={
        "X-Forwarded-Host": "patents.example.com",
        "X-Forwarded-Proto": "https",
    })
    assert response.headers["location"] == "https://patents.example.com/?query=pn%3DEP666666"


def test_proxy_prefix(tmp_path):
    path = tmp_path / "patzilla.ini"
    path.write_text(CONFIGURATION.replace("use = egg:PasteDeploy#prefix\n", "use = egg:PasteDeploy#prefix\nprefix = /patzilla\n"))
    client = TestClient(app_from_config(str(path)), base_url="http://patzilla.example.org")
    assert client.get("/patzilla/api/identity/session").json() == {"authenticated": False, "user": None}
    response = client.get("/patzilla/navigator/logout", follow_redirects=False)
    assert response.headers["location"] == "http://patzilla.example.org/login"


def test_magic_link_end_to_end(client, memory_db):  # noqa: F811
    """
    Sign in using an email magic link, and use the session cookie, all over HTTP.
    """

    # 1. Request a magic link. The response is neutral.
    response = client.post("/api/identity/magic-link", json={"email": "founder@example.org", "came_from": "/navigator/"})
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert len(memory_db.tokens.docs) == 1

    # Invalid email addresses are rejected using the error envelope.
    response = client.post("/api/identity/magic-link", data={"email": "not-an-email"})
    assert response.status_code == 400
    assert response.json()["status"] == "error"

    # Create a link where the raw token is known.
    captured = {}
    result = request_magic_link(
        email="founder2@example.org",
        settings=AuthSettings(),
        base_url="http://patzilla.example.org",
        came_from="/navigator/?query=battery",
        send_mail_fn=lambda **kw: captured.update(kw) or True,
    )
    raw_token = parse_qs(urlsplit(result.verify_url).query)["token"][0]

    # 2. GET renders a confirmation page, without consuming the token.
    response = client.get(f"/auth/magic/verify?token={raw_token}")
    assert response.status_code == 200
    assert "founder2@example.org" in response.text

    # 3. POST consumes the token, sets the session cookie, and redirects.
    response = client.post("/navigator/auth/magic/verify", data={"token": raw_token}, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "http://patzilla.example.org/navigator/?query=battery"
    set_cookie = response.headers["set-cookie"]
    assert "patzilla_session=" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "SameSite=Lax" in set_cookie
    session_token = response.cookies["patzilla_session"]

    # 4. The session cookie authenticates subsequent requests.
    response = client.get("/api/identity/session", cookies={"patzilla_session": session_token})
    assert response.json()["authenticated"] is True
    assert response.json()["user"]["email"] == "founder2@example.org"

    # 5. Replaying the token fails.
    response = client.post("/auth/magic/verify", data={"token": raw_token}, follow_redirects=False)
    assert response.status_code == 200
    assert "already been used" in response.text

    # 6. Sliding renewal: When the session is about to expire, the cookie is renewed.
    session = memory_db.sessions.docs[0]
    assert isinstance(session, UserSession)
    session.expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
    response = client.get("/api/identity/session", cookies={"patzilla_session": session_token})
    assert response.json()["authenticated"] is True
    assert f"patzilla_session={session_token}" in response.headers["set-cookie"]

    # 7. Logout revokes the session and clears the cookie.
    response = client.post("/api/identity/logout", cookies={"patzilla_session": session_token})
    assert response.json() == {"status": "ok"}
    assert response.headers["set-cookie"].startswith("patzilla_session=; Max-Age=0")
    assert authenticate_session(session_token, AuthSettings()) == (None, None, False)

    # 8. A revoked session cookie is cleared on the next request.
    response = client.get("/api/identity/session", cookies={"patzilla_session": session_token})
    assert response.json()["authenticated"] is False
    assert response.headers["set-cookie"].startswith("patzilla_session=; Max-Age=0")
