# -*- coding: utf-8 -*-
# (c) 2013-2017 Andreas Motl, Elmyra UG
import logging
from cornice.service import Service
from pyramid.httpexceptions import HTTPNotFound
from pyramid.settings import asbool
from elmyra.ip.access.epo.ops import ops_published_data_crawl, inquire_images, get_ops_image, ops_family_inpadoc, get_ops_client, pdf_document_build, ops_claims, ops_document_kindcodes, ops_description, ops_published_data_search, ops_published_data_search_invalidate, ops_published_data_search_swap_family
from elmyra.ip.access.epo.services import propagate_keywords, cql_prepare_query
from elmyra.ip.access.generic.exceptions import NoResultsException
from elmyra.ip.util.numbers.common import split_patent_number
from elmyra.ip.util.python import _exception_traceback

log = logging.getLogger(__name__)

ops_published_data_search_service = Service(
    name='ops-published-data-search',
    path='/api/ops/published-data/search',
    description="OPS search interface")
ops_published_data_crawl_service = Service(
    name='ops-published-data-crawl',
    path='/api/ops/published-data/crawl{dummy1:\/?}{constituents:.*?}',
    description="OPS crawler interface")

ops_family_simple_service = Service(
    name='ops-family-simple',
    path='/api/ops/{patent}/family/simple',
    description="OPS family simple interface")
ops_family_inpadoc_service = Service(
    name='ops-family-inpadoc',
    path='/api/ops/{reference_type}/{patent}/family/inpadoc',
    description="OPS family inpadoc interface")

ops_image_info_service = Service(
    name='ops-image-info',
    path='/api/ops/{patent}/image/info',
    description="OPS image info interface")

ops_fullimage_service = Service(
    name='ops-fullimage',
    path='/api/ops/{patent}/image/full',
    description="OPS fullimage interface")

ops_pdf_service = Service(
    name='ops-pdf',
    path='/api/ops/{patent}/pdf/{parts}',
    description="OPS pdf interface")

ops_description_service = Service(
    name='ops-description',
    path='/api/ops/{patent}/description',
    description="OPS description interface")

ops_claims_service = Service(
    name='ops-claims',
    path='/api/ops/{patent}/claims',
    description="OPS claims interface")

ops_kindcode_service = Service(
    name='ops-kindcodes',
    path='/api/ops/{patent}/kindcodes',
    description="OPS kindcodes interface")



@ops_published_data_search_service.get(accept="application/json")
def ops_published_data_search_handler(request):
    """Search for published-data at OPS"""

    # Constituents: abstract, biblio and/or full-cycle
    constituents = request.params.get('constituents', 'full-cycle')

    # CQL query string
    query = request.params.get('expression', '')
    log.info('query raw: %s', query)

    query_object, query = cql_prepare_query(query)

    log.info('query cql: %s', query)

    # range: x-y, maximum delta is 100, default is 25
    range = request.params.get('range')
    range = range or '1-25'

    # Search options
    family_swap_default = asbool(request.params.get('family_swap_default'))

    # invalidate cache
    invalidate = asbool(request.params.get('invalidate', 'false'))
    if invalidate:
        ops_published_data_search_invalidate(constituents, query, range)

    try:
        if family_swap_default:
            result = ops_published_data_search_swap_family(constituents, query, range)
        else:
            result = ops_published_data_search(constituents, query, range)
        propagate_keywords(request, query_object)

    except NoResultsException as ex:
        # Forward response to let the frontend recognize zero hits
        request.response.status = HTTPNotFound.code
        return ex.data

    log.info('query finished')

    return result


