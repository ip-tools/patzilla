# -*- coding: utf-8 -*-
# (c) 2017-2018 Andreas Motl <andreas.motl@ip-tools.org>
#
# HTTP API for search provider "MTC depa.tech"
#
import logging

from fastapi import APIRouter, Response
from pymongo.errors import OperationFailure
from patzilla.access.depatech.client import depatech_search, LoginException, depatech_crawl
from patzilla.access.depatech.expression import DepaTechParser, should_be_quoted
from patzilla.navigator.services import handle_generic_exception
from patzilla.util.expression.keywords import keywords_to_response
from patzilla.navigator.services.util import request_to_options
from patzilla.access.generic.exceptions import NoResultsException, SearchException, ServiceError
from patzilla.util.data.container import SmartMunch
from patzilla.util.python import _exception_traceback
from patzilla.web.dependencies import DepaTechClient, Params

log = logging.getLogger(__name__)

router = APIRouter(tags=["depatech"])


@router.get("/api/status/upstream/mtc/depatech", name="status_depatech",
            summary="Checks MTC depa-tech upstream for valid response")
def status_upstream_depatech_handler(client: DepaTechClient):
    query = SmartMunch({
        'expression': '(PC:DE AND DE:212016000074 AND KI:U1) OR AN:DE212016000074U1 OR NP:DE212016000074U1',
    })
    data = client.search_real(query)
    assert data, 'Empty response from MTC depa.tech'
    return "OK"


# TODO: implement as JSON POST
@router.api_route("/api/depatech/published-data/search", methods=["GET", "POST"],
                  name="depatech-published-data-search", summary="MTC depa.tech search interface")
def depatech_published_data_search_handler(response: Response, client: DepaTechClient, params: Params):
    """Search for published-data at MTC depa.tech"""

    # Get hold of query expression and filter
    expression = params.get('expression', '')
    filter = params.get('filter', '')
    query = SmartMunch({
        'syntax':     'lucene',
        'expression': expression,
        'filter':     filter,
    })
    if expression.startswith('DEPAROM V1.0') or expression.startswith('deparom:'):
        query.syntax = 'deparom'

    log.info('Query: {}'.format(query))

    # Parse expression, extract and propagate keywords to user interface
    if query.syntax == 'lucene':
        parser = DepaTechParser(query.expression)
        keywords_to_response(response, parser)

    # TODO: Parse DEPAROM query expression and extract keywords

    # Fixup query: wrap into quotes if cql string is a) unspecific, b) contains spaces and c) is still unquoted
    if should_be_quoted(query.expression):
        query.expression = '"%s"' % query.expression

    # Lazy-fetch more entries
    # TODO: get from patzilla.access.depatech
    limit = 250
    offset_local = int(params.get('range_begin', 0))
    offset_remote = int(offset_local / limit) * limit

    # Compute query options, like
    # - limit
    # - sorting
    # - whether to remove family members
    options = SmartMunch()
    options.update({
        'limit': limit,
        'offset': offset_remote,
    })

    # Propagate request parameters to search options parameters
    request_to_options(params, options)

    try:
        data = depatech_search(client, query, options)
        #print data.prettify()      # debugging
        return data

    except LoginException as ex:
        error = ServiceError('depatech-search', 'login', ex.get_message())
        log.warning(error.errors)
        raise error

    except SyntaxError as ex:
        error = ServiceError('depatech-search', 'expression', str(ex.msg))
        log.warning(error.errors)
        raise error

    except SearchException as ex:
        message = ex.get_message()
        error = ServiceError('depatech-search', 'search', message)
        log.warning(error.errors)
        raise error

    except NoResultsException as ex:
        # Forward response to let the frontend recognize zero hits
        response.status_code = 404
        return ex.data

    except OperationFailure as ex:
        message = str(ex)
        error = ServiceError('depatech-search', 'internals', message)
        log.error(error.errors)
        raise error

    except Exception as ex:
        message = handle_generic_exception(ex, 'depatech-search', query)
        raise ServiceError('depatech-search', 'search', message)


@router.api_route("/api/depatech/published-data/crawl", methods=["GET", "POST"],
                  name="depatech-published-data-crawl", summary="MTC depa.tech crawler interface")
@router.api_route("/api/depatech/published-data/crawl/{constituents:path}", methods=["GET", "POST"],
                  name="depatech-published-data-crawl")
def depatech_published_data_crawl_handler(client: DepaTechClient, params: Params, constituents: str = 'full-cycle'):
    """Crawl published-data at MTC depa.tech"""

    # Get hold of query expression and filter
    query = SmartMunch({
        'expression': params.get('expression', ''),
        'filter':     params.get('filter', ''),
        })
    log.info('query: {}'.format(query))

    if should_be_quoted(query.expression):
        query.expression = '"%s"' % query.expression

    # constituents: abstract, biblio and/or full-cycle
    #print 'constituents:', constituents

    chunksize = int(params.get('chunksize', '5000'))

    try:
        result = depatech_crawl(client, constituents, query, chunksize)
        return result

    except Exception as ex:
        error = ServiceError('depatech-crawl', 'crawl', str(ex))
        log.error(error.errors)
        log.error('query="{0}", exception:\n{1}'.format(query, _exception_traceback()))
        raise error
