# -*- coding: utf-8 -*-
# (c) 2013-2018 Andreas Motl <andreas.motl@ip-tools.org>
import logging

from beaker.cache import cache_region
from fastapi import APIRouter, HTTPException, Response
from patzilla.access.dpma import dpmaregister
from patzilla.access.generic.exceptions import NoResultsException, ServiceError
from patzilla.util.config import asbool
from patzilla.util.expression.keywords import keywords_to_response
from patzilla.util.python import _exception_traceback, exception_traceback
from patzilla.access.dpma.depatisconnect import depatisconnect_claims, depatisconnect_abstracts, depatisconnect_description
from patzilla.access.dpma.depatisnet import DpmaDepatisnetAccess
from patzilla.access.epo.espacenet.service import espacenet_claims_handler, espacenet_description_handler
from patzilla.navigator.services import cql_prepare_query, handle_generic_exception, ikofax_prepare_query
from patzilla.navigator.services.util import request_to_options
from patzilla.web.dependencies import Params

log = logging.getLogger(__name__)

router = APIRouter(tags=["dpma"])


@router.get("/api/status/upstream/dpma/depatisnet", name="status_depatisnet",
            summary="Checks DPMA depatisnet upstream for valid response")
def status_upstream_depatisnet_handler():
    data = dpma_published_data_search_real('pn=EP666666', None)
    assert data, 'Empty response from depatisnet'
    return "OK"

@router.get("/api/status/upstream/dpma/depatisconnect", name="status_depatisconnect",
            summary="Checks DPMA depatisconnect upstream for valid response")
def status_upstream_depatisconnect_handler():
    data = depatisconnect_claims_handler_real('DE212016000074U1')
    assert data['xml'], 'Empty response from depatisconnect'
    return "OK"

@router.get("/api/status/upstream/dpma/dpmaregister", name="status_dpmaregister",
            summary="Checks DPMA dpmaregister upstream for valid response")
def status_upstream_dpmaregister_handler():
    data = dpmaregister.access_register('DE212016000074', 'json')
    assert data, 'Empty response from dpmaregister'
    return "OK"


def prepare_search(params, response):

    # CQL expression string
    expression = params.get('expression', '').strip()

    # Compute expression syntax
    syntax_cql = asbool(params.get('query_data[modifiers][syntax-cql]'))
    syntax_ikofax = asbool(params.get('query_data[modifiers][syntax-ikofax]'))
    syntax = 'cql'
    if syntax_ikofax or expression.startswith('ikofax:'):
        expression = expression.replace('ikofax:', '')
        syntax = 'ikofax'

    log.info('DEPATISnet query: {}, syntax: {}'.format(expression, syntax))

    # Compute query options, like
    # - limit
    # - sorting
    # - whether to remove family members
    options = {}
    options.update({'syntax': syntax})

    # propagate request parameters to search options parameters
    request_to_options(params, options)

    # Transcode query expression
    if syntax == 'cql':
        search = cql_prepare_query(expression)
    elif syntax == 'ikofax':
        search = ikofax_prepare_query(expression)
    else:
        raise ServiceError('depatisnet-search', 'expression', 'Unknown syntax {}'.format(syntax))

    # Propagate keywords to highlighting component
    keywords_to_response(response, search=search)

    return search, options


# TODO: implement as JSON POST
@router.api_route("/api/depatisnet/published-data/search", methods=["GET", "POST"],
                  name="depatisnet-published-data-search", summary="DEPATISnet search interface")
def depatisnet_published_data_search_handler(params: Params, response: Response):
    """Search for published-data at DEPATISnet"""

    search, options = prepare_search(params, response)

    # Run query through upstream database
    try:
        return dpma_published_data_search(search.expression, options)

    except SyntaxError as ex:
        log.warning('depatisnet-search: Invalid expression: %s', ex.msg)
        raise ServiceError('depatisnet-search', 'expression', str(ex.msg))

    except NoResultsException as ex:
        # Forward response to let the frontend recognize zero hits
        response.status_code = 404
        return ex.data

    except Exception as ex:
        message = handle_generic_exception(ex, 'depatisnet-search', search.expression)
        raise ServiceError('depatisnet-search', 'search', message)


@router.api_route("/api/depatisnet/published-data/crawl", methods=["GET", "POST"],
                  name="depatisnet-published-data-crawl", summary="DEPATISnet crawler interface")
@router.api_route("/api/depatisnet/published-data/crawl/{constituents:path}", methods=["GET", "POST"],
                  name="depatisnet-published-data-crawl")
