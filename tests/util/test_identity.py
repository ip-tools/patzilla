from mock import mock

from patzilla.util.web.identity.service import includeme, attach_user


def test_identity_service_baseline():
    config = mock.Mock()
    includeme(config)
    config.add_subscriber.assert_called_once_with(attach_user, 'pyramid.events.ContextFound')
