# -*- coding: utf-8 -*-
# (c) 2022 Andreas Motl <andreas.motl@ip-tools.org>
"""
playwright install --with-deps msedge
"""
import os

import pytest

if "GITHUB_ACTION" in os.environ:
    pytest.skip("Espacenet per MS Edge does not work on GitHub Actions", allow_module_level=True)


from patzilla.access.epo.espacenet.api import espacenet_description, espacenet_claims, espacenet_abstract


def test_espacenet_abstract_success():
    """
    Acquire "abstract" section of valid patent document from Espacenet.

    TODO: Impossible to get abstract for document EP0666666B1.
    """
    result = espacenet_abstract(document_number="EP0666666A2")
    assert result["source"] == "espacenet"
    assert result["lang"] == "en"
    assert "A non-quota access indicator is circulated among nodes" in result["xml"]


def test_espacenet_abstract_failure():
    """
    Acquire "abstract" section of invalid patent document from Espacenet.
    """
    with pytest.raises(KeyError) as ex:
        espacenet_abstract(document_number="EP123A2")
    assert ex.match('No section "biblio" at Espacenet for "EP0000123A2"')


def test_espacenet_description_success():
    """
    Acquire "description" section of valid patent document from Espacenet.
    """
    result = espacenet_description(document_number="EP0666666B1")
    assert result["source"] == "espacenet"
    assert result["lang"] == "en"
    assert "multi-node communication systems with shared resources" in result["xml"]


def test_espacenet_description_failure():
    """
    Acquire "description" section of invalid patent document from Espacenet.
    """
    with pytest.raises(KeyError) as ex:
        espacenet_description(document_number="EP123A2")
    assert ex.match('No section "description" at Espacenet for "EP0000123A2"')


def test_espacenet_claims_success():
    """
    Acquire "claims" section of valid patent document from Espacenet.
    """
    result = espacenet_claims(document_number="EP0666666B1")
    assert result["source"] == "espacenet"
    assert result["lang"] == "en"
    assert "A method for non-quota access to a shared resource" in result["xml"]


def test_espacenet_claims_failure():
    """
    Acquire "claims" section of invalid patent document from Espacenet.
    """
    with pytest.raises(KeyError) as ex:
        espacenet_claims(document_number="EP123A2")
    assert ex.match('No section "claims" at Espacenet for "EP0000123A2"')
