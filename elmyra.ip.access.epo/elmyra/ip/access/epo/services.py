# -*- coding: utf-8 -*-
# (c) 2013,2014 Andreas Motl, Elmyra UG
import json
import logging
from pymongo.errors import OperationFailure
import re
import arrow
from urllib import unquote_plus
from beaker.cache import cache_region
from cornice import Service
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest
from pyramid.response import Response
from pyramid.settings import asbool
from elmyra.ip.access.dpma.depatisconnect import depatisconnect_claims, depatisconnect_description, depatisconnect_abstracts
from elmyra.ip.access.dpma.depatisnet import DpmaDepatisnetAccess
from elmyra.ip.access.drawing import get_drawing_png
from elmyra.ip.access.epo.core import pdf_universal, pdf_universal_multi
from elmyra.ip.access.epo.ops import get_ops_client, ops_published_data_search, get_ops_image, pdf_document_build, inquire_images, ops_description, ops_claims, ops_document_kindcodes, ops_family_inpadoc, ops_analytics_applicant_family, ops_service_usage, ops_published_data_crawl
from elmyra.ip.access.google.search import GooglePatentsAccess, GooglePatentsExpression
from elmyra.ip.access.ftpro.expression import FulltextProExpression
from elmyra.ip.access.ftpro.search import LoginException, SearchException, ftpro_published_data_search, ftpro_published_data_crawl
from elmyra.ip.util.cql.pyparsing import CQL
from elmyra.ip.util.cql.util import pair_to_cql, should_be_quoted
from elmyra.ip.util.date import datetime_iso_filename, now
from elmyra.ip.util.expression.keywords import clean_keyword, keywords_from_boolean_expression
from elmyra.ip.util.numbers.common import split_patent_number
from elmyra.ip.util.numbers.numberlists import parse_numberlist, normalize_numbers
from elmyra.ip.util.python import _exception_traceback
from elmyra.ip.util.xml.format import pretty_print
from elmyra.web.identity.store import User

log = logging.getLogger(__name__)

# ------------------------------------------
#   services: ops
# ------------------------------------------
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

drawing_service = Service(
    name='drawing',
    path='/api/drawing/{patent}',
    description="Retrieve drawings for patent documents")

ops_fullimage_service = Service(
    name='ops-fullimage',
    path='/api/ops/{patent}/image/full',
    description="OPS fullimage interface")

pdf_service = Service(
    name='pdf',
    path='/api/pdf/{patent}',
    description="Retrieve patent document PDF files")

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

ops_analytics_applicant_family_service = Service(
    name='ops-analytics-applicant-family',
    path='/api/ops/analytics/applicant-family/{applicant}',
    renderer='prettyjson',
    description="OPS applicant-family analytics interface")

ops_usage_service = Service(
    name='ops-usage',
    path='/api/ops/usage/{kind}',
    renderer='prettyjson',
    description="OPS usage interface")


# ------------------------------------------
#   services: depatisnet
# ------------------------------------------
depatisnet_published_data_search_service = Service(
    name='depatisnet-published-data-search',
    path='/api/depatisnet/published-data/search',
    description="DEPATISnet search interface")
depatisnet_published_data_crawl_service = Service(
    name='depatisnet-published-data-crawl',
    path='/api/depatisnet/published-data/crawl{dummy1:\/?}{constituents:.*?}',
    description="DEPATISnet crawler interface")

depatisconnect_description_service = Service(
    name='depatisconnect-description',
    path='/api/depatisconnect/{patent}/description',
    description="DEPATISconnect description interface")

depatisconnect_claims_service = Service(
    name='depatisconnect-claims',
    path='/api/depatisconnect/{patent}/claims',
    description="DEPATISconnect claims interface")

depatisconnect_abstract_service = Service(
    name='depatisconnect-abstract',
    path='/api/depatisconnect/{patent}/abstract',
    description="DEPATISconnect abstract interface")


# ------------------------------------------
#   services: google
# ------------------------------------------
google_published_data_search_service = Service(
    name='google-published-data-search',
    path='/api/google/published-data/search',
    description="Google Patents search interface")


# ------------------------------------------
#   services: ftpro
# ------------------------------------------
ftpro_published_data_search_service = Service(
    name='ftpro-published-data-search',
    path='/api/ftpro/published-data/search',
    description="FulltextPRO search interface")
ftpro_published_data_crawl_service = Service(
    name='ftpro-published-data-crawl',
    path='/api/ftpro/published-data/crawl{dummy1:\/?}{constituents:.*?}',
    description="FulltextPRO crawler interface")


