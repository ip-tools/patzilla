# -*- coding: utf-8 -*-
# (c) 2022 Andreas Motl <andreas.motl@ip-tools.org>
import socket

import pytest
from epo_ops.exceptions import MissingRequiredValue
from starlette.exceptions import HTTPException

from patzilla.access import resolve_client
from patzilla.access.epo.ops.api import ops_published_data_search, OPS_BASE_URI, get_ops_biblio_data, \
    ops_biblio_documents, ops_document_kindcodes, ops_family_members, ops_published_data_search_swap_family, \
    ops_published_data_crawl, image_representative, get_ops_image, ops_description, ops_claims, get_ops_image_pdf, \
    ops_service_usage, _result_list_compact, ops_family_publication_docdb_xml, ops_register, \
    _flatten_ops_json_list, inquire_images
from patzilla.access.epo.ops.client import OpsCredentialsGetter
from patzilla.access.generic.exceptions import ServiceError
from patzilla.util.data.container import jpath


# Skip those tests when there is no way to access EPO OPS because corresponding
# credentials haven't been provided as environment variables. See :ref:`cli`_
# for further information.
from patzilla.util.numbers.common import split_patent_number, DocumentIdentifierBunch

try:
    OpsCredentialsGetter.from_environment()
except KeyError:
    pytestmark = pytest.mark.skip(reason="No OPS credentials provided")

PDF_HEADER = b"%PDF"
TIFF_HEADER_BIG_ENDIAN = b"\x4d\x4d\x00\x2a"


def test_client_not_configured():
    assert resolve_client({}, "ops", datasource_settings=None) is None


@pytest.mark.skipif("sink" in socket.gethostname(), reason="Skip to speed things up on developer workstation")
def test_baseurl(ops_client):
    """
    Proof that OAuth2 authentication works. The baseurl, where the "OPS Guide"
    is published, is not available for anonymous users.
    """
    response = ops_client._make_request(
        OPS_BASE_URI, data={}, extra_headers={"Accept": "*"}, use_get=True,
    )
    assert "<title>Open Patent Services (OPS) | epo.org</title>" in response.text


def test_search_full_success(ops_client):
    """
    Proof a basic search expression works on OPS and yields a response in the
    appropriate format. Validate that response by checking the result count.
    """
    results = ops_published_data_search(ops_client, constituents="full-cycle", query="pn=(EP666666 or EP666667)", range="1-10")
    total_result_count = int(jpath('/ops:world-patent-data/ops:biblio-search/@total-result-count', results))
    assert total_result_count == 2


def test_search_biblio_compact_success(ops_client):
    """
    Run a search expression with requesting bibliographic data
    and return the results in "compact" JSON format.
    """
    results = ops_published_data_search(ops_client, constituents="biblio", query="pn=(EP666666 or EP666667)", range="1-10")
    compact = _result_list_compact(results)
    assert jpath('/1/pubnumber', compact) == "EP0666666"
    assert jpath('/1/pubdate', compact) == "1995-08-09"
    assert jpath('/0/pubnumber', compact) == "EP0666667"
    assert jpath('/0/pubdate', compact) == "1995-08-09"
    assert sorted(compact[0].keys()) == sorted(compact[1].keys()) == [
        'abstract',
        'appdate',
        'applicant',
        'appnumber',
        'inventor',
        'pubdate',
        'pubnumber',
        'title',
    ]


def test_search_no_results(ops_client):
    """
    Proof a basic search without results has the expected outcome.
    """
    with pytest.raises(ServiceError) as ex:
        ops_published_data_search(ops_client, constituents="full-cycle", query="applicant=foobar", range="1-10")

    assert_404_not_found(ex,
                         location="ops-search",
                         url="https://ops.epo.org/3.2/rest-services/published-data/search/full-cycle")


