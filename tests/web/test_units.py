from types import SimpleNamespace

import pytest

from patzilla.boot.cache import client_cache_region, configure_cache_backend
from patzilla.web.dependencies import prefers_xml


@pytest.mark.parametrize("accept,expected", [
    ("", False),
    ("*/*", False),
    ("application/json, text/javascript, */*; q=0.01", False),
    ("text/xml", True),
    ("application/xml;q=0.9, application/json;q=0.5", True),
    ("application/json, application/xml;q=0.9", False),
])
def test_prefers_xml(accept, expected):
    request = SimpleNamespace(headers={"accept": accept})
    assert prefers_xml(request) is expected


def test_client_cache_region_excludes_client_from_key():
    configure_cache_backend("memory")
    calls = []

    @client_cache_region("search")
    def fetch(client, document, xml=False):
        calls.append((client, document, xml))
        return document

    assert fetch("client-1", "EP666666") == "EP666666"
    assert fetch("client-2", "EP666666") == "EP666666"
    assert fetch("client-1", "EP666666", xml=True) == "EP666666"
    assert fetch("client-2", "EP666666", True) == "EP666666"
    assert calls == [("client-1", "EP666666", False), ("client-1", "EP666666", True)]