# ------------------------------------------
#   services: misc
# ------------------------------------------
query_expression_util_service = Service(
    name='query-expression-utility-service',
    path='/api/util/query-expression',
    description="Query expression utility service")

numberlist_util_service = Service(
    name='numberlist-utility-service',
    path='/api/util/numberlist',
    description="Numberlist utility service")

void_service = Service(
    name='void-service',
    path='/api/void',
    description="Void service")


# ------------------------------------------
#   services: admin
# ------------------------------------------
admin_users_emails_service = Service(
    name='admin-users-email-service',
    path='/api/admin/users/emails',
    description="Responds with email addresses of all customers")


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

    query_object, query = cql_prepare_query(query)

    log.info('query cql: ' + query)

    # range: x-y, maximum delta is 100, default is 25
    range = request.params.get('range')
    range = range or '1-25'

    result = ops_published_data_search(constituents, query, range)
    propagate_keywords(request, query_object)

    log.info('query finished')

    return result


@ops_published_data_crawl_service.get(accept="application/json")
def ops_published_data_crawl_handler(request):
    """Crawl published-data at OPS"""

    # constituents: abstract, biblio and/or full-cycle
    constituents = request.matchdict.get('constituents', 'full-cycle')
    print 'constituents:', constituents

    # CQL query string
    query = request.params.get('query', '')
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



@depatisnet_published_data_search_service.get(accept="application/json")
def depatisnet_published_data_search_handler(request):
    """Search for published-data at DEPATISnet"""

    # CQL query string
    query = request.params.get('query', '')
    log.info('query raw: ' + query)

    query_object, query = cql_prepare_query(query)

    log.info('query cql: ' + query)

    propagate_keywords(request, query_object)

    # lazy-fetch more entries up to maximum of depatisnet
    # TODO: get from elmyra.ip.access.dpma.depatisnet
    request_size = 250
    if int(request.params.get('range_begin', 0)) > request_size:
        request_size = 1000

    try:
        return dpma_published_data_search(query, request_size)

    except SyntaxError as ex:
        request.errors.add('depatisnet-published-data-search', 'query', str(ex.msg))


@depatisnet_published_data_crawl_service.get(accept="application/json")
def depatisnet_published_data_crawl_handler(request):
    """Crawl published-data at DEPATISnet"""

    # CQL query string
    query = request.params.get('query', '')
    log.info('query raw: ' + query)

    query_object, query = cql_prepare_query(query)
    propagate_keywords(request, query_object)

    chunksize = 1000

    log.info('query cql: ' + query)
    try:
        result = dpma_published_data_search(query, chunksize)
        return result

    except Exception as ex:
        log.error(u'DEPATISnet crawler error: query="{0}", reason={1}, Exception was:\n{2}'.format(query, ex, _exception_traceback()))
        request.errors.add('depatisnet-published-data-crawl', 'query', str(ex))


def cql_prepare_query(query):

    # fixup query: wrap into quotes if cql string is a) unspecific, b) contains spaces and c) is still unquoted
    if should_be_quoted(query) and 'within' not in query:
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

    return query_object, query


@google_published_data_search_service.get(accept="application/json")
def google_published_data_search_handler(request):
    """Search for published-data at Google Patents"""

    # CQL query string
    query = request.params.get('query', '')
    log.info('query raw: ' + query)

    #propagate_keywords(request, query_object)

    # lazy-fetch more entries up to maximum of FulltextPRO
    # TODO: get from elmyra.ip.access.google
    limit = 100
    offset_local = int(request.params.get('range_begin', 1))
    offset_remote = int(offset_local / limit) * limit

    try:
        data = google_published_data_search(query, offset_remote, limit)
        return data

    except SyntaxError as ex:
        request.errors.add('google-search', 'query', str(ex.msg))

    except ValueError as ex:
        request.errors.add('google-search', 'query', str(ex))


@ftpro_published_data_search_service.get(accept="application/json")
def ftpro_published_data_search_handler(request):
    """Search for published-data at FulltextPRO"""

    # XML query expression
    query = request.params.get('query', '')
    log.info('query raw: ' + query)

    # fixup query: wrap into quotes if cql string is a) unspecific, b) contains spaces and c) is still unquoted
    if should_be_quoted(query):
        query = '"%s"' % query

    #propagate_keywords(request, query_object)

    # lazy-fetch more entries up to maximum of FulltextPRO
    # TODO: get from elmyra.ip.access.ftpro
    limit = 250
    offset_local = int(request.params.get('range_begin', 1))
    offset_remote = int(offset_local / limit) * limit

    try:
        data = ftpro_published_data_search(query, offset_remote, limit)
        return data

    except LoginException as ex:
        request.errors.add('FulltextPRO', 'login', ex.ftpro_info)

    except SearchException as ex:
        request.errors.add('FulltextPRO', 'search', ex.ftpro_info)

    except SyntaxError as ex:
        request.errors.add('FulltextPRO', 'query', str(ex.msg))

    except OperationFailure as ex:
        log.error(ex)
        message = str(ex)
        message = re.sub('namespace: .*', '', message)
        request.errors.add('FulltextPRO', 'query', message)

