from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from starlette.exceptions import HTTPException

from patzilla.access.generic.exceptions import ServiceError

from patzilla.access.epo.ops import api as ops_api


def make_response(
    status=200,
    reason="OK",
    content_type="application/json",
    text="",
    json_data=None,
):
    return SimpleNamespace(
        status_code=status,
        reason=reason,
        url="https://ops.example.invalid/search",
        headers={"content-type": content_type},
        text=text,
        content=text.encode("utf-8"),
        json=Mock(return_value=json_data),
    )


def test_handle_response_decodes_json():
    data = {"ops:world-patent-data": {"result": "ok"}}
    response = make_response(
        content_type="application/json; charset=utf-8",
        json_data=data,
    )

    assert ops_api.handle_response(Mock(), response, "ops-search") == data
    response.json.assert_called_once_with()


@pytest.mark.parametrize("content_type", [
    "application/xml; charset=utf-8",
    "text/xml",
])
def test_handle_response_returns_xml_text(content_type):
    xml = "<world-patent-data/>"
    response = make_response(content_type=content_type, text=xml)

    assert ops_api.handle_response(Mock(), response, "ops-search") == xml
    response.json.assert_not_called()


def test_handle_response_rejects_unknown_content_type():
    response = make_response(content_type="application/octet-stream")

    with pytest.raises(HTTPException, match="unknown content type"):
        ops_api.handle_response(Mock(), response, "ops-search")


@pytest.mark.parametrize(
    "status,reason,text,expected_name,expected_status",
    [
        (400, "Bad Request", "CLIENT.CQL: invalid query", "expression", 400),
        (404, "Not Found", "SERVER.EntityNotFound", "http-response", 404),
        (404, "Not Found", "OPS - 404: Page not found", "http-response", 502),
        (
            404,
            "Not Found",
            "This API version is not supported",
            "http-response",
            502,
        ),
    ],
)
def test_handle_response_raises_classified_error(
    monkeypatch, status, reason, text, expected_name, expected_status
):
    response = make_response(
        status=status,
        reason=reason,
        content_type="application/xml",
        text=text,
    )

    with pytest.raises(ServiceError) as exc_info:
        ops_api.handle_response(Mock(), response, "ops-search")

    error = exc_info.value
    assert error.status_code == expected_status
    assert error.detail == "{} {}: {}".format(status, reason, text)

    recorded = error.envelope["errors"][0]
    assert recorded["location"] == "ops-search"
    assert recorded["name"] == expected_name
    assert recorded["description"]["status_code"] == status
    assert recorded["description"]["reason"] == reason
    assert recorded["description"]["url"] == response.url
    assert recorded["description"]["text"] == text
    # json_error decodes the upstream bytes for JSON serialization.
    assert recorded["description"]["content"] == text


@pytest.mark.parametrize("content_length", ["7", "", "invalid", None])
def test_measure_response_records_only_numeric_content_length(
    monkeypatch, content_length
):
    metrics = Mock()
    client = SimpleNamespace(metrics_manager=metrics, userid="foo")
    response = make_response(json_data={"ok": True})
    if content_length is not None:
        response.headers["Content-Length"] = content_length

    assert ops_api.handle_response(client, response, "ops-search") == {"ok": True}

    if content_length == "7":
        metrics.measure_upstream.assert_called_once_with("ops", 7, userid="foo")
    else:
        metrics.measure_upstream.assert_not_called()
