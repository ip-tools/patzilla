# -*- coding: utf-8 -*-
# (c) 2013,2014 Andreas Motl, Elmyra UG
import logging
from cornice import Service
from elmyra.ip.access.drawing import get_drawing_png
from elmyra.ip.access.epo.ops import get_ops_client, ops_published_data_search, get_ops_image, pdf_document_build, inquire_images
from elmyra.ip.util.numbers.common import split_patent_number
from elmyra.ip.util.cql.cheshire3_parser import parse as cql_parse, Diagnostic

log = logging.getLogger(__name__)

# ------------------------------------------
#   services
# ------------------------------------------
ops_published_data_search_service = Service(
    name='ops-published-data-search',
    path='/api/ops/published-data/search',
    description="OPS search interface")

ops_family_publication_service = Service(
    name='ops-family-publication',
    path='/api/ops/{patent}/family/publication',
    description="OPS family publication interface")

ops_image_info_service = Service(
    name='ops-image-info',
    path='/api/ops/{patent}/image/info',
    description="OPS image info interface")

drawing_service = Service(
    name='drawing',
    path='/api/drawing/{patent}',
    description="Retrieve drawings for patent documents")

ops_fullimage_service = Service(
    name='ops-fullimage',
    path='/api/ops/{patent}/image/full',
    description="OPS fullimage interface")

ops_pdf_service = Service(
    name='ops-pdf',
    path='/api/ops/{patent}/pdf/{parts}',
    description="OPS pdf interface")


# ------------------------------------------
#   handlers
# ------------------------------------------
@ops_published_data_search_service.get(accept="application/json")
def ops_published_data_search_handler(request):
    """Search for published-data at OPS"""

    # constituents: abstract, biblio and/or full-cycle
    constituents = request.params.get('constituents', 'biblio')

    # CQL query string
    query = request.params.get('query', '')
    log.info('query raw: ' + query)

    # fixup query: wrap into quotes if cql string is a) unspecific, b) contains spaces and c) is still unquoted
    if '=' not in query and ' ' in query and query[0] != '"' and query[-1] != '"':
        query = '"%s"' % query

    # Parse and recompile CQL query string to apply number normalization
    try:
        query_object = cql_parse(query)
        query = query_object.toCQL().strip()
    except Diagnostic as ex:
        # TODO: can we get more details from diagnostic information to just stop here w/o propagating obviously wrong query to OPS?
        log.warn('CQL parse error: query="{0}", reason={1}'.format(query, str(ex)))

    log.info('query cql: ' + query)

    # range: x-y, maximum delta is 100, default is 25
    range = request.params.get('range')
    range = range or '1-25'

    result = ops_published_data_search(constituents, query, range)

    log.info('query finished')

    return result


@ops_image_info_service.get()
def ops_image_info_handler(request):
    patent = request.matchdict['patent']
    info = inquire_images(patent)
    return info


@drawing_service.get(renderer='png')
def drawing_handler(request):
    """request drawing, convert from tiff to png"""

    # TODO: respond with proper 4xx codes if something fails

    patent = request.matchdict['patent']
    page = int(request.params.get('page', 1))
    png = get_drawing_png(patent, page, 'FullDocumentDrawing')
    return png


@ops_fullimage_service.get(renderer='pdf')
def ops_fullimage_handler(request):
    """request full image as pdf"""
    # http://ops.epo.org/3.1/rest-services/published-data/images/EP/1000000/A1/fullimage.pdf?Range=1

    # TODO: respond with proper 4xx codes if something fails

    patent = request.matchdict['patent']
    page = int(request.params.get('page', 1))
    pdf = get_ops_image(patent, page, 'FullDocument', 'pdf')
    return pdf


@ops_family_publication_service.get(renderer='xml')
def ops_family_publication_handler(request):
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
    """request full document as pdf"""
    # http://ops.epo.org/3.1/rest-services/published-data/images/EP/1000000/A1/fullimage.pdf?Range=1

    # TODO: respond with proper 4xx codes if something fails

    patent = request.matchdict['patent']
    parts = request.matchdict['parts']

    pdf_payload = pdf_document_build(patent)

    # http://tools.ietf.org/html/rfc6266#section-4.2
    request.response.headers['Content-Disposition'] = 'inline; filename={0}.pdf'.format(patent)

    return pdf_payload
