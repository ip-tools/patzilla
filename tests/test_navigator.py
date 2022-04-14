import unittest

import mock

from pyramid import testing

from patzilla.navigator.views import navigator_standalone
from patzilla.util.web.identity.service import identity_auth_handler, identity_pwhash_handler


class TestNavigatorStandalone(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_navigator_standalone(self):
        request = testing.DummyRequest()
        info = navigator_standalone(request)
        assert type(info) is dict

    @mock.patch("patzilla.util.web.identity.service.User")
    @mock.patch("patzilla.util.web.identity.service.UserHistory")
    def test_identity_auth_success(self, user_history_mock, user_mock):
        request = testing.DummyRequest(json={"username": "foo", "password": "bar"})

        user_data = {
            'userid': '12345',
            'username': 'foo',
            'fullname': 'foo bar',
            'tags': 'tag1,tag2',
            'modules': 'mod1,mod2',
        }
        user_data_mock = mock.Mock(**user_data)
        user_data_mock.check_password.return_value = True

        user_results_mock = mock.Mock()
        user_results_mock.first.return_value = user_data_mock
        user_mock.objects.return_value = user_results_mock

        response = identity_auth_handler(request)

        assert response == user_data

    @mock.patch("patzilla.util.web.identity.service.User")
    @mock.patch("patzilla.util.web.identity.service.UserHistory")
    def test_identity_auth_failure(self, user_history_mock, user_mock):

        request = testing.DummyRequest(json={"username": "foo", "password": "bar"})
        request.errors = mock.Mock()

        user_data_mock = mock.Mock()
        user_data_mock.check_password.return_value = False

        user_results_mock = mock.Mock()
        user_results_mock.first.return_value = user_data_mock
        user_mock.objects.return_value = user_results_mock

        response = identity_auth_handler(request)

        request.errors.add.assert_called_once_with('identity subsystem', 'authentication-failed', 'Authentication failed')

        assert response is None

    def test_identity_pwhash(self):
        request = testing.DummyRequest(matchdict={"password": "foobar"})
        pwhash = identity_pwhash_handler(request)
        assert '$p5k2$' in pwhash
