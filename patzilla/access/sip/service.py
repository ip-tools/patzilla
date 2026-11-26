# -*- coding: utf-8 -*-
# (c) 2013-2018 Andreas Motl <andreas.motl@ip-tools.org>
import re
import logging

from fastapi import APIRouter, Response
from pymongo.errors import OperationFailure
from patzilla.navigator.services.util import request_to_options
from patzilla.access.generic.exceptions import NoResultsException, ServiceError
from patzilla.access.sip.client import sip_published_data_search, sip_published_data_crawl, SearchException
from patzilla.access.sip.client import LoginException
from patzilla.util.cql.util import should_be_quoted
from patzilla.util.data.container import SmartMunch
from patzilla.util.python import _exception_traceback
from patzilla.web.dependencies import Params, SipClient

log = logging.getLogger(__name__)

router = APIRouter(tags=["sip"])


# TODO: implement as JSON POST
@router.api_route("/api/sip/published-data/search", methods=["GET", "POST"],
                  name="sip-published-data-search", summary="SIP search interface")
def sip_published_data_search_handler(response: Response, sip: SipClient, params: Params):
    """Search for published-data at SIP"""

    #raise ServiceError('sip-search', 'login', "SIP data source disabled, please use alternative data source.")

    # XML query expression
    query = params.get('expression', '')
    log.info('Raw query: ' + query)

    # fixup query: wrap into quotes if cql string is a) unspecific, b) contains spaces and c) is still unquoted
    if should_be_quoted(query):
        query = '"%s"' % query

    #propagate_keywords(request, query_object)

    # lazy-fetch more entries up to maximum of SIP
    # TODO: get from patzilla.access.sip
    limit = 250
    offset_local = int(params.get('range_begin', 1))
    offset_remote = int(offset_local / limit) * limit

    # Compute query options, like
    # - limit
    # - sorting
    # - whether to remove family members
    # - whether to return all family members
    options = SmartMunch()
    options.update({
        'limit':  limit,
        'offset': offset_remote,
    })

    # Propagate request parameters to search options parameters
    request_to_options(params, options)

    # currently not handled by search handler, it's already handled on xml expression builder level
    #if asbool(params.get('query_data[modifiers][family-full]')):
    #    options.update({'feature_family_full': True})

    try:
        data = sip_published_data_search(sip, query, options)
        #print ' SIPsearch response:'; print data.prettify()      # debugging
        return data

    except LoginException as ex:
        raise ServiceError('sip-search', 'login', ex.sip_info)

    except SyntaxError as ex:
        error = ServiceError('sip-search', 'expression', str(ex.msg))
        log.warning(error.errors)
        raise error

    except SearchException as ex:
        message = ex.get_message()
        error = ServiceError('sip-search', 'search', message)
        log.error(error.errors)
        raise error

    except NoResultsException as ex:
        # Forward response to let the frontend recognize zero hits
        response.status_code = 404
        return ex.data

    except OperationFailure as ex:
        message = str(ex)
        message = re.sub('namespace: .*', '', message)
        error = ServiceError('sip-search', 'internals', message)
        log.error(error.errors)
        raise error


@router.api_route("/api/sip/published-data/crawl", methods=["GET", "POST"],
                  name="sip-published-data-crawl", summary="SIP crawler interface")
@router.api_route("/api/sip/published-data/crawl/{constituents:path}", methods=["GET", "POST"],
                  name="sip-published-data-crawl")
def sip_published_data_crawl_handler(sip: SipClient, params: Params, constituents: str = 'full-cycle'):
    """Crawl published-data at SIP"""

    # XML query expression
    query = params.get('expression', '')
    log.info('query raw: ' + query)

    if should_be_quoted(query):
        query = '"%s"' % query

    # constituents: abstract, biblio and/or full-cycle
    #print 'constituents:', constituents

    chunksize = int(params.get('chunksize', '2500'))

    try:
        result = sip_published_data_crawl(sip, constituents, query, chunksize)
        return result

    except Exception as ex:
        if hasattr(ex, 'user_info'):
            message = ex.user_info
        else:
            message = str(ex)
        error = ServiceError('sip-crawl', 'crawl', message)
        log.error(error.errors)
        log.error('query="{0}", exception:\n{1}'.format(query, _exception_traceback()))
        raise error
