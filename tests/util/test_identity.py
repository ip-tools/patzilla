from patzilla.web.registry import Registry

from patzilla.util.web.identity.service import setup, attach_user


def test_identity_service_baseline():
    registry = Registry()
    setup(registry)
    assert registry.request_subscribers == [attach_user]
