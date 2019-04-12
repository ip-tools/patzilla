# -*- coding: utf-8 -*-
# (c) 2013-2018 Andreas Motl <andreas.motl@ip-tools.org>
import logging

import re
from cornice.service import Service
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest
from beaker.cache import cache_region
from patzilla.access.dpma import dpmaregister
from patzilla.access.generic.exceptions import NoResultsException
from patzilla.util.config import asbool
from patzilla.util.expression.keywords import clean_keyword, keywords_to_response
from patzilla.util.python import _exception_traceback, exception_traceback
from patzilla.access.dpma.depatisconnect import depatisconnect_claims, depatisconnect_abstracts, depatisconnect_description
from patzilla.access.dpma.depatisnet import DpmaDepatisnetAccess
from patzilla.access.epo.espacenet.pyramid import espacenet_claims_handler, espacenet_description_handler
from patzilla.navigator.services import cql_prepare_query, handle_generic_exception, ikofax_prepare_query
from patzilla.navigator.services.util import request_to_options

log = logging.getLogger(__name__)

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

dpma_register_service = Service(
    name='dpma-register',
    path='/api/dpma/register/{type}/{document}',
    description="DPMAregister interface")


status_upstream_depatisnet = Service(
    name='status_depatisnet',
    path='/api/status/upstream/dpma/depatisnet',
    description="Checks DPMA depatisnet upstream for valid response")
status_upstream_depatisconnect = Service(
    name='status_depatisconnect',
    path='/api/status/upstream/dpma/depatisconnect',
    description="Checks DPMA depatisconnect upstream for valid response")
status_upstream_dpmaregister = Service(
    name='status_dpmaregister',
    path='/api/status/upstream/dpma/dpmaregister',
    description="Checks DPMA dpmaregister upstream for valid response")

@status_upstream_depatisnet.get()
def status_upstream_depatisnet_handler(request):
    data = dpma_published_data_search_real('pn=EP666666', None)
    assert data, 'Empty response from depatisnet'
    return "OK"

@status_upstream_depatisconnect.get()
def status_upstream_depatisconnect_handler(request):
    data = depatisconnect_claims_handler_real('DE212016000074U1')
    assert data['xml'], 'Empty response from depatisconnect'
    return "OK"

@status_upstream_dpmaregister.get()
def status_upstream_dpmaregister_handler(request):
    data = dpmaregister.access_register('DE212016000074', 'json')
    assert data, 'Empty response from dpmaregister'
    return "OK"


def prepare_search(request):

    #pprint(request.params)

    # CQL expression string
    expression = request.params.get('expression', '').strip()

    # Compute expression syntax
    syntax_cql = asbool(request.params.get('query_data[modifiers][syntax-cql]'))
    syntax_ikofax = asbool(request.params.get('query_data[modifiers][syntax-ikofax]'))
    syntax = 'cql'
    if syntax_ikofax or expression.startswith('ikofax:'):
        expression = expression.replace('ikofax:', '')
        syntax = 'ikofax'

    log.info(u'DEPATISnet query: {}, syntax: {}'.format(expression, syntax))

    # Compute query options, like
    # - limit
    # - sorting
    # - whether to remove family members
    options = {}
    options.update({'syntax': syntax})

    # propagate request parameters to search options parameters
    request_to_options(request, options)

    # Transcode query expression
    if syntax == 'cql':
        search = cql_prepare_query(expression)
    elif syntax == 'ikofax':
        search = ikofax_prepare_query(expression)
    else:
        request.errors.add('depatisnet-search', 'expression', u'Unknown syntax {}'.format(syntax))

    # Propagate keywords to highlighting component
    keywords_to_response(request, search=search)

    return search, options


# TODO: implement as JSON POST
@depatisnet_published_data_search_service.get(accept="application/json")
@depatisnet_published_data_search_service.post(accept="application/json")
def depatisnet_published_data_search_handler(request):
    """Search for published-data at DEPATISnet"""

    search, options = prepare_search(request)

    # Run query through upstream database
    try:
        return dpma_published_data_search(search.expression, options)

    except SyntaxError as ex:
        request.errors.add('depatisnet-search', 'expression', str(ex.msg))
        log.warn(request.errors)

    except NoResultsException as ex:
        # Forward response to let the frontend recognize zero hits
        request.response.status = HTTPNotFound.code
        return ex.data

    except Exception as ex:
        message = handle_generic_exception(request, ex, 'depatisnet-search', search.expression)
        request.errors.add('depatisnet-search', 'search', message)


