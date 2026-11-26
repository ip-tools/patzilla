"""
Integration tests for the web application, see `patzilla.web`.
"""
import pytest
from fastapi.testclient import TestClient

from patzilla.web.app import create_app
from patzilla.web.settings import WebSettings

from tests.conftest import WEB_CONFIGURATION

# The routes of the former Pyramid application in matching order, with their HTTP methods.
PYRAMID_ROUTES = [
    ('favicon', []),
    ('admin-user-create', []),
    ('login', []),
    ('auth-magic-verify', []),
    ('logout', []),
    ('help-hotkeys', []),
    ('help-ificlaims', []),
    ('patentsearch', []),
    ('embedded-item', []),
    ('embedded-list', []),
    ('patentview', []),
    ('patentsearch-vanity', []),
    ('patentsearch-quick', []),
    ('patentsearch-quick2', []),
    ('static', []),
    ('auth-magic-verify-root', []),
    ('logout-root', []),
    ('jump-office', []),
    ('status_espacenet', ['GET']),
    ('sip-published-data-crawl', ['GET', 'POST']),
    ('sip-published-data-search', ['GET', 'POST']),
    ('opaquelinks-token', ['POST']),
    ('opaquelinks-verify', ['POST']),
    ('admin-users-email-service', ['GET']),
    ('ops-usage', ['GET']),
    ('analytics-applicants-distinct', ['GET']),
    ('analytics-daterange', ['GET']),
    ('analytics-applicant-family', ['GET']),
    ('drawing', ['GET']),
    ('pdf', ['GET']),
    ('depatech-published-data-crawl', ['GET', 'POST']),
    ('depatech-published-data-search', ['GET', 'POST']),
    ('status_depatech', ['GET']),
    ('depatisconnect-abstract', ['GET']),
    ('depatisconnect-claims', ['GET']),
    ('depatisconnect-description', ['GET']),
    ('depatisnet-published-data-crawl', ['GET', 'POST']),
    ('depatisnet-published-data-search', ['GET', 'POST']),
    ('dpma-register', ['GET']),
    ('status_depatisconnect', ['GET']),
    ('status_depatisnet', ['GET']),
    ('status_dpmaregister', ['GET']),
    ('espacenet-abstract', ['GET']),
    ('espacenet-claims', ['GET']),
    ('espacenet-description', ['GET']),
    ('google-published-data-search', ['GET']),
    ('ificlaims-deliver', ['GET']),
    ('ificlaims-download', ['GET']),
    ('ificlaims-published-data-crawl', ['GET', 'POST']),
    ('ificlaims-published-data-search', ['GET', 'POST']),
    ('status_ificlaims', ['GET']),
    ('ops-claims', ['GET']),
    ('ops-description', ['GET']),
    ('ops-family-inpadoc', ['GET']),
    ('ops-fullimage', ['GET']),
    ('ops-image-info', ['GET']),
    ('ops-kindcodes', ['GET']),
    ('ops-pdf', ['GET']),
    ('ops-published-data-crawl', ['GET']),
    ('ops-published-data-search', ['GET']),
    ('ops-register', ['GET']),
    ('status_ops', ['GET']),
    ('publicationserver-pdf', ['GET']),
    ('export-utility-service', ['POST']),
    ('issue-reporter-service', ['POST']),
    ('numberlist-utility-service', ['POST']),
    ('query-expression-utility-service', ['POST']),
    ('identity-auth', ['POST']),
    ('identity-logout', ['POST']),
    ('identity-magic-link', ['POST']),
    ('identity-pwhash', ['GET']),
    ('identity-session', ['GET']),
]


def make_client(tmp_path, configuration=WEB_CONFIGURATION):
    path = tmp_path / "patzilla.ini"
    path.write_text(configuration)
    return TestClient(create_app(WebSettings.from_ini(path)), base_url="http://patzilla.example.org")


def test_settings(web_configfile):
    settings = WebSettings.from_ini(web_configfile)
    assert settings.flavor == "web"
    assert settings.mongodb_uri == "mongodb://localhost:27017/patzilla_testing"
    assert settings.proxy is not None
    assert (settings.server.host, settings.server.port, settings.server.threads) == ("127.0.0.1", 6543, 8)