def test_search_failure(ops_client):
    """
    Proof that submitting an invalid search request fails.
    """
    with pytest.raises(ServiceError) as ex:
        ops_published_data_search(ops_client, constituents="full-cycle", query="foo=bar", range="1-10")

    json_error = ex.value
    message = str(json_error)

    # TODO: Maybe do XML parsing here? Or better within the core implementation?
    assert "400 Bad Request" in message
    assert '<fault xmlns="http://ops.epo.org">' in message
    assert "<code>CLIENT.InvalidIndex</code>" in message
    assert "<message>The query provided is invalid. Invalid index name foo</message>" in message

    error_data = json_error.envelope
    assert jpath('/status', error_data) == "error"
    assert jpath('/errors/0/name', error_data) == "http-response"
    assert jpath('/errors/0/location', error_data) == "ops-search"
    assert jpath('/errors/0/description/status_code', error_data) == 400
    assert jpath('/errors/0/description/reason', error_data) == "Bad Request"
    assert jpath('/errors/0/description/url',
                 error_data) == "https://ops.epo.org/3.2/rest-services/published-data/search/full-cycle"
    assert jpath('/errors/0/description/headers/x-api', error_data) == "ops-v3.2"
    assert jpath('/errors/0/description/headers/content-type', error_data).startswith("application/xml")


def test_search_swap_family(ops_client):
    """
    Test the adjustments to the selection of representative documents.

    TODO: Improve! Currently, this is just a very basic test which is
          not probing too many details.
    """
    results = ops_published_data_search_swap_family(ops_client,
        constituents="full-cycle",
        query="pn=(EP666666 or EP666667)", range="1-10")

    total_result_count = int(jpath('/ops:world-patent-data/ops:biblio-search/@total-result-count', results.data))
    assert total_result_count == 2

    assert results.selected_numbers == ['EP0666667A2', 'DE69534171T2']


def test_crawl(ops_client):
    """
    Test that the search crawler works as expected.

    TODO: It is just a basic test and has to be improved to improve coverage.
    """
    results = ops_published_data_crawl(ops_client, constituents="pub-number", query="pn=(EP666666 or EP666667)", chunksize=25)
    total_result_count = int(jpath('/ops:world-patent-data/ops:biblio-search/@total-result-count', results))
    assert total_result_count == 2


def test_crawl_no_results(ops_client):
    """
    Test that the search crawler works as expected.

    TODO: It is just a basic test and has to be improved to improve coverage.
    """
    with pytest.raises(ServiceError) as ex:
        ops_published_data_crawl(ops_client, constituents="pub-number", query="pn=EP0", chunksize=25)
    assert_404_not_found(
        ex,
        location="ops-search",
        url="https://ops.epo.org/3.2/rest-services/published-data/search",
    )


def test_crawl_invalid_constituent(ops_client):
    """
    Test that the search crawler works as expected.
    """
    with pytest.raises(ValueError) as ex:
        ops_published_data_crawl(ops_client, constituents="full-cycle", query="pn=(EP666666 or EP666667)", chunksize=25)
    ex.match('Only constituent "pub-number" permitted here')


def test_biblio_data_json_success(ops_client):
    """
    Proof getting bibliographic for a specific document in JSON format works.
    """
    documents = ops_biblio_documents(ops_client, "EP0666666")
    kindcodes = sorted([document["@kind"] for document in documents])
    attributes = sorted(documents[0].keys())
    assert len(documents) == 3
    assert kindcodes == ["A2", "A3", "B1"]
    assert attributes == [
        '@country',
        '@doc-number',
        '@family-id',
        '@kind',
        '@system',
        'abstract',
        'bibliographic-data',
    ]


@pytest.mark.slow
def test_biblio_data_json_failure(ops_client):
    """
    Proof getting bibliographic for an invalid document number croaks.
    """
    with pytest.raises(ServiceError) as ex:
        ops_biblio_documents(ops_client, "EP0")

    assert_404_not_found(
        ex,
        location="ops-biblio",
        url="https://ops.epo.org/3.2/rest-services/published-data/publication/epodoc/biblio/full-cycle",
    )