@ftpro_published_data_crawl_service.get(accept="application/json")
def ftpro_published_data_crawl_handler(request):
    """Crawl published-data at FulltextPRO"""

    # XML query expression
    query = request.params.get('query', '')
    log.info('query raw: ' + query)

    if should_be_quoted(query):
        query = '"%s"' % query

    # constituents: abstract, biblio and/or full-cycle
    constituents = request.matchdict.get('constituents', 'full-cycle')
    print 'constituents:', constituents

    chunksize = int(request.params.get('chunksize', '2500'))

    try:
        result = ftpro_published_data_crawl(constituents, query, chunksize)
        return result

    except Exception as ex:
        log.error(u'FulltextPRO crawler error: query="{0}", reason={1}, Exception was:\n{2}'.format(query, ex, _exception_traceback()))
        request.errors.add('ftpro-published-data-crawl', 'query', str(ex))


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

    # TODO: move to some ops.py

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
            keyword = clean_keyword(unicode(op.term))
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

@cache_region('search')
def google_published_data_search(query, offset, limit):
    google = GooglePatentsAccess()
    try:
        return google.search(query, offset, limit)
    except SyntaxError as ex:
        log.warn('Invalid query for Google Patents: %s' % ex.msg)
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


@pdf_service.get(renderer='null')
def pdf_handler(request):
    """request full document as pdf, universal datasource"""

    if ',' in request.matchdict['patent']:
        return pdf_serve_multi(request)
    else:
        return pdf_serve_single(request)


def pdf_serve_single(request):

    patent = request.matchdict['patent']
    #parts = request.matchdict['parts']

    data = pdf_universal(patent)

    if data.get('pdf'):
        # http://tools.ietf.org/html/rfc6266#section-4.2
        request.response.content_type = 'application/pdf'
        request.response.charset = None
        request.response.headers['Content-Disposition'] = 'inline; filename={0}.pdf'.format(patent)
        request.response.headers['X-Pdf-Source'] = data['datasource']
        return data['pdf']

    else:
        raise HTTPNotFound('No PDF for document {0}'.format(patent))


def pdf_serve_multi(request):
    patents_raw = request.matchdict['patent']
    patents = patents_raw.split(',')
    patents = [patent.strip() for patent in patents]

    data = pdf_universal_multi(patents)
    zipfilename = 'ipsuite-collection-pdf_{0}.zip'.format(datetime_iso_filename(now()))

    # http://tools.ietf.org/html/rfc6266#section-4.2
    request.response.content_type = 'application/zip'
    request.response.charset = None
    request.response.headers['Content-Disposition'] = 'attachment; filename={0}'.format(zipfilename)
    return data['zip']


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

@ops_analytics_applicant_family_service.get()
def ops_analytics_applicant_family_handler(request):
    # TODO: respond with proper 4xx codes if something fails
    applicant = unquote_plus(request.matchdict['applicant'])
    response = ops_analytics_applicant_family(applicant)
    return response

@ops_usage_service.get()
def ops_usage_handler(request):
    # TODO: respond with proper 4xx codes if something fails
    kind = request.matchdict['kind']
    now = arrow.utcnow()
    if kind == 'day':
        date_begin = now.replace(days=-1)
        date_end = now

    elif kind == 'week':
        date_begin = now.replace(weeks=-1)
        date_end = now

    elif kind == 'month':
        date_begin = now.replace(months=-1)
        date_end = now

    elif kind == 'year':
        date_begin = now.replace(years=-1)
        date_end = now

    else:
        raise HTTPNotFound('Use /day, {0} not implemented'.format(kind))

    date_begin = date_begin.format('DD/MM/YYYY')
    date_end = date_end.format('DD/MM/YYYY')

    response = ops_service_usage(date_begin, date_end)
    return response


@depatisconnect_claims_service.get()
def depatisconnect_claims_handler(request):
    # TODO: use jsonified error responses
    patent = request.matchdict['patent']
    try:
        description = depatisconnect_claims(patent)

    except KeyError as ex:
        log.error('Problem fetching details of DEPATISconnect: %s %s', type(ex), ex)
        raise HTTPNotFound(ex)

    except ValueError as ex:
        log.error('Problem fetching details of DEPATISconnect: %s %s', type(ex), ex)
        raise HTTPBadRequest(ex)

    return description


