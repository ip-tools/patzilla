# -*- coding: utf-8 -*-
# (c) 2022 Andreas Motl <andreas.motl@ip-tools.org>
import socket

import pytest
from cornice.util import _JSONError
from pyramid.httpexceptions import HTTPBadGateway

from patzilla.access.epo.ops.api import ops_published_data_search, get_ops_client, OPS_BASE_URI, get_ops_biblio_data, \
    ops_biblio_documents, ops_document_kindcodes, ops_family_members, ops_published_data_search_swap_family
from patzilla.access.epo.ops.client import OpsCredentialsGetter
from patzilla.util.data.container import jpath


# Skip those tests when there is no way to access EPO OPS because corresponding
# credentials haven't been provided as environment variables. See :ref:`cli`_
# for further information.
try:
    OpsCredentialsGetter.from_environment()
except KeyError:
    pytestmark = pytest.mark.skip(reason="No OPS credentials provided")


def test_client_not_configured():
    with pytest.raises(HTTPBadGateway) as ex:
        get_ops_client()
    assert ex.match("EPO OPS: Data source not enabled or not configured")


@pytest.mark.skipif("sink" in socket.gethostname(), reason="Skip to speed things up on developer workstation")
def test_baseurl(app_environment):
    """
    Proof that OAuth2 authentication works. The baseurl, where the "OPS Guide"
    is published, is not available for anonymous users.
    """
    client = get_ops_client()
    response = client._make_request(
        OPS_BASE_URI, data={}, extra_headers={"Accept": "*"}, use_get=True,
    )
    assert "<title>EPO - Open Patent Services (OPS)</title>" in response.content


def test_search_basic_success(app_request):
    """
    Proof a basic search expression works on OPS and yields a response in the
    appropriate format. Validate that response by checking the result count.
    """
    results = ops_published_data_search(constituents="full-cycle", query="pn=(EP666666 or EP666667)", range="1-10")
    total_result_count = int(jpath('/ops:world-patent-data/ops:biblio-search/@total-result-count', results))
    assert total_result_count == 2


def test_search_basic_failure(app_request):
    """
    Proof that submitting an invalid search request fails.
    """
    with pytest.raises(_JSONError) as ex:
        ops_published_data_search(constituents="full-cycle", query="foo=bar", range="1-10")

    json_error = ex.value
    message = str(json_error)

    # TODO: Maybe do XML parsing here? Or better within the core implementation?
    assert "400 Bad Request" in message
    assert '<fault xmlns="http://ops.epo.org">' in message
    assert "<code>CLIENT.InvalidIndex</code>" in message
    assert "<message>The query provided is invalid. Invalid index name foo</message>" in message

    error_data = json_error.json
    assert jpath('/status', error_data) == "error"
    assert jpath('/errors/0/name', error_data) == "http-response"
    assert jpath('/errors/0/location', error_data) == "ops-search"
    assert jpath('/errors/0/description/status_code', error_data) == 400
    assert jpath('/errors/0/description/reason', error_data) == "Bad Request"
    assert jpath('/errors/0/description/url', error_data) == "https://ops.epo.org/3.2/rest-services/published-data/search/full-cycle"
    assert jpath('/errors/0/description/headers/X-API', error_data) == "ops-v3.2"
    assert jpath('/errors/0/description/headers/Content-Type', error_data).startswith("application/xml")


def test_search_swap_family(app_request):
    """
    Test the adjustments to the selection of representative documents.

    TODO: Improve! Currently, this is just a very basic test which is
          not probing too many details.
    """
    results = ops_published_data_search_swap_family(
        constituents="full-cycle",
        query="pn=(EP666666 or EP666667)", range="1-10")

    total_result_count = int(jpath('/ops:world-patent-data/ops:biblio-search/@total-result-count', results.data))
    assert total_result_count == 2

    assert results.selected_numbers == [u'DE69534171T2', u'EP0666667A2']