def test_settings_unsupported_filter(tmp_path):
    path = tmp_path / "patzilla.ini"
    path.write_text(WEB_CONFIGURATION.replace("use = egg:PasteDeploy#prefix", "use = egg:Paste#translogger"))
    with pytest.raises(ValueError, match="Unsupported filter"):
        WebSettings.from_ini(path)


def test_routes_match_pyramid(web_app):
    """
    The same routes as before, with the same HTTP methods. Page routes are matched in the same order.
    `portfolio-demo` has been served by traversal before, now it has an explicit route.
    """
    def flatten(routes):
        for route in routes:
            nested = getattr(route, "original_router", None)
            yield from flatten(nested.routes) if nested is not None else [route]

    routes = []
    for route in flatten(web_app.router.routes):
        name = getattr(route, "name", None)
        if name in ("portfolio-demo", "openapi", "swagger_ui_html") or (routes and routes[-1][0] == name):
            continue
        methods = sorted(route.methods) if route.path.startswith("/api/") else []
        routes.append((name, methods))
    pages = [route for route in routes if not route[1]]
    assert pages == [route for route in PYRAMID_ROUTES if not route[1]]
    assert sorted(routes) == sorted(PYRAMID_ROUTES)


def test_openapi_disabled_by_default(web_client):
    assert web_client.get("/api/openapi.json").status_code == 404


def test_openapi_enabled(tmp_path):
    with make_client(tmp_path, WEB_CONFIGURATION.replace("[app:main]\n", "[app:main]\napi.docs = true\n")) as client:
        schema = client.get("/api/openapi.json").json()
    assert "/api/ops/published-data/search" in schema["paths"]
    parameters = {p["name"] for p in schema["paths"]["/api/ops/published-data/search"]["get"]["parameters"]}
    assert {"expression", "constituents", "range", "family_swap_default"} <= parameters
    assert not any(path.startswith("/navigator") for path in schema["paths"])


def test_pages(web_client):
    response = web_client.get("/navigator/login")
    assert response.status_code == 200
    assert "PatZilla IP Navigator" in response.text
    assert web_client.get("/navigator/help/hotkeys").status_code == 200
    assert web_client.get("/navigator/embed/item").status_code == 200
    assert web_client.get("/navigator/view/pn/EP666666").status_code == 200
    assert web_client.get("/portfolio-demo?query=foo").status_code == 200


def test_vanity_redirect(web_client):
    response = web_client.get("/navigator/pn/EP666666", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/?query=pn%3DEP666666"
    assert web_client.get("/navigator/a/b/c.map", follow_redirects=False).status_code == 404


def test_static_files(web_client):
    response = web_client.get("/static/patzilla.css")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "max-age=0, must-revalidate, no-cache, no-store"
    assert response.headers["x-content-type-options"] == "nosniff"


def test_api_errors_use_envelope(web_client):
    response = web_client.get("/api/nonexistent")
    assert response.status_code == 404
    assert response.json() == {"status": "error", "errors": [
        {"location": "http", "name": "Not Found", "description": "Not Found"}]}

    response = web_client.get("/api/identity/auth")
    assert response.status_code == 405
    assert response.json()["errors"][0]["name"] == "Method Not Allowed"

    response = web_client.get("/api/google/published-data/search?range_begin=foo")
    assert response.status_code == 400
    assert response.json()["errors"][0]["location"] == "query"


def test_upstream_not_configured(web_client, monkeypatch):
    for name in ("OPS_API_CONSUMER_KEY", "OPS_API_CONSUMER_SECRET"):
        monkeypatch.delenv(name, raising=False)
    response = web_client.get("/api/ops/EP666666/claims")
    assert response.status_code == 502
    assert response.json()["errors"][0]["description"] == "EPO OPS: Data source not enabled or not configured"


def test_proxy_headers(web_client):
    response = web_client.post("/api/identity/magic-link", data={"email": "invalid"},
                               headers={"X-Forwarded-Proto": "https", "X-Forwarded-For": "192.0.2.1"})
    assert response.status_code == 400


def test_proxy_prefix(tmp_path):
    configuration = WEB_CONFIGURATION.replace("use = egg:PasteDeploy#prefix\n", "use = egg:PasteDeploy#prefix\nprefix = /patzilla\n")
    with make_client(tmp_path, configuration) as client:
        assert client.get("/patzilla/api/identity/session").json() == {"authenticated": False, "user": None}
