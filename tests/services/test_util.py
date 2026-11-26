from unittest import mock

import pytest

from patzilla.access.generic.exceptions import ServiceError
from patzilla.navigator.services.util import make_expression_filter, request_to_options


def test_query_expression_util_handler_success(web_client):
    body = {
        "datasource": "ops",
        "criteria": {"patentnumber": "EP666666 or EP666667"},
    }
    response = web_client.post("/api/util/query-expression", json=body)
    assert response.status_code == 200
    assert response.json() == {
        "expression": "pn=(EP666666 or EP666667)",
        "filter": "",
    }


def test_query_expression_util_handler_failure(web_client):
    response = web_client.post("/api/util/query-expression", json={
        "datasource": "ops",
        "criteria": {"unknown": "foo"},
    })
    assert response.status_code == 400
    assert response.json()["errors"] == [{
        'location': 'query-expression-utility-service',
        'name': 'comfort-form',
        'description': 'Criteria "unknown: foo" has invalid format, datasource=ops.'
    }]


def test_make_expression_filter_failure():
    with pytest.raises(ServiceError) as ex:
        make_expression_filter({"datasource": "ops", "criteria": {"unknown": "foo"}})
    assert ex.value.errors[0]["name"] == "comfort-form"


def test_numberlist_util_handler_standard_success(web_client):
    response = web_client.post("/api/util/numberlist", content=b"EP666666\nEP666667",
                               headers={"Content-Type": "text/plain"})
    assert response.json() == {"numbers-sent": ["EP666666", "EP666667"]}


def test_numberlist_util_handler_normalize_success(web_client):
    response = web_client.post("/api/util/numberlist?normalize=true", content=b"EP666666\nEP666667",
                               headers={"Content-Type": "text/plain; charset=utf-8"})
    assert response.json() == {
        "numbers-sent": ["EP666666", "EP666667"],
        "numbers-normalized": {
            'valid': ["EP0666666", "EP0666667"],
            'invalid': [],
            'all': ["EP0666666", "EP0666667"],
        },
    }


def test_request_to_options_family_remove():
    options = {}
    request_to_options({
        'query_data[modifiers][family-remove]': 'true',
        'query_data[modifiers][family-replace]': 'true',
        'query_data[sorting][foo]': 'true',
    }, options)
    assert options == {
        "feature_family_remove": True,
        "sorting": {"foo": "true"},
    }


def test_request_to_options_family_replace():
    options = {}
    request_to_options({
        'query_data[modifiers][family-remove]': 'false',
        'query_data[modifiers][family-replace]': 'true',
        'query_data[sorting][foo]': 'true',
    }, options)
    assert options == {
        "feature_family_replace": True,
        "sorting": {"foo": "true"},
    }


def test_issue_reporter_handler(web_client):
    with mock.patch('patzilla.navigator.services.util.email_issue_report') as submit:
        response = web_client.post(
            "/api/util/issue/report?targets=email:test@example.org",
            json={"dialog": {"what": "Something", "remark": "Wrong"}, "meta": {"id": "unknown"}},
        )
    assert response.status_code == 200
    submit.assert_called_once()
    assert submit.call_args.args[1] == "test@example.org"
