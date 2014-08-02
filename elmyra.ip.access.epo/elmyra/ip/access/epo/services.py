# -*- coding: utf-8 -*-
# (c) 2013,2014 Andreas Motl, Elmyra UG
import json
import logging
from beaker.cache import cache_region
from cornice import Service
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest
from elmyra.ip.access.dpma.depatisconnect import depatisconnect_claims, depatisconnect_description
from elmyra.ip.access.dpma.depatisnet import DpmaDepatisnetAccess
from elmyra.ip.access.drawing import get_drawing_png
from elmyra.ip.access.epo.ops import get_ops_client, ops_published_data_search, get_ops_image, pdf_document_build, inquire_images, ops_description, ops_claims
from elmyra.ip.util.cql.knowledge import datasource_indexnames
from elmyra.ip.util.cql.pyparsing import CQL
from elmyra.ip.util.date import iso_to_german
from elmyra.ip.util.numbers.common import split_patent_number
from elmyra.ip.util.python import _exception_traceback

log = logging.getLogger(__name__)

# ------------------------------------------
#   services
# ------------------------------------------
ops_published_data_search_service = Service(
    name='ops-published-data-search',
    path='/api/ops/published-data/search',
    description="OPS search interface")

depatisnet_published_data_search_service = Service(
    name='depatisnet-published-data-search',
    path='/api/depatisnet/published-data/search',
    description="DEPATISnet search interface")

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

ops_description_service = Service(
    name='ops-description',
    path='/api/ops/{patent}/description',
    description="OPS description interface")

ops_claims_service = Service(
    name='ops-claims',
    path='/api/ops/{patent}/claims',
    description="OPS claims interface")

depatisconnect_description_service = Service(
    name='depatisconnect-description',
    path='/api/depatisconnect/{patent}/description',
    description="DEPATISconnect description interface")

depatisconnect_claims_service = Service(
    name='depatisconnect-claims',
    path='/api/depatisconnect/{patent}/claims',
    description="DEPATISconnect claims interface")

cql_tool_service = Service(
    name='cql-tool-service',
    path='/api/cql',
    description="CQL tool service")


# ------------------------------------------
#   handlers
# ------------------------------------------
@ops_published_data_search_service.get(accept="application/json")
def ops_published_data_search_handler(request):
    """Search for published-data at OPS"""

    # constituents: abstract, biblio and/or full-cycle
    constituents = request.params.get('constituents', 'full-cycle')

    # CQL query string
    query = request.params.get('query', '')
    log.info('query raw: ' + query)

    # fixup query: wrap into quotes if cql string is a) unspecific, b) contains spaces and c) is still unquoted
    if ('=' not in query and 'within' not in query) and ' ' in query and query[0] != '"' and query[-1] != '"':
        query = '"%s"' % query

    # Parse and recompile CQL query string to apply number normalization
    query_object = None
    try:

        # v1: Cheshire3 CQL parser
        #query_object = cql_parse(query)
        #query = query_object.toCQL().strip()

        # v2 pyparsing CQL parser
        query_object = CQL(query).polish()
        query_recompiled = query_object.dumps()

        if query_recompiled:
            query = query_recompiled

    except Exception as ex:
        # TODO: can we get more details from diagnostic information to just stop here w/o propagating obviously wrong query to OPS?
        log.warn(u'CQL parse error: query="{0}", reason={1}, Exception was:\n{2}'.format(query, ex, _exception_traceback()))

    log.info('query cql: ' + query)

    # range: x-y, maximum delta is 100, default is 25
    range = request.params.get('range')
    range = range or '1-25'

    result = ops_published_data_search(constituents, query, range)
    propagate_keywords(request, query_object)

    log.info('query finished')

    return result



@depatisnet_published_data_search_service.get(accept="application/json")
def depatisnet_published_data_search_handler(request):
    """Search for published-data at DEPATISnet"""

    # CQL query string
    query = request.params.get('query', '')
    log.info('query raw: ' + query)

    # fixup query: wrap into quotes if cql string is a) unspecific, b) contains spaces and c) is still unquoted
    if '=' not in query and ' ' in query and query[0] != '"' and query[-1] != '"':
        query = '"%s"' % query

    # Parse and recompile CQL query string to apply number normalization
    query_object = None
    try:

        # v1: Cheshire3 CQL parser
        #query_object = cql_parse(query)
        #query_recompiled = query_object.toCQL().strip()

        # v2 pyparsing CQL parser
        query_object = CQL(query).polish()
        query_recompiled = query_object.dumps()

        if query_recompiled:
            query = query_recompiled

    except Exception as ex:
        # TODO: can we get more details from diagnostic information to just stop here w/o propagating obviously wrong query to OPS?
        log.warn(u'CQL parse error: query="{0}", reason={1}, Exception was:\n{2}'.format(query, ex, _exception_traceback()))

    log.info('query cql: ' + query)

    propagate_keywords(request, query_object)

    try:
        return dpma_published_data_search(query, 250)

    except SyntaxError as ex:
        request.errors.add('depatisnet-published-data-search', 'query', str(ex.msg))


