import mock
import pytest


def test_navigator_standalone(web_client):
    response = web_client.get("/navigator/")
    assert response.status_code == 200
    assert "var navigator_configuration" in response.text


@mock.patch("patzilla.util.web.identity.service.User")
@mock.patch("patzilla.util.web.identity.service.UserHistory")
def test_identity_auth_success(user_history_mock, user_mock, web_client):
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

    response = web_client.post("/api/identity/auth", json={"username": "foo", "password": "bar"})
    assert response.json() == user_data


@mock.patch("patzilla.util.web.identity.service.User")
@mock.patch("patzilla.util.web.identity.service.UserHistory")
def test_identity_auth_failure(user_history_mock, user_mock, web_client):
    user_data_mock = mock.Mock()
    user_data_mock.check_password.return_value = False

    user_results_mock = mock.Mock()
    user_results_mock.first.return_value = user_data_mock
    user_mock.objects.return_value = user_results_mock

    response = web_client.post("/api/identity/auth", json={"username": "foo", "password": "bar"})
    assert response.status_code == 400
    assert response.json() == {"status": "error", "errors": [
        {"location": "identity subsystem", "name": "authentication-failed", "description": "Authentication failed"}]}


def test_identity_pwhash(web_client):
    assert '$p5k2$' in web_client.get("/api/identity/pwhash/foobar").json()


@pytest.mark.parametrize("payload",
                         [{}, {"username": None}, {"username": ""}, {"username": "foo"}],
                         ids=["empty-payload", "username-null", "username-empty", "password-missing"])
def test_identity_auth_incomplete_credentials(payload, web_client):
    response = web_client.post("/api/identity/auth", json=payload)
    assert response.status_code == 400
    assert response.json()["errors"][0]["description"] == "Incomplete credentials"


def test_navigator_app(app_environment):
    assert app_environment["settings"].flavor == "minimal"


def test_navigator_web(web_environment):
    assert web_environment["settings"].flavor == "web"
    assert web_environment["state"].templates is not None