def test_biblio_data_xml_success(ops_client):
    """
    Proof getting bibliographic for a specific document in XML format works.
    """
    results = get_ops_biblio_data(ops_client, "publication", "EP0666666", xml=True)
    assert results.startswith('<?xml version="1.0" encoding="UTF-8"?>')


def test_document_kindcodes_success(ops_client):
    """
    Validate acquiring document kind codes.
    """
    kindcodes = ops_document_kindcodes(ops_client, "EP0666666")
    assert kindcodes == ["A2", "A3", "B1"]


def test_document_kindcodes_failure(ops_client):
    """
    Validate acquiring document kind codes.
    """
    with pytest.raises(ServiceError) as ex:
        ops_document_kindcodes(ops_client, "EP0")

    assert_404_not_found(
        ex,
        location="ops-biblio",
        url="https://ops.epo.org/3.2/rest-services/published-data/publication/epodoc/biblio/full-cycle",
    )


def assert_404_not_found(ex, location=None, url=None):
    json_error = ex.value
    message = str(json_error)

    # TODO: Maybe do XML parsing here? Or better within the core implementation?
    assert "404 Not Found" in message
    assert '<fault xmlns="http://ops.epo.org">' in message
    assert "<code>SERVER.EntityNotFound</code>" in message
    assert "<message>No results found</message>" in message

    error_data = json_error.envelope
    print("error_data:", error_data)
    assert jpath('/status', error_data) == "error"
    assert jpath('/errors/0/name', error_data) == "http-response"
    assert jpath('/errors/0/location', error_data) == location
    assert jpath('/errors/0/description/status_code', error_data) == 404
    assert jpath('/errors/0/description/reason', error_data) == "Not Found"
    assert jpath('/errors/0/description/url', error_data) == url
    assert jpath('/errors/0/description/headers/x-api', error_data) == "ops-v3.2"
    assert jpath('/errors/0/description/headers/content-type', error_data).startswith("application/xml")


def test_family_members(ops_client):
    """
    Validate acquiring family members.
    """
    members = ops_family_members(ops_client, "EP0666666")

    appnumbers = sorted([item["application"]["number-docdb"] for item in members.items])
    pubnumbers = sorted([item["publication"]["number-docdb"] for item in members.items])

    assert appnumbers == [
        'CA2142029A',
        'CA2142029A',
        'DE69534171T',
        'DE69534171T',
        'EP95480005A',
        'EP95480005A',
        'EP95480005A',
        'JP29020894A',
        'JP29020894A',
        'US19288494A',
        'US47157195A',
    ]

    assert pubnumbers == [
        'CA2142029A1',
        'CA2142029C',
        'DE69534171D1',
        'DE69534171T2',
        'EP0666666A2',
        'EP0666666A3',
        'EP0666666B1',
        'JP2613027B2',
        'JPH07231328A',
        'US5467352A',
        'US5572526A',
    ]


def test_image_inquiry_with_kindcode_A2_success(ops_client):
    """
    Check successful image inquiry of a European Patent Application.
    """
    data = inquire_images(ops_client, "EP0666666A2")
    assert jpath("/META/drawing-start-page", data) == 7
    assert jpath("/META/drawing-total-count", data) == 2


def test_image_inquiry_with_kindcode_B1_success(ops_client):
    """
    Check successful image inquiry of a European Patent Specification.
    """
    data = inquire_images(ops_client, "EP0666666B1")
    assert jpath("/META/drawing-start-page", data) == 12
    assert jpath("/META/drawing-total-count", data) == 2


def test_image_inquiry_with_kindcode_A3_success(ops_client):
    """
    Check successful image inquiry of a European Search Report.
    """
    data = inquire_images(ops_client, "EP0666666A3")
    assert jpath("/META", data) == {}
    assert jpath("/FullDocument/ops:document-section/2/@name", data) == "SEARCH_REPORT"


def test_image_inquiry_no_kindcode_success(ops_client):
    """
    Check successful image inquiry without kind code.

    Inquiring EP0666666 should yield the document EP0666666B1,
    a European Patent Specification.
    """
    data = inquire_images(ops_client, "EP0666666")
    assert jpath("/META/drawing-start-page", data) == 12
    assert jpath("/META/drawing-total-count", data) == 2


