# -*- coding: utf-8 -*-
# (c) 2013-2026 Andreas Motl, Elmyra UG
import logging

from fastapi import APIRouter, Request, Response

from patzilla.access.epo.ops.api import inquire_images, get_ops_image, ops_family_inpadoc, \
    pdf_document_build, ops_claims, ops_document_kindcodes, ops_description, ops_family_publication_docdb_xml, \
    ops_published_data_search, ops_published_data_search_real, ops_published_data_search_swap_family, \
    ops_published_data_crawl, ops_register
from patzilla.access.generic.exceptions import NoResultsException, ServiceError
from patzilla.navigator.services import cql_prepare_query, handle_generic_exception
from patzilla.util.expression.keywords import keywords_to_response
from patzilla.util.python import _exception_traceback
from patzilla.web.dependencies import LenientBool, OpsClient, prefers_xml

log = logging.getLogger(__name__)

router = APIRouter(tags=["ops"])


@router.get("/api/status/upstream/epo/ops", name="status_ops",
            summary="Checks EPO OPS upstream for valid response")
def status_upstream_ops_handler(client: OpsClient):
    data = ops_published_data_search_real(client, 'full-cycle', 'pn=EP666666', '1-10')
    assert data, 'Empty response from OPS'
    return "OK"


@router.get("/api/ops/published-data/search", name="ops-published-data-search", summary="OPS search interface")
def ops_published_data_search_handler(response: Response, client: OpsClient, expression: str = '',
                                      constituents: str = 'full-cycle', range: str = '1-25',
                                      family_swap_default: LenientBool = False):
    """Search for published-data at OPS"""

    # CQL query string
    log.info('query raw: %s', expression)

    # Transcode CQL query expression
    search = cql_prepare_query(expression)
    log.info('query cql: %s', search.expression)

    # range: x-y, maximum delta is 100, default is 25
    range = range or '1-25'

    try:
        if family_swap_default:
            result = ops_published_data_search_swap_family(client, constituents, search.expression, range).data
        else:
            result = ops_published_data_search(client, constituents, search.expression, range)

        # Propagate keywords to highlighting component
        keywords_to_response(response, search=search)
        return result

    except NoResultsException as ex:
        # Forward response to let the frontend recognize zero hits
        response.status_code = 404
        return ex.data

    except Exception as ex:
        message = handle_generic_exception(ex, 'ops-search', search.expression)
        raise ServiceError('ops-search', 'search', message)


@router.get("/api/ops/published-data/crawl", name="ops-published-data-crawl", summary="OPS crawler interface")
@router.get("/api/ops/published-data/crawl/{constituents:path}", name="ops-published-data-crawl")
def ops_published_data_crawl_handler(response: Response, client: OpsClient, constituents: str = 'full-cycle',
                                     expression: str = '', chunksize: int = 100):
    """Crawl published-data at OPS"""

    log.info('query raw: ' + expression)
    search = cql_prepare_query(expression)
    keywords_to_response(response, search=search)
    log.info('query cql: ' + search.expression)

    try:
        return ops_published_data_crawl(client, constituents, search.expression, chunksize)

    except Exception as ex:
        log.error('OPS crawler error: query="{0}", reason={1}, Exception was:\n{2}'.format(
            expression, ex, _exception_traceback()))
        raise ServiceError('ops-published-data-crawl', 'query', str(ex))


@router.get("/api/ops/{patent}/image/info", name="ops-image-info", summary="OPS image info interface")
def ops_image_info_handler(patent: str, client: OpsClient):
    return inquire_images(client, patent)


@router.get("/api/ops/{patent}/image/full", name="ops-fullimage", summary="OPS fullimage interface")
def ops_fullimage_handler(patent: str, client: OpsClient, page: int = 1):
    """request full image as pdf"""
    # http://ops.epo.org/3.1/rest-services/published-data/images/EP/1000000/A1/fullimage.pdf?Range=1
    return Response(get_ops_image(client, patent, page, 'FullDocument', 'pdf'), media_type='application/pdf')


@router.get("/api/ops/{reference_type}/{patent}/family/inpadoc", name="ops-family-inpadoc",
            summary="OPS family inpadoc interface")
def ops_family_inpadoc_handler(request: Request, reference_type: str, patent: str, client: OpsClient,
                               constituents: str = ''):
    """Responds with JSON, or XML when preferred by the client. constituents: biblio, legal"""
    if prefers_xml(request):
        xml = ops_family_publication_docdb_xml(client, reference_type, patent, constituents)
        return Response(xml, media_type='text/xml')
    return ops_family_inpadoc(client, reference_type, patent, constituents)


@router.get("/api/ops/{patent}/pdf/{parts}", name="ops-pdf", summary="OPS pdf interface")
def ops_pdf_handler(patent: str, parts: str, client: OpsClient):
    """request full document as pdf from OPS"""
    # http://tools.ietf.org/html/rfc6266#section-4.2
    return Response(pdf_document_build(client, patent), media_type='application/pdf', headers={
        'Content-Disposition': 'inline; filename={0}.pdf'.format(patent),
        'X-Pdf-Source': 'ops',
    })


@router.get("/api/ops/{patent}/claims", name="ops-claims", summary="OPS claims interface")
def ops_claims_handler(patent: str, client: OpsClient):
    return ops_claims(client, patent)


@router.get("/api/ops/{patent}/description", name="ops-description", summary="OPS description interface")
def ops_description_handler(patent: str, client: OpsClient):
    return ops_description(client, patent)


@router.get("/api/ops/{patent}/kindcodes", name="ops-kindcodes", summary="OPS kindcodes interface")
def ops_kindcode_handler(patent: str, client: OpsClient):
    return ops_document_kindcodes(client, patent)


@router.get("/api/ops/{reference_type}/{patent}/register", name="ops-register", summary="OPS register interface")
def ops_register_handler(request: Request, reference_type: str, patent: str, client: OpsClient,
                         constituents: str = 'biblio,legal'):
    """Responds with JSON, or XML when preferred by the client."""
    if prefers_xml(request):
        return Response(ops_register(client, reference_type, patent, constituents, xml=True), media_type='text/xml')
    return ops_register(client, reference_type, patent, constituents)
