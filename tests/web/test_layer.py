"""
Unit tests for the building blocks of the web layer, see `patzilla.web`.
"""
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from patzilla.web.accept import Accept
from patzilla.web.context import get_current_registry, get_current_request, request_context
from patzilla.web.errors import Errors, JSONError, json_error
from patzilla.web.exceptions import HTTPBadGateway, HTTPFound, HTTPNotFound
from patzilla.web.registry import Registry
from patzilla.web.request import MultiDict, Request
from patzilla.web.response import Response
from patzilla.web.routing import RouteTable, convert_path
from patzilla.web.service import Service
from patzilla.web.testing import DummyRequest


def make_client(*entries) -> TestClient:
    """
    Build a bare application from route tables and services, without configuration file.
    """
    from patzilla.web.app import create_app

    registry = Registry()
    for entry in entries:
        if isinstance(entry, RouteTable):
            registry.add_routes(entry)
        else:
            registry.add_services(entry)
    return TestClient(create_app(registry), base_url="http://patzilla.example.org")


# ------------------------------------------
#   Accept header negotiation
# ------------------------------------------
def test_accept_missing_header_accepts_everything():
    assert Accept(None).acceptable_offers(["text/xml", "application/json"]) == [
        ("text/xml", 1.0), ("application/json", 1.0)]


def test_accept_quality_and_specificity():
    accept = Accept("application/json, text/javascript, */*; q=0.01")
    assert accept.best_match(["text/xml", "application/json"]) == "application/json"
    assert accept.acceptable_offers(["text/xml"]) == [("text/xml", 0.01)]


def test_accept_exclusion():
    accept = Accept("text/html, application/json;q=0")
    assert accept.acceptable_offers(["application/json"]) == []


def test_accept_invalid_header_accepts_everything():
    assert Accept("foo").acceptable_offers(["text/plain"]) == [("text/plain", 1.0)]


# ------------------------------------------
#   Request
# ------------------------------------------
def test_request_params_query_and_form():
    request = Request(
        method="POST",
        query_string="a=1&b=2&b=3",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        body=b"a=form&c=4",
    )
    assert request.GET.getall("b") == ["2", "3"]
    assert request.GET["b"] == "3"
    assert request.POST["c"] == "4"
    # Query parameters take precedence, like with WebOb.
    assert request.params["a"] == "1"
    assert request.params["c"] == "4"
    assert dict(request.params.copy()) == {"a": "form", "b": "3", "c": "4"}


def test_request_params_mutation():
    request = Request(method="POST", query_string="a=1",
                      headers={"Content-Type": "application/x-www-form-urlencoded"}, body=b"b=2")
    request.params["c"] = "3"
    assert request.params.items() == [("a", "1"), ("b", "2"), ("c", "3")]


def test_request_path_quoting_like_webob():
    request = Request(path="/navigator/view/pn/US:123 4")
    assert request.path == "/navigator/view/pn/US:123%204"


def test_request_json_body():
    request = DummyRequest(json={"foo": "bar"})
    assert request.method == "POST"
    assert request.content_type == "application/json"
    assert request.json == {"foo": "bar"}
    assert request.json_body == {"foo": "bar"}


def test_request_body_assignment_invalidates_parsed_body():
    request = DummyRequest(json={"foo": "bar"})
    request.body = b'{"foo": "baz"}'
    assert request.json == {"foo": "baz"}


def test_request_urls():
    request = Request(path="/navigator/", query_string="query=foo", host="patzilla.example.org:443",
                      scheme="https", script_name="/app")
    assert request.host_url == "https://patzilla.example.org"
    assert request.application_url == "https://patzilla.example.org/app"
    assert request.path_url == "https://patzilla.example.org/app/navigator/"
    assert request.url == "https://patzilla.example.org/app/navigator/?query=foo"
    assert request.host_port == "443"
    assert request.domain == "patzilla.example.org"


def test_request_client_addr():
    assert Request(remote_addr="10.0.0.1").client_addr == "10.0.0.1"
    assert Request(remote_addr="10.0.0.1", headers={"X-Forwarded-For": "192.0.2.1, 10.0.0.2"}).client_addr == "192.0.2.1"


def test_request_lazy_methods():
    registry = Registry()
    calls = []

    def answer(request):
        calls.append(request)
        return 42

    registry.add_request_method(answer)
    request = Request(registry=registry)
    assert request.answer == 42
    assert request.answer == 42
    assert len(calls) == 1
    assert not hasattr(request, "unknown")


