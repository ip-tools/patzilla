# -*- coding: utf-8 -*-
# (c) 2013-2016 Andreas Motl, Elmyra UG
import logging
from pprint import pprint
from cornice.service import Service
from pyramid.settings import asbool
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest
from beaker.cache import cache_region, region_invalidate
from elmyra.ip.access.generic.exceptions import NoResultsException
from elmyra.ip.util.python import _exception_traceback
from elmyra.ip.access.dpma.depatisconnect import depatisconnect_claims, depatisconnect_abstracts, depatisconnect_description
from elmyra.ip.access.dpma.depatisnet import DpmaDepatisnetAccess
from elmyra.ip.access.epo.espacenet import espacenet_claims, espacenet_description
from elmyra.ip.access.epo.services import cql_prepare_query, propagate_keywords
from elmyra.ip.access.epo.services.util import request_to_options

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


# TODO: implement as JSON POST
@depatisnet_published_data_search_service.get(accept="application/json")
@depatisnet_published_data_search_service.post(accept="application/json")
def depatisnet_published_data_search_handler(request):
    """Search for published-data at DEPATISnet"""

    #pprint(request.params)

    # CQL query string
    query = request.params.get('query', '')
    log.info('query raw: ' + query)

    # lazy-fetch more entries up to maximum of depatisnet
    # TODO: get from elmyra.ip.access.dpma.depatisnet
    request_size = 250
    if int(request.params.get('range_begin', 0)) > request_size:
        request_size = 1000

    # Compute query options, like
    # - limit
    # - sorting
    # - whether to remove family members
    options = {}
    options.update({'limit': request_size})

    # propagate request parameters to search options parameters
    request_to_options(request, options)

    # transcode CQL query
    query_object, query = cql_prepare_query(query)
    log.info('query cql: ' + query)

    # propagate keywords to highlighting component
    propagate_keywords(request, query_object)

    # invalidate cache
    invalidate = asbool(request.params.get('invalidate', 'false'))
    if invalidate:
        dpma_published_data_search_invalidate(query, options)

    try:
        return dpma_published_data_search(query, options)

    except SyntaxError as ex:
        request.errors.add('depatisnet-search', 'expression', str(ex.msg))
        log.warn(request.errors)

    except NoResultsException as ex:
        # Forward response to let the frontend recognize zero hits
        request.response.status = HTTPNotFound.code
        return ex.data

    except Exception as ex:
        http_response = None
        if hasattr(ex, 'http_response'):
            http_response = ex.http_response
        reason = u'{}: {}'.format(ex.__class__.__name__, ex.message)
        log.error(u'DEPATISnet search error: query="{0}", reason={1}\nresponse:\n{2}\nexception:\n{3}'.format(
            query, reason, http_response, _exception_traceback()))

        message = u'An exception occurred while processing your query<br/>Reason: {}'.format(reason)
        request.errors.add('depatisnet-search', 'search', message)


@depatisnet_published_data_crawl_service.get(accept="application/json")
@depatisnet_published_data_crawl_service.post(accept="application/json")
def depatisnet_published_data_crawl_handler(request):
    """Crawl published-data at DEPATISnet"""

    # CQL query string
    query = request.params.get('query', '')
    log.info('query raw: ' + query)

    query_object, query = cql_prepare_query(query)
    propagate_keywords(request, query_object)

    chunksize = 1000

    # Compute query options, like
    # - limit
    # - sorting
    # - whether to remove family members
    options = {}
    options.update({'limit': chunksize})

    # propagate request parameters to search options parameters
    request_to_options(request, options)

    log.info('query cql: ' + query)
    try:
        result = dpma_published_data_search(query, options)
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
    options = options or {}
    depatisnet = DpmaDepatisnetAccess()
    data = depatisnet.search_patents(query, options)
    #print data.prettify()      # debugging

    # Raise an exception on empty results to skip caching this response
    if data.meta.navigator.count_total == 0:
        raise NoResultsException('No results', data=data)

    return data

def dpma_published_data_search_invalidate(*args):
    region_invalidate(dpma_published_data_search, None, 'dpma_search', *args)

@depatisconnect_claims_service.get()
def depatisconnect_claims_handler(request):
    # TODO: use jsonified error responses
    patent = request.matchdict['patent']
    invalidate = asbool(request.params.get('invalidate', 'false'))
    try:
        return depatisconnect_claims_handler_real(patent, invalidate)
    except:
        return espacenet_claims_handler_real(patent)

def depatisconnect_claims_handler_real(patent, invalidate=False):
    try:
        claims = depatisconnect_claims(patent, invalidate)

    except KeyError as ex:
        log.error('No details at DEPATISconnect: %s %s', type(ex), ex)
        raise HTTPNotFound(ex)

    except ValueError as ex:
        log.error('Fetching details from DEPATISconnect failed: %s %s', type(ex), ex)
        raise HTTPBadRequest(ex)

    return claims

def espacenet_claims_handler_real(patent):
    try:
        claims = espacenet_claims(patent)

    except KeyError as ex:
        log.error('No details at Espacenet: %s %s', type(ex), ex)
        raise HTTPNotFound(ex)

    except ValueError as ex:
        log.error('Fetching details from Espacenet failed: %s %s', type(ex), ex)
        raise HTTPBadRequest(ex)

    return claims

def espacenet_description_handler_real(patent):
    try:
        description = espacenet_description(patent)

    except KeyError as ex:
        log.error('No details at Espacenet: %s %s', type(ex), ex)
        raise HTTPNotFound(ex)

    except ValueError as ex:
        log.error('Fetching details from Espacenet failed: %s %s', type(ex), ex)
        raise HTTPBadRequest(ex)

    return description

@depatisconnect_description_service.get()
def depatisconnect_description_handler(request):
    # TODO: use jsonified error responses
    patent = request.matchdict['patent']
    try:
        return depatisconnect_description_handler_real(patent)
    except:
        return espacenet_description_handler_real(patent)

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

    return description


@depatisconnect_abstract_service.get()
def depatisconnect_abstract_handler(request):
    # TODO: use jsonified error responses
    patent = request.matchdict['patent']
    language = request.params.get('language')
    invalidate = asbool(request.params.get('invalidate', 'false'))
    try:
        abstract = depatisconnect_abstracts(patent, language, invalidate)

    except KeyError as ex:
        log.error('Problem fetching details of DEPATISconnect: %s %s', type(ex), ex)
        raise HTTPNotFound(ex)

    except ValueError as ex:
        log.error('Problem fetching details of DEPATISconnect: %s %s', type(ex), ex)
        raise HTTPBadRequest(ex)

    return abstract
