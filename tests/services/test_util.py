import json
from unittest import mock
from unittest.mock import Mock

import cornice
from munch import Munch
from pyramid.testing import DummyRequest

from patzilla.navigator.services.util import query_expression_util_handler, numberlist_util_handler, request_to_options, \
    issue_reporter_handler


class FakeRequest(DummyRequest):
    def __init__(self, *args, **kwargs):
        self.user = Munch(userid="foo")
        self.errors = cornice.Errors()
        super().__init__(*args, **kwargs)


def test_query_expression_util_handler_success(app_request):
    request = app_request
    body = {
        "datasource": "ops",
        "criteria": {"patentnumber": "EP666666 or EP666667"},
        #"modifiers": {},
        #"query": "",
    }
    request.body = json.dumps(body).encode("utf-8")

    retval = query_expression_util_handler(app_request)
    assert retval == {
        "expression": "pn=(EP666666 or EP666667)",
        "filter": "",
    }
    assert request.errors == []


def test_query_expression_util_handler_failure():
    request = FakeRequest(json={
        "datasource": "ops",
        "criteria": {"unknown": "foo"},
    })

    retval = query_expression_util_handler(request)
    assert retval == {"expression": "", "filter": ""}
    assert request.errors == [{
        'location': 'query-expression-utility-service',
        'name': 'comfort-form',
        'description': 'Criteria "unknown: foo" has invalid format, datasource=ops.'
    }]


def test_numberlist_util_handler_standard_success(app_request):
    request = app_request
    request.content_type = 'text/plain'
    request.body = b"EP666666\nEP666667"

    retval = numberlist_util_handler(request)
    assert retval == {"numbers-sent": ["EP666666", "EP666667"]}
    assert request.errors == []


def test_numberlist_util_handler_normalize_success():
    request = FakeRequest()

    request.content_type = 'text/plain'  # ty: ignore[unresolved-attribute]
    request.text = "EP666666\nEP666667"  # ty: ignore[unresolved-attribute]
    request.params = {"normalize": "true"}

    retval = numberlist_util_handler(request)
    assert retval == {
        "numbers-sent": ["EP666666", "EP666667"],
        "numbers-normalized": {
            'valid': ["EP0666666", "EP0666667"],
            'invalid': [],
            'all': ["EP0666666", "EP0666667"],
        },
    }
    assert request.errors == []


def test_request_to_options_family_remove():
    request = FakeRequest(params={
        'query_data[modifiers][family-remove]': 'true',
        'query_data[modifiers][family-replace]': 'true',
        'query_data[sorting][foo]': 'true',
    })
    options = {}
    request.errors = cornice.Errors()
    request_to_options(request, options)
    assert options == {
        "feature_family_remove": True,
        "sorting": {"foo": "true"},
    }


def test_request_to_options_family_replace():
    request = FakeRequest(params={
        'query_data[modifiers][family-remove]': 'false',
        'query_data[modifiers][family-replace]': 'true',
        'query_data[sorting][foo]': 'true',
    })
    options = {}
    request.errors = cornice.Errors()
    request_to_options(request, options)
    assert options == {
        "feature_family_replace": True,
        "sorting": {"foo": "true"},
    }


def test_issue_reporter_handler(app_environment, mocker):
    # https://docs.pylonsproject.org/projects/pyramid/en/latest/api/testing.html
    request = DummyRequest(
        json={"dialog": {"what": "Something", "remark": "Wrong"}, "meta": {"id": "unknown"}},
        params={"targets": "email:test@example.org"},
        user=None,
    )
    request.errors = cornice.Errors()  # ty: ignore[unresolved-attribute]
    request.registry = Mock()

    submit = mocker.patch('patzilla.navigator.services.util.email_issue_report')

    issue_reporter_handler(request)

    submit.assert_called_once()
    submit.assert_called_with(mock.ANY, "test@example.org")