@depatisnet_published_data_crawl_service.get(accept="application/json")
@depatisnet_published_data_crawl_service.post(accept="application/json")
def depatisnet_published_data_crawl_handler(request):
    """Crawl published-data at DEPATISnet"""

    search, options = prepare_search(request)

    try:
        result = dpma_published_data_search(search.expression, options)
        return result

    except SyntaxError as ex:
        request.errors.add('depatisnet-search', 'expression', str(ex.msg))
        log.warn(request.errors)

    except Exception as ex:
        http_response = None
        if hasattr(ex, 'http_response'):
            http_response = ex.http_response
        log.error(u'DEPATISnet crawler error: query="{0}", reason={1}\nresponse:\n{2}\nexception:\n{3}'.format(
            query, ex, http_response, _exception_traceback()))

        message = u'An exception occurred while processing your query<br/>Reason: {}'.format(ex)
        request.errors.add('depatisnet-search', 'crawl', message)


@cache_region('search', 'dpma_search')
def dpma_published_data_search(query, options):
    return dpma_published_data_search_real(query, options)

def dpma_published_data_search_real(query, options):
    options = options or {}
    depatisnet = DpmaDepatisnetAccess()
    data = depatisnet.search_patents(query, options)
    #print data.prettify()      # debugging

    # Raise an exception on empty results to skip caching this response
    if data.meta.navigator.count_total == 0:
        raise NoResultsException('No results', data=data)

    return data

@depatisconnect_claims_service.get()
def depatisconnect_claims_handler(request):
    # TODO: use jsonified error responses
    patent = request.matchdict['patent']
    try:
        return depatisconnect_claims_handler_real(patent)
    except:
        return espacenet_claims_handler(patent)

def depatisconnect_claims_handler_real(patent):
    try:
        claims = depatisconnect_claims(patent)

    except KeyError as ex:
        log.error('No details at DEPATISconnect: %s %s', type(ex), ex)
        raise HTTPNotFound(ex)

    except ValueError as ex:
        log.error('Fetching details from DEPATISconnect failed: %s %s', type(ex), ex)
        raise HTTPBadRequest(ex)

    except Exception as ex:
        log.error('Unknown error from DEPATISconnect: %s %s.', type(ex), ex)
        log.error(exception_traceback())
        raise HTTPBadRequest(ex)

    return claims

@depatisconnect_description_service.get()
def depatisconnect_description_handler(request):
    # TODO: use jsonified error responses
    patent = request.matchdict['patent']
    try:
        return depatisconnect_description_handler_real(patent)
    except:
        return espacenet_description_handler(patent)

def depatisconnect_description_handler_real(patent):
    try:
        description = depatisconnect_description(patent)
        if not description['xml']:
            raise KeyError('Description is empty')

    except KeyError as ex:
        log.error('No details at DEPATISconnect: %s %s', type(ex), ex)
        raise HTTPNotFound(ex)

    except ValueError as ex:
        log.error('Fetching details from DEPATISconnect failed: %s %s', type(ex), ex)
        raise HTTPBadRequest(ex)

    except Exception as ex:
        log.error('Unknown error from DEPATISconnect: %s %s.', type(ex), ex)
        log.error(exception_traceback())
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


@dpma_register_service.get(renderer='null')
def dpma_register_handler(request):

    type = request.matchdict['type']
    document = request.matchdict['document']
    format = request.params.get('format')
    language = request.params.get('lang', 'en')

    try:
        if type == 'patent':
            payload = dpmaregister.access_register(document, format, language)
        else:
            raise HTTPBadRequest('IP right type "{}" not implemented yet.'.format(type))

    except dpmaregister.NoResults as ex:
        raise HTTPNotFound(ex)

    except dpmaregister.UnknownFormat as ex:
        raise HTTPBadRequest(ex)

    except ValueError as ex:
        raise HTTPBadRequest(ex)

    if format == 'xml':
        request.response.content_type = 'application/xml'
    elif format.startswith('json'):
        request.response.content_type = 'application/json'
    elif format.startswith('html'):
        request.response.content_type = 'text/html'
    elif format == 'pdf':
        request.response.content_type = 'application/pdf'
    elif format == 'url':
        request.response.content_type = 'text/uri-list'

    return payload