def propagate_keywords(request, query_object):
    """propagate keywords to client for highlighting"""
    if query_object:
        if type(query_object) is CQL:
            keywords = query_object.keywords()
            # TODO: how to build a unique list of keywords? the list now can contain lists (TypeError: unhashable type: 'list')
            # possible solution: iterate list, convert lists to tuples, then list(set(keywords)) is possible
        else:
            keywords = compute_keywords(query_object)

        log.info("keywords: %s", keywords)
        request.response.headers['X-Elmyra-Query-Keywords'] = json.dumps(keywords)

def compute_keywords(query_object):
    keywords = []
    scan_keywords(query_object, keywords)
    keywords = list(set(keywords))
    return keywords

def scan_keywords(op, keywords):

    if not op: return
    #print "op:", dir(op)

    keyword_fields = [

        # OPS
        'title', 'ti',
        'abstract', 'ab',
        'titleandabstract', 'ta',
        'txt',
        'applicant', 'pa',
        'inventor', 'in',
        'ct', 'citation',

        # classifications
        'ipc', 'ic',
        'cpc', 'cpci', 'cpca', 'cl',

        # application and priority
        'ap', 'applicantnumber', 'sap',
        'pr', 'prioritynumber', 'spr',

        # DEPATISnet
        'ti', 'ab', 'de', 'bi',
        'pa', 'in',
    ]

    if hasattr(op, 'index'):
        #print "op.index:", op.index
        #print "op.term:", op.term
        if str(op.index) in keyword_fields:
            keyword = unicode(op.term).strip('?').strip('*')
            keywords.append(keyword)

    hasattr(op, 'leftOperand') and scan_keywords(op.leftOperand, keywords)
    hasattr(op, 'rightOperand') and scan_keywords(op.rightOperand, keywords)

@cache_region('search')
def dpma_published_data_search(query, hits_per_page):
    depatisnet = DpmaDepatisnetAccess()
    try:
        return depatisnet.search_patents(query, hits_per_page)
    except SyntaxError as ex:
        log.warn('Invalid query for DEPATISnet: %s' % ex.msg)
        raise

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

@depatisconnect_claims_service.get()
def depatisconnect_claims_handler(request):
    # TODO: use jsonified error responses
    patent = request.matchdict['patent']
    try:
        description = depatisconnect_claims(patent)
    except KeyError as ex:
        raise HTTPNotFound(ex)
    except ValueError as ex:
        raise HTTPBadRequest(ex)
    return description

@depatisconnect_description_service.get()
def depatisconnect_description_handler(request):
    # TODO: use jsonified error responses
    patent = request.matchdict['patent']
    try:
        description = depatisconnect_description(patent)
    except KeyError as ex:
        raise HTTPNotFound(ex)
    except ValueError as ex:
        raise HTTPBadRequest(ex)
    return description


@cql_tool_service.post()
def cql_tool_handler(request):
    data = request.json
    source = data['datasource']

    cql_parts = []

    if data['format'] == 'comfort':
        for key, value in data['criteria'].iteritems():

            try:
                fieldname = datasource_indexnames[key][source]
            except KeyError:
                continue

            cql_part = None
            format = u'{0}=({1})'

            query_has_booleans = ' or ' in value.lower() or ' and ' in value.lower() or ' not ' in value.lower()

            # special processing rules for depatisnet
            if source == 'depatisnet':

                if key == 'pubdate':

                    if len(value) == 4 and value.isdigit():
                        fieldname = 'py'

                    elif 'within' in value:
                        value = value.replace('within', '').strip()
                        parts = value.split(',')
                        parts = map(unicode.strip, parts)
                        print parts
                        elements_are_years = all([len(part) == 4 and part.isdigit() for part in parts])
                        if elements_are_years:
                            fieldname = 'py'
                        cql_part = '{fieldname} >= {left} and {fieldname} <= {right}'.format(
                            fieldname=fieldname, left=iso_to_german(parts[0]), right=iso_to_german(parts[1]))

                    else:
                        value = iso_to_german(value)

                elif key == 'inventor':
                    if ' ' in value and not query_has_booleans:
                        value = value.replace(' ', '(L)')


            elif source == 'ops':

                if key == 'inventor':
                    if ' ' in value and not query_has_booleans:
                        value = '"{0}"'.format(value)

                if 'within' in value:
                    format = '{0} {1}'

            if not cql_part:
                cql_part = format.format(fieldname, value)

            cql_parts.append(cql_part)


    cql = ' and '.join(cql_parts)
    return cql