def test_image_inquiry_failure(ops_client):
    """
    Check successful image inquiry.
    """
    with pytest.raises(HTTPException) as ex:
        inquire_images(ops_client, "EP123A2")
    assert ex.match("No image information for document=EP123A2")


def test_image_representative(ops_client):
    """
    Proof representative drawings can be found in family members.
    """
    assert image_representative(ops_client, split_patent_number("EP666666A2")) is None

    patent = split_patent_number("DE112013003369A5")
    assert image_representative(ops_client, patent) is True
    assert patent == DocumentIdentifierBunch(country='DE', ext='', kind='A1', number='102012211542')

    patent = split_patent_number("EP1929706A4")
    assert image_representative(ops_client, patent) is True
    assert patent == DocumentIdentifierBunch(country='EP', ext='', kind='A1', number='1929706')


def test_image_tiff_success(ops_client):
    """
    Acquire drawing in TIFF format.
    """
    response = get_ops_image(ops_client, "EP0666666A2", 1, "FullDocumentDrawing", "tiff")
    assert response.startswith(TIFF_HEADER_BIG_ENDIAN)

    response = get_ops_image(ops_client, "EP0666666A2", 1, "FullDocument", "tiff")
    assert response.startswith(TIFF_HEADER_BIG_ENDIAN)


def test_image_pdf_success(ops_client):
    """
    Acquire drawing in PDF format.
    """
    response = get_ops_image(ops_client, "EP0666666A2", 1, "FullDocumentDrawing", "pdf")
    assert response.startswith(PDF_HEADER)


def test_image_failure(ops_client):
    """
    Check acquire drawing fails.
    """
    with pytest.raises(HTTPException) as ex:
        get_ops_image(ops_client, "EP0", 1, "FullDocumentDrawing", "tiff")
    assert ex.match("No image information for document=EP0")


def test_fulldocument_pdf_success(ops_client):
    """
    Check downloading full PDF document.
    """
    response = get_ops_image_pdf(ops_client, "EP0666666A2", 1)
    assert response.startswith(PDF_HEADER)


def test_description_json_success(ops_client):
    """
    Acquire full text "description" in JSON format.
    """
    data = ops_description(ops_client, "EP666666A2")
    pubref = jpath(
        "/ops:world-patent-data/ftxt:fulltext-documents/ftxt:fulltext-document/bibliographic-data/publication-reference",
        data)
    description = jpath("/ops:world-patent-data/ftxt:fulltext-documents/ftxt:fulltext-document/description", data)

    assert pubref == {
        "document-id": {
            "country": {
                "$": "EP"
            },
            "kind": {
                "$": "A2"
            },
            "doc-number": {
                "$": "0666666"
            }
        },
        "@data-format": "docdb"
    }
    assert "The present invention generally relates to multi-node communication systems with shared resources." in str(
        description)


def test_description_xml_success(ops_client):
    """
    Acquire full text "description" in XML format.
    """
    data = ops_description(ops_client, "EP666666A2", xml=True)
    assert data.startswith('<?xml version="1.0" encoding="UTF-8"?>')
    assert "The present invention generally relates to multi-node communication systems with shared resources." in data


def test_description_failure(ops_client):
    """
    Full text acquisition for unknown documents should fail appropriately.
    """
    with pytest.raises(ServiceError) as ex:
        ops_description(ops_client, "EP0")

    assert_404_not_found(
        ex,
        location="ops-description",
        url="https://ops.epo.org/3.2/rest-services/published-data/publication/epodoc/description",
    )


