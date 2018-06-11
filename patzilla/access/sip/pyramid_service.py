# -*- coding: utf-8 -*-
# (c) 2013-2018 Andreas Motl <andreas.motl@ip-tools.org>
import re
import logging
from pprint import pprint

from cornice.service import Service
from pymongo.errors import OperationFailure
from pyramid.httpexceptions import HTTPNotFound
from patzilla.navigator.services.util import request_to_options
from patzilla.access.generic.exceptions import NoResultsException
from patzilla.access.sip.client import sip_published_data_search, sip_published_data_crawl, SearchException
from patzilla.access.sip.client import LoginException
from patzilla.util.cql.util import should_be_quoted
from patzilla.util.data.container import SmartBunch
from patzilla.util.python import _exception_traceback

log = logging.getLogger(__name__)

sip_published_data_search_service = Service(
    name='sip-published-data-search',
    path='/api/sip/published-data/search',
    description="SIP search interface")
sip_published_data_crawl_service = Service(
    name='sip-published-data-crawl',
    path='/api/sip/published-data/crawl{dummy1:\/?}{constituents:.*?}',
    description="SIP crawler interface")



# TODO: implement as JSON POST
@sip_published_data_search_service.get(accept="application/json")
@sip_published_data_search_service.post(accept="application/json")
def sip_published_data_search_handler(request):
    """Search for published-data at SIP"""

    #request.errors.add('sip-search', 'login', "SIP data source disabled, please use alternative data source.")
    #return

    # XML query expression
    query = request.params.get('expression', '')
    log.info('Raw query: ' + query)

    # fixup query: wrap into quotes if cql string is a) unspecific, b) contains spaces and c) is still unquoted
    if should_be_quoted(query):
        query = '"%s"' % query

    #propagate_keywords(request, query_object)

    # lazy-fetch more entries up to maximum of SIP
    # TODO: get from patzilla.access.sip
    limit = 250
    offset_local = int(request.params.get('range_begin', 1))
    offset_remote = int(offset_local / limit) * limit

    # Compute query options, like
    # - limit
    # - sorting
    # - whether to remove family members
    # - whether to return all family members
    options = SmartBunch()
    options.update({
        'limit':  limit,
        'offset': offset_remote,
    })

    # Propagate request parameters to search options parameters
    request_to_options(request, options)

    # currently not handled by search handler, it's already handled on xml expression builder level
    #if asbool(request.params.get('query_data[modifiers][family-full]')):
    #    options.update({'feature_family_full': True})

    try:
        data = sip_published_data_search(query, options)
        #print ' SIPsearch response:'; print data.prettify()      # debugging
        return data

    except LoginException as ex:
        request.errors.add('sip-search', 'login', ex.sip_info)

    except SyntaxError as ex:
        request.errors.add('sip-search', 'expression', str(ex.msg))
        log.warn(request.errors)

    except SearchException as ex:
        message = ex.get_message()
        request.errors.add('sip-search', 'search', message)
        log.error(request.errors)

    except NoResultsException as ex:
        # Forward response to let the frontend recognize zero hits
        request.response.status = HTTPNotFound.code
        return ex.data

    except OperationFailure as ex:
        message = unicode(ex)
        message = re.sub(u'namespace: .*', u'', message)
        request.errors.add('sip-search', 'internals', message)
        log.error(request.errors)


@sip_published_data_crawl_service.get(accept="application/json")
@sip_published_data_crawl_service.post(accept="application/json")
def sip_published_data_crawl_handler(request):
    """Crawl published-data at SIP"""

    # XML query expression
    query = request.params.get('expression', '')
    log.info('query raw: ' + query)

    if should_be_quoted(query):
        query = '"%s"' % query

    # constituents: abstract, biblio and/or full-cycle
    constituents = request.matchdict.get('constituents', 'full-cycle')
    #print 'constituents:', constituents

    chunksize = int(request.params.get('chunksize', '2500'))

    try:
        result = sip_published_data_crawl(constituents, query, chunksize)
        return result

    except Exception as ex:
        if hasattr(ex, 'user_info'):
            message = ex.user_info
        else:
            message = unicode(ex)
        request.errors.add('sip-crawl', 'crawl', message)
        log.error(request.errors)
        log.error(u'query="{0}", exception:\n{1}'.format(query, _exception_traceback()))