def test_multidict():
    data = MultiDict([("a", "1"), ("a", "2"), ("b", "3")])
    assert data["a"] == "2"
    assert data.getall("a") == ["1", "2"]
    assert data.mixed() == {"a": ["1", "2"], "b": "3"}
    data["a"] = "x"
    assert data.getall("a") == ["x"]
    del data["b"]
    assert "b" not in data


def test_context():
    request = DummyRequest()
    assert get_current_request() is not request
    with request_context(request):
        assert get_current_request() is request
        assert get_current_registry() is request.registry
    assert get_current_request() is not request


# ------------------------------------------
#   Responses and exceptions
# ------------------------------------------
def test_response_cookies():
    response = Response()
    response.set_cookie(name="session", value="abc", max_age=60, httponly=True, secure=True, samesite="Lax")
    response.delete_cookie(name="other")
    cookies = response.headers.getlist("Set-Cookie")
    assert cookies[0].startswith("session=abc; ")
    assert "HttpOnly" in cookies[0] and "Secure" in cookies[0] and "SameSite=Lax" in cookies[0]
    assert cookies[1] == "other=; Max-Age=0; Path=/; expires=Wed, 31-Dec-97 23:59:59 GMT"


def test_response_cookie_deletion_retains_attributes():
    response = Response()
    response.set_cookie("__Secure-x", None, secure=True, samesite="None")
    assert response.headers["Set-Cookie"] == \
        "__Secure-x=; Max-Age=0; Path=/; expires=Wed, 31-Dec-97 23:59:59 GMT; Secure; SameSite=None"


def test_render_mapping_without_renderer_fails():
    from patzilla.web.render import render
    with pytest.raises(TypeError):
        render(DummyRequest(), {"a": 1}, None)


def test_response_content_type_header():
    response = Response(body=b"{}", content_type="application/json")
    assert response.content_type_header == "application/json"
    response = Response(body="hello", content_type="text/plain")
    assert response.content_type_header == "text/plain; charset=UTF-8"
    response = Response(body="hello", content_type="application/octet-stream", charset="utf-8")
    assert response.content_type_header == "application/octet-stream; charset=utf-8"


@pytest.mark.parametrize("accept,content_type,body", [
    (None, "text/plain; charset=UTF-8",
     b"404 Not Found\n\nThe resource could not be found.\n\n\nSome detail\n\n"),
    ("application/json", "application/json",
     b'{"message": "The resource could not be found.\\n\\n\\nSome detail\\n\\n", "code": "404 Not Found", "title": "Not Found"}'),
    ("text/html", "text/html; charset=UTF-8",
     b"<html>\n <head>\n  <title>404 Not Found</title>\n </head>\n <body>\n  <h1>404 Not Found</h1>\n"
     b"  The resource could not be found.<br/><br/>\nSome detail\n\n\n </body>\n</html>"),
])
def test_exception_rendering_matches_pyramid(accept, content_type, body):
    response = HTTPNotFound("Some detail").to_starlette(accept=accept)
    assert response.status_code == 404
    assert response.headers["Content-Type"] == content_type
    assert response.body == body


def test_redirect_location_made_absolute():
    response = HTTPFound(location="/login").to_starlette(base_url="https://patzilla.example.org/navigator/logout")
    assert response.status_code == 302
    assert response.headers["Location"] == "https://patzilla.example.org/login"
    assert response.body == b"302 Found\n\nThe resource was found at /login; you should be redirected automatically.\n\n"


def test_json_error():
    request = DummyRequest()
    request.errors.add("ops-search", "http-response", {"content": b"bytes"})
    error = json_error(request)
    assert isinstance(error, JSONError)
    assert error.status_code == 400
    assert error.json == {"status": "error", "errors": [
        {"location": "ops-search", "name": "http-response", "description": {"content": "bytes"}}]}


# ------------------------------------------
#   Routing
# ------------------------------------------
def test_convert_path():
    assert convert_path("/api/{patent}/claims") == "/api/{patent}/claims"
    assert convert_path("navigator/{label}") == "/navigator/{label}"
    converted = convert_path(r"/api/crawl{dummy1:\/?}{constituents:.*?}")
    assert converted.startswith("/api/crawl{dummy1:re_")