def test_get_ops_biblio_data_json_success(app_request):
    """
    Proof getting bibliographic for a specific document in JSON format works.
    """
    documents = ops_biblio_documents("EP0666666")
    kindcodes = sorted([document["@kind"] for document in documents])
    attributes = sorted(documents[0].keys())
    assert len(documents) == 3
    assert kindcodes == ["A2", "A3", "B1"]
    assert attributes == [
        u'@country',
        u'@doc-number',
        u'@family-id',
        u'@kind',
        u'@system',
        u'abstract',
        u'bibliographic-data',
    ]


@pytest.mark.slow
def test_get_ops_biblio_data_json_failure(app_request):
    """
    Proof getting bibliographic for an invalid document number croaks.
    """
    with pytest.raises(_JSONError) as ex:
        ops_biblio_documents("EP0")

    assert_404_not_found(ex, location="ops-biblio", url="https://ops.epo.org/3.2/rest-services/published-data/publication/epodoc/biblio/full-cycle")


def test_get_ops_biblio_data_xml(app_request):
    """
    Proof getting bibliographic for a specific document in XML format works.
    """
    results = get_ops_biblio_data("publication", "EP0666666", xml=True)
    assert results.startswith('<?xml version="1.0" encoding="UTF-8"?>')


def te2st_ops_document_kindcodes_success(app_request):
    """
    Validate acquiring document kind codes.
    """
    kindcodes = ops_document_kindcodes("EP0666666")
    assert kindcodes == ["A2", "A3", "B1"]


def tes2t_ops_document_kindcodes_failure(app_request):
    """
    Validate acquiring document kind codes.
    """
    with pytest.raises(_JSONError) as ex:
        ops_document_kindcodes("EP0")

    assert_404_not_found(ex, location="ops-biblio", url="https://ops.epo.org/3.2/rest-services/published-data/publication/epodoc/biblio/full-cycle")


def assert_404_not_found(ex, location=None, url=None):

    json_error = ex.value
    message = str(json_error)

    # TODO: Maybe do XML parsing here? Or better within the core implementation?
    assert "404 Not Found" in message
    assert '<fault xmlns="http://ops.epo.org">' in message
    assert "<code>SERVER.EntityNotFound</code>" in message
    assert "<message>No results found</message>" in message

    error_data = json_error.json
    print("error_data:", error_data)
    assert jpath('/status', error_data) == "error"
    assert jpath('/errors/0/name', error_data) == "http-response"
    assert jpath('/errors/0/location', error_data) == location
    assert jpath('/errors/0/description/status_code', error_data) == 404
    assert jpath('/errors/0/description/reason', error_data) == "Not Found"
    assert jpath('/errors/0/description/url', error_data) == url
    assert jpath('/errors/0/description/headers/X-API', error_data) == "ops-v3.2"
    assert jpath('/errors/0/description/headers/Content-Type', error_data).startswith("application/xml")


def test_ops_family_members(app_request):
    """
    Validate acquiring family members.
    """
    members = ops_family_members("EP0666666")

    appnumbers = sorted([item["application"]["number-docdb"] for item in members.items])
    pubnumbers = sorted([item["publication"]["number-docdb"] for item in members.items])

    assert appnumbers == [
        u'CA2142029A',
        u'CA2142029A',
        u'DE69534171T',
        u'DE69534171T',
        u'EP95480005A',
        u'EP95480005A',
        u'EP95480005A',
        u'JP29020894A',
        u'JP29020894A',
        u'US19288494A',
        u'US47157195A',
    ]

    assert pubnumbers == [
        u'CA2142029A1',
        u'CA2142029C',
        u'DE69534171D1',
        u'DE69534171T2',
        u'EP0666666A2',
        u'EP0666666A3',
        u'EP0666666B1',
        u'JP2613027B2',
        u'JPH07231328A',
        u'US5467352A',
        u'US5572526A',
    ]