def test_claims_json_success(ops_client):
    """
    Acquire full text "claims" in JSON format.
    """
    data = ops_claims(ops_client, "EP666666A2")
    pubref = jpath(
        "/ops:world-patent-data/ftxt:fulltext-documents/ftxt:fulltext-document/bibliographic-data/publication-reference",
        data)
    claims = jpath("/ops:world-patent-data/ftxt:fulltext-documents/ftxt:fulltext-document/claims", data)

    assert pubref == {
        "document-id": {
            "country": {
                "$": "EP"
            },
            "kind": {
                "$": "A2"
            },
            "doc-number": {
                "$": "0666666"
            }
        },
        "@data-format": "docdb"
    }
    assert "1. In a communication system having a plurality of nodes" in str(claims)


def test_claims_xml_success(ops_client):
    """
    Acquire full text "claims" in XML format.
    """
    data = ops_claims(ops_client, "EP666666A2", xml=True)
    assert data.startswith('<?xml version="1.0" encoding="UTF-8"?>')
    assert "1. In a communication system having a plurality of nodes" in data


def test_claims_failure(ops_client):
    """
    Full text acquisition for unknown documents should fail appropriately.
    """
    with pytest.raises(ServiceError) as ex:
        ops_claims(ops_client, "EP0")

    assert_404_not_found(
        ex,
        location="ops-claims",
        url="https://ops.epo.org/3.2/rest-services/published-data/publication/epodoc/claims",
    )


def test_family_members_success(ops_client):
    family_members = ops_family_members(ops_client, "EP0666666A2")
    jp_members = family_members.publications_by_country(countries=["JP"])
    assert jp_members == ["JPH07231328A", "JP2613027B2"]


def test_family_members_invalid_number_failure(ops_client):
    with pytest.raises(MissingRequiredValue) as ex:
        ops_family_members(ops_client, "EP0")
    assert ex.match("number, country_code, and kind_code must be present")


def test_family_members_not_found_failure(ops_client):
    with pytest.raises(ServiceError) as ex:
        ops_family_members(ops_client, "EP0000001A2")
    assert_404_not_found(
        ex,
        location="ops-family",
        url="https://ops.epo.org/3.2/rest-services/family/publication/docdb/(EP).(0000001).(A2)?(EP).(0000001).(A2)",
    )


def test_family_docdb_xml_success(ops_client):
    response = ops_family_publication_docdb_xml(ops_client,
        reference_type="publication",
        document_number="EP0666666A2",
        constituents="biblio",
    )
    assert response.startswith('<?xml version="1.0" encoding="UTF-8"?>')


def test_family_docdb_xml_not_found_failure(ops_client):
    with pytest.raises(ServiceError) as ex:
        ops_family_publication_docdb_xml(ops_client,
            reference_type="publication",
            document_number="EP0000001A2",
            constituents="biblio",
        )
    assert_404_not_found(
        ex,
        location="ops-family",
        url="https://ops.epo.org/3.2/rest-services/family/publication/docdb/(EP).(0000001).(A2)/biblio?(EP).(0000001).(A2)",
    )


def test_register_json_success(ops_client):
    response = ops_register(ops_client, reference_type="publication", document_number="EP0666666A2")
    reg_countries = jpath("/ops:world-patent-data/ops:register-search/reg:register-documents"
                          "/reg:register-document/reg:bibliographic-data/reg:designation-of-states"
                          "/reg:designation-pct/reg:regional/reg:country", response)
    assert list(_flatten_ops_json_list(reg_countries)) == ['DE', 'FR', 'GB']


def test_register_xml_success(ops_client):
    response = ops_register(ops_client, reference_type="publication", document_number="EP0666666A2", xml=True)
    assert response.startswith('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>')


def test_register_not_found_failure(ops_client):
    with pytest.raises(ServiceError) as ex:
        ops_register(ops_client, reference_type="publication", document_number="EP0A2")
    assert_404_not_found(
        ex,
        location="ops-register",
        url="https://ops.epo.org/3.2/rest-services/register/publication/epodoc/biblio,legal",
    )


def test_service_usage(ops_client):
    response = ops_service_usage(ops_client, "01/01/2022", "02/01/2022")
    assert sorted(response.keys()) == ["message-count", "response-size", "time-range"]