def depatisnet_published_data_crawl_handler(params: Params, response: Response):
    """Crawl published-data at DEPATISnet"""

    search, options = prepare_search(params, response)

    try:
        result = dpma_published_data_search(search.expression, options)
        return result

    except SyntaxError as ex:
        log.warning('depatisnet-search: Invalid expression: %s', ex.msg)
        raise ServiceError('depatisnet-search', 'expression', str(ex.msg))

    except Exception as ex:
        http_response = None
        if hasattr(ex, 'http_response'):
            http_response = ex.http_response
        log.error('DEPATISnet crawler error: query="{0}", reason={1}\nresponse:\n{2}\nexception:\n{3}'.format(
            search.expression, ex, http_response, _exception_traceback()))

        message = 'An exception occurred while processing your query<br/>Reason: {}'.format(ex)
        raise ServiceError('depatisnet-search', 'crawl', message)


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

@router.get("/api/depatisconnect/{patent}/claims", name="depatisconnect-claims",
            summary="DEPATISconnect claims interface")
def depatisconnect_claims_handler(patent: str):
    # TODO: use jsonified error responses
    # return depatisconnect_claims_handler_real(patent)
    try:
        return espacenet_claims_handler(patent)
    except:
        log.exception("Fetching claims from Espacenet failed for document: {}".format(patent))
        raise

def depatisconnect_claims_handler_real(patent):
    try:
        claims = depatisconnect_claims(patent)

    except KeyError as ex:
        log.error('No details at DEPATISconnect: %s %s', type(ex), ex)
        raise HTTPException(404, str(ex))

    except ValueError as ex:
        log.error('Fetching details from DEPATISconnect failed: %s %s', type(ex), ex)
        raise HTTPException(400, str(ex))

    except Exception as ex:
        log.error('Unknown error from DEPATISconnect: %s %s.', type(ex), ex)
        log.error(exception_traceback())
        raise HTTPException(400, str(ex))

    return claims

@router.get("/api/depatisconnect/{patent}/description", name="depatisconnect-description",
            summary="DEPATISconnect description interface")
def depatisconnect_description_handler(patent: str):
    # TODO: use jsonified error responses
    # return depatisconnect_description_handler_real(patent)
    try:
        return espacenet_description_handler(patent)
    except:
        log.exception("Fetching description from Espacenet failed for document: {}".format(patent))
        raise

def depatisconnect_description_handler_real(patent):
    try:
        description = depatisconnect_description(patent)
        if not description['xml']:
            raise KeyError('Description is empty')

    except KeyError as ex:
        log.error('No details at DEPATISconnect: %s %s', type(ex), ex)
        raise HTTPException(404, str(ex))

    except ValueError as ex:
        log.error('Fetching details from DEPATISconnect failed: %s %s', type(ex), ex)
        raise HTTPException(400, str(ex))

    except Exception as ex:
        log.error('Unknown error from DEPATISconnect: %s %s.', type(ex), ex)
        log.error(exception_traceback())
        raise HTTPException(400, str(ex))

    return description


@router.get("/api/depatisconnect/{patent}/abstract", name="depatisconnect-abstract",
            summary="DEPATISconnect abstract interface")
def depatisconnect_abstract_handler(patent: str, language: str = None):
    # TODO: use jsonified error responses
    try:
        abstract = depatisconnect_abstracts(patent, language)

    except KeyError as ex:
        log.error('Problem fetching details of DEPATISconnect: %s %s', type(ex), ex)
        raise HTTPException(404, str(ex))

    except ValueError as ex:
        log.error('Problem fetching details of DEPATISconnect: %s %s', type(ex), ex)
        raise HTTPException(400, str(ex))

    return abstract


@router.get("/api/dpma/register/{type}/{document}", name="dpma-register", summary="DPMAregister interface")
def dpma_register_handler(type: str, document: str, format: str = None, lang: str = 'en'):

    language = lang

    try:
        if type == 'patent':
            payload = dpmaregister.access_register(document, format, language)
        else:
            raise HTTPException(400, 'IP right type "{}" not implemented yet.'.format(type))

    except dpmaregister.NoResults as ex:
        raise HTTPException(404, str(ex))

    except dpmaregister.UnknownFormat as ex:
        raise HTTPException(400, str(ex))

    except ValueError as ex:
        raise HTTPException(400, str(ex))

    media_type = None
    if format == 'xml':
        media_type = 'application/xml'
    elif format.startswith('json'):
        media_type = 'application/json'
    elif format.startswith('html'):
        media_type = 'text/html'
    elif format == 'pdf':
        media_type = 'application/pdf'
    elif format == 'url':
        media_type = 'text/uri-list'

    return Response(payload, media_type=media_type)