@depatisconnect_description_service.get()
def depatisconnect_description_handler(request):
    # TODO: use jsonified error responses
    patent = request.matchdict['patent']
    try:
        description = depatisconnect_description(patent)

    except KeyError as ex:
        log.error('Problem fetching details of DEPATISconnect: %s %s', type(ex), ex)
        raise HTTPNotFound(ex)

    except ValueError as ex:
        log.error('Problem fetching details of DEPATISconnect: %s %s', type(ex), ex)
        raise HTTPBadRequest(ex)

    return description


@depatisconnect_abstract_service.get()
def depatisconnect_abstract_handler(request):
    # TODO: use jsonified error responses
    patent = request.matchdict['patent']
    language = request.params.get('language')
    try:
        abstract = depatisconnect_abstracts(patent, language)

    except KeyError as ex:
        log.error('Problem fetching details of DEPATISconnect: %s %s', type(ex), ex)
        raise HTTPNotFound(ex)

    except ValueError as ex:
        log.error('Problem fetching details of DEPATISconnect: %s %s', type(ex), ex)
        raise HTTPBadRequest(ex)

    return abstract


@query_expression_util_service.post()
def query_expression_util_handler(request):

    # TODO: split functionality between ops/depatisnet, google and ftpro/ftpro

    data = request.json

    datasource = data['datasource']
    criteria = data['criteria']
    modifiers = data.get('modifiers', {})
    query = data.get('query')

    if datasource == 'ftpro':
        modifiers = FulltextProExpression.compute_modifiers(modifiers)

    expression = ''
    expression_parts = []
    keywords = []

    if data['format'] == 'comfort':

        if datasource == 'google':
            gpe = GooglePatentsExpression(criteria, query)
            expression = gpe.serialize()
            keywords = gpe.get_keywords()

        else:

            for key, value in criteria.iteritems():

                if not value:
                    continue

                # allow notations like "DE or EP or US" and "DE,EP"
                if key == 'country':
                    entries = re.split('(?: or |,)', value, flags=re.IGNORECASE)
                    entries = [entry.strip() for entry in entries]
                    value = ' or '.join(entries)

                expression_part = None

                if datasource in ['ops', 'depatisnet']:
                    expression_part = pair_to_cql(datasource, key, value)

                elif datasource == 'ftpro':
                    expression_part = FulltextProExpression.pair_to_ftpro_xml(key, value, modifiers)
                    if expression_part:
                        if expression_part.has_key('keywords'):
                            keywords += expression_part['keywords']
                        else:
                            keywords += keywords_from_boolean_expression(key, value)

                error_tpl = u'Criteria "{0}: {1}" has invalid format, datasource={2}.'
                if not expression_part:
                    message = error_tpl.format(key, value, datasource)
                    log.warn(message)
                    request.errors.add('query-expression-utility-service', 'comfort-form', message)

                elif expression_part.has_key('error'):
                    message = error_tpl.format(key, value, datasource)
                    message += u'<br/>' + expression_part['message']
                    log.warn(message)
                    request.errors.add('query-expression-utility-service', 'comfort-form', message)

                else:
                    expression_part.get('query') and expression_parts.append(expression_part.get('query'))


    log.info("keywords: %s", keywords)
    request.response.headers['X-Elmyra-Query-Keywords'] = json.dumps(keywords)


    # assemble complete expression from parts, connect them with AND operators
    if datasource in ['ops', 'depatisnet']:
        expression = ' and '.join(expression_parts)

    elif datasource == 'ftpro':
        if expression_parts:
            if len(expression_parts) == 1:
                expression = expression_parts[0]
            else:
                expression = '\n'.join(expression_parts)
                expression = '<and>\n' + expression + '\n</and>'
            expression = pretty_print(expression)

    return expression


@numberlist_util_service.post()
def numberlist_util_handler(request):
    response = {}
    numberlist = None

    if request.content_type == 'text/plain':
        numberlist = parse_numberlist(request.text)
        response['numbers-sent'] = numberlist

    if numberlist:
        if asbool(request.params.get('normalize')):
            response['numbers-normalized'] = normalize_numbers(numberlist)

    return response

@admin_users_emails_service.get()
def admin_users_emails_handler(request):
    users = User.objects()
    user_emails = ['support@elmyra.de']
    for user in users:
        if '@' not in user.username:
            continue
        user_emails.append(user.username.lower())

    payload = u'\n'.join(user_emails)

    return Response(payload, content_type='text/plain', charset='utf-8')
