# -*- coding: utf-8 -*-
# (c) 2022 Andreas Motl <andreas.motl@ip-tools.org>
import pytest

from patzilla.access.epo.espacenet.client import espacenet_description, espacenet_claims, espacenet_abstract


def test_espacenet_abstract_success(app_request):
    """
    Acquire "abstract" section of valid patent document from Espacenet.
    """
    result = espacenet_abstract(document_number="EP0666666B1")
    assert result["source"] == "espacenet"
    assert result["lang"] == "en"
    assert "A non-quota access indicator is circulated among nodes" in result["xml"]


def test_espacenet_abstract_failure(app_request):
    """
    Acquire "abstract" section of invalid patent document from Espacenet.
    """
    with pytest.raises(KeyError) as ex:
        espacenet_abstract(document_number="EP123A2")
    assert ex.match('No section "biblio" at Espacenet for "EP123A2"')


def test_espacenet_description_success(app_request):
    """
    Acquire "description" section of valid patent document from Espacenet.
    """
    result = espacenet_description(document_number="EP0666666B1")
    assert result["source"] == "espacenet"
    assert result["lang"] == "en"
    assert "multi-node communication systems with shared resources" in result["xml"]


def test_espacenet_description_failure(app_request):
    """
    Acquire "description" section of invalid patent document from Espacenet.
    """
    with pytest.raises(KeyError) as ex:
        espacenet_description(document_number="EP123A2")
    assert ex.match('No section "description" at Espacenet for "EP123A2"')


def test_espacenet_claims_success(app_request):
    """
    Acquire "claims" section of valid patent document from Espacenet.
    """
    result = espacenet_claims(document_number="EP0666666B1")
    assert result["source"] == "espacenet"
    assert result["lang"] == "en"
    assert "A method for non-quota access to a shared resource" in result["xml"]


def test_espacenet_claims_failure(app_request):
    """
    Acquire "claims" section of invalid patent document from Espacenet.
    """
    with pytest.raises(KeyError) as ex:
        espacenet_claims(document_number="EP123A2")
    assert ex.match('No section "claims" at Espacenet for "EP123A2"')