@ops_published_data_crawl_service.get(accept="application/json")
def ops_published_data_crawl_handler(request):
    """Crawl published-data at OPS"""

    # constituents: abstract, biblio and/or full-cycle
    constituents = request.matchdict.get('constituents', 'full-cycle')
    print 'constituents:', constituents

    # CQL query string
    query = request.params.get('expression', '')
    log.info('query raw: ' + query)

    query_object, query = cql_prepare_query(query)
    propagate_keywords(request, query_object)

    log.info('query cql: ' + query)


    chunksize = int(request.params.get('chunksize', '100'))

    try:
        result = ops_published_data_crawl(constituents, query, chunksize)
        return result

    except Exception as ex:
        log.error(u'OPS crawler error: query="{0}", reason={1}, Exception was:\n{2}'.format(query, ex, _exception_traceback()))
        request.errors.add('ops-published-data-crawl', 'query', str(ex))


@ops_image_info_service.get()
def ops_image_info_handler(request):
    patent = request.matchdict['patent']
    info = inquire_images(patent)
    return info


@ops_fullimage_service.get(renderer='pdf')
def ops_fullimage_handler(request):
    """request full image as pdf"""
    # http://ops.epo.org/3.1/rest-services/published-data/images/EP/1000000/A1/fullimage.pdf?Range=1

    # TODO: respond with proper 4xx codes if something fails

    patent = request.matchdict['patent']
    page = int(request.params.get('page', 1))
    pdf = get_ops_image(patent, page, 'FullDocument', 'pdf')
    return pdf


@ops_family_inpadoc_service.get(accept='application/json')
def ops_family_inpadoc_json_handler(request):
    reference_type = request.matchdict.get('reference_type')
    patent = request.matchdict.get('patent')

    # constituents: biblio, legal
    constituents = request.params.get('constituents', '')

    return ops_family_inpadoc(reference_type, patent, constituents)


@ops_family_inpadoc_service.get(accept='text/xml', renderer='xml')
def ops_family_publication_xml_handler(request):
    """
    Download requested family publication information from OPS
    e.g. http://ops.epo.org/3.1/rest-services/family/publication/docdb/EP.1491501.A1/biblio,legal
    """

    url_tpl = 'https://ops.epo.org/3.1/rest-services/family/publication/docdb/{patent}/{constituents}'

    # split patent number
    patent = split_patent_number(request.matchdict.get('patent'))
    patent_dotted = '.'.join([patent['country'], patent['number'], patent['kind']])

    # constituents: biblio, legal, xxx?
    constituents = request.params.get('constituents', 'biblio')

    url = url_tpl.format(patent=patent_dotted, constituents=constituents)
    client = get_ops_client()
    #response = client.get(url, headers={'Accept': 'application/json'})
    response = client.get(url, headers={'Accept': 'text/xml'})
    #print "response:", response.content

    return response.content


@ops_pdf_service.get(renderer='pdf')
def ops_pdf_handler(request):
    """request full document as pdf from OPS"""
    # http://ops.epo.org/3.1/rest-services/published-data/images/EP/1000000/A1/fullimage.pdf?Range=1

    # TODO: respond with proper 4xx codes if something fails

    patent = request.matchdict['patent']
    parts = request.matchdict['parts']

    pdf_payload = pdf_document_build(patent)

    # http://tools.ietf.org/html/rfc6266#section-4.2
    request.response.headers['Content-Disposition'] = 'inline; filename={0}.pdf'.format(patent)
    request.response.headers['X-Pdf-Source'] = 'ops'

    return pdf_payload


@ops_claims_service.get()
def ops_claims_handler(request):
    # TODO: respond with proper 4xx codes if something fails
    patent = request.matchdict['patent']
    description = ops_claims(patent)
    return description

@ops_description_service.get()
def ops_description_handler(request):
    # TODO: respond with proper 4xx codes if something fails
    patent = request.matchdict['patent']
    description = ops_description(patent)
    return description

@ops_kindcode_service.get()
def ops_kindcode_handler(request):
    # TODO: respond with proper 4xx codes if something fails
    patent = request.matchdict['patent']
    kindcodes = ops_document_kindcodes(patent)
    return kindcodes