def test_route_table_dispatch_and_predicates():
    routes = RouteTable(prefix="/navigator")
    routes.add("home", "/", lambda request: "standalone", renderer="null")
    routes.add("home", "/", lambda request: b"%PDF", renderer="pdf", request_param="pdf=true")
    routes.add("quick", "/{field}/{value}", lambda request: HTTPFound(location="/?" + request.matchdict["value"]),
               path_info=r"^(?!.*\.map).*$")
    client = make_client(routes)

    response = client.get("/navigator/")
    assert response.text == "standalone"
    assert response.headers["content-type"] == "text/html; charset=UTF-8"

    response = client.get("/navigator/?pdf=true")
    assert response.content == b"%PDF"
    assert response.headers["content-type"] == "application/pdf"

    response = client.get("/navigator/pn/EP666666", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "http://patzilla.example.org/?EP666666"

    response = client.get("/navigator/static/foo.map")
    assert response.status_code == 404
    assert response.headers["x-content-type-options"] == "nosniff"


# ------------------------------------------
#   Services
# ------------------------------------------
def test_service_json_rendering_and_response_headers():
    service = Service(name="test-search", path="/api/test/{patent}/search")

    @service.get()
    def handler(request):
        request.response.headers["X-PatZilla-Query-Keywords"] = json.dumps(["foo"])
        return {"patent": request.matchdict["patent"], "range": request.params.get("range")}

    client = make_client(service)
    response = client.get("/api/test/EP666666/search?range=1-10")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.headers["x-patzilla-query-keywords"] == '["foo"]'
    assert response.json() == {"patent": "EP666666", "range": "1-10"}

    response = client.get("/api/test/EP666666/search", headers={"Accept": "text/plain"})
    assert response.headers["content-type"] == "text/plain; charset=UTF-8"

    response = client.head("/api/test/EP666666/search")
    assert response.status_code == 200


def test_service_error_envelope():
    service = Service(name="test-errors", path="/api/test/errors")

    @service.post()
    def handler(request):
        request.response.headers["X-Discarded"] = "true"
        request.errors.add("test-service", "query", "Something went wrong")
        request.errors.status = 422

    client = make_client(service)
    response = client.post("/api/test/errors")
    assert response.status_code == 422
    assert "x-discarded" not in response.headers
    assert response.json() == {"status": "error", "errors": [
        {"location": "test-service", "name": "query", "description": "Something went wrong"}]}


def test_service_raised_http_exception():
    service = Service(name="test-upstream", path="/api/test/upstream")

    @service.get()
    def handler(request):
        raise HTTPBadGateway("Data source not configured")

    client = make_client(service)
    response = client.get("/api/test/upstream", headers={"Accept": "application/json"})
    assert response.status_code == 502
    assert response.json()["title"] == "Bad Gateway"


def test_service_accept_dispatch():
    service = Service(name="test-register", path="/api/test/register")

    @service.get(accept="application/json")
    def json_handler(request):
        return {"format": "json"}

    @service.get(accept=["text/xml", "application/xml"], renderer="xml")
    def xml_handler(request):
        return "<format>xml</format>"

    client = make_client(service)
    response = client.get("/api/test/register", headers={"Accept": "application/json, text/javascript, */*; q=0.01"})
    assert response.json() == {"format": "json"}

    # Like Pyramid, XML is preferred when the client accepts both equally.
    response = client.get("/api/test/register", headers={"Accept": "*/*"})
    assert response.text == "<format>xml</format>"
    assert response.headers["content-type"] == "text/xml; charset=UTF-8"

    response = client.get("/api/test/register", headers={"Accept": "image/png"})
    assert response.status_code == 406
    assert response.json()["errors"][0]["name"] == "Accept"


def test_service_method_not_allowed():
    service = Service(name="test-post", path="/api/test/post")

    @service.post()
    def handler(request):
        return {}

    client = make_client(service)
    response = client.get("/api/test/post")
    assert response.status_code == 405
    assert response.headers["allow"] == "POST"
    assert "The method GET is not allowed for this resource." in response.text


def test_service_without_handlers_is_not_mounted():
    client = make_client(Service(name="void", path="/api/void"))
    assert client.get("/api/void").status_code == 404


def test_service_form_and_multipart_parameters():
    service = Service(name="test-form", path="/api/test/form")

    @service.post()
    def handler(request):
        return {key: (value if isinstance(value, str) else value.filename) for key, value in request.params.items()}

    client = make_client(service)
    assert client.post("/api/test/form", data={"email": "foo@example.org"}).json() == {"email": "foo@example.org"}
    response = client.post("/api/test/form", data={"kind": "csv"}, files={"file": ("numbers.txt", b"EP666666")})
    assert response.json() == {"kind": "csv", "file": "numbers.txt"}


def test_request_subscribers_and_response_callbacks():
    calls = []

    def subscriber(event):
        calls.append(event.request.path_info)
        event.request.add_response_callback(lambda request, response: response.set_cookie("seen", "yes"))

    routes = RouteTable()
    routes.add("page", "/page", lambda request: "ok", renderer="null")
    client = make_client(routes)
    client.app.state.registry.add_request_subscriber(subscriber)

    response = client.get("/page")
    assert calls == ["/page"]
    assert response.cookies["seen"] == "yes"
