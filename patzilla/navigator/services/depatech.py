# -*- coding: utf-8 -*-
# (c) 2017-2018 Andreas Motl <andreas.motl@ip-tools.org>
#
# Cornice services for search provider "MTC depa.tech"
#
import logging
from cornice.service import Service
from pymongo.errors import OperationFailure
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest
from patzilla.access.depatech import get_depatech_client
from patzilla.access.depatech.client import depatech_search, LoginException, depatech_crawl
from patzilla.access.depatech.expression import DepaTechParser, should_be_quoted
from patzilla.navigator.services import handle_generic_exception
from patzilla.util.expression.keywords import keywords_to_response
from patzilla.navigator.services.util import request_to_options
from patzilla.access.generic.exceptions import NoResultsException, SearchException
from patzilla.util.data.container import SmartBunch
from patzilla.util.python import _exception_traceback

log = logging.getLogger(__name__)

depatech_published_data_search_service = Service(
    name='depatech-published-data-search',
    path='/api/depatech/published-data/search',
    description="MTC depa.tech search interface")
depatech_published_data_crawl_service = Service(
    name='depatech-published-data-crawl',
    path='/api/depatech/published-data/crawl{dummy1:\/?}{constituents:.*?}',
    description="MTC depa.tech crawler interface")

status_upstream_depatech = Service(
    name='status_depatech',
    path='/api/status/upstream/mtc/depatech',
    description="Checks MTC depa-tech upstream for valid response")


@status_upstream_depatech.get()
def status_upstream_depatech_handler(request):
    client = get_depatech_client()
    query = SmartBunch({
        'expression': '(PC:DE AND DE:212016000074 AND KI:U1) OR AN:DE212016000074U1 OR NP:DE212016000074U1',
    })
    data = client.search_real(query)
    assert data, 'Empty response from MTC depa.tech'
    return "OK"

# TODO: implement as JSON POST
@depatech_published_data_search_service.get(accept="application/json")
@depatech_published_data_search_service.post(accept="application/json")
def depatech_published_data_search_handler(request):
    """Search for published-data at MTC depa.tech"""

    # Get hold of query expression and filter
    expression = request.params.get('expression', '')
    filter = request.params.get('filter', '')
    query = SmartBunch({
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
        keywords_to_response(request, parser)

    # TODO: Parse DEPAROM query expression and extract keywords

    # Fixup query: wrap into quotes if cql string is a) unspecific, b) contains spaces and c) is still unquoted
    if should_be_quoted(query.expression):
        query.expression = '"%s"' % query.expression

    # Lazy-fetch more entries
    # TODO: get from patzilla.access.depatech
    limit = 250
    offset_local = int(request.params.get('range_begin', 0))
    offset_remote = int(offset_local / limit) * limit

    # Compute query options, like
    # - limit
    # - sorting
    # - whether to remove family members
    options = SmartBunch()
    options.update({
        'limit': limit,
        'offset': offset_remote,
    })

    # Propagate request parameters to search options parameters
    request_to_options(request, options)

    try:
        data = depatech_search(query, options)
        #print data.prettify()      # debugging
        return data

    except LoginException as ex:
        request.errors.add('depatech-search', 'login', ex.details)
        log.warn(request.errors)

    except SyntaxError as ex:
        request.errors.add('depatech-search', 'expression', unicode(ex.msg))
        log.warn(request.errors)

    except SearchException as ex:
        message = ex.get_message()
        request.errors.add('depatech-search', 'search', message)
        log.warn(request.errors)

    except NoResultsException as ex:
        # Forward response to let the frontend recognize zero hits
        request.response.status = HTTPNotFound.code
        return ex.data

    except OperationFailure as ex:
        message = unicode(ex)
        request.errors.add('depatech-search', 'internals', message)
        log.error(request.errors)

    except Exception as ex:
        message = handle_generic_exception(request, ex, 'depatech-search', query)
        request.errors.add('depatech-search', 'search', message)

@depatech_published_data_crawl_service.get(accept="application/json")
@depatech_published_data_crawl_service.post(accept="application/json")
def depatech_published_data_crawl_handler(request):
    """Crawl published-data at MTC depa.tech"""

    # Get hold of query expression and filter
    query = SmartBunch({
        'expression': request.params.get('expression', ''),
        'filter':     request.params.get('filter', ''),
        })
    log.info('query: {}'.format(query))

    if should_be_quoted(query.expression):
        query.expression = '"%s"' % query.expression

    # constituents: abstract, biblio and/or full-cycle
    constituents = request.matchdict.get('constituents', 'full-cycle')
    #print 'constituents:', constituents

    chunksize = int(request.params.get('chunksize', '5000'))

    try:
        result = depatech_crawl(constituents, query, chunksize)
        return result

    except Exception as ex:
        request.errors.add('depatech-crawl', 'crawl', unicode(ex))
        log.error(request.errors)
        log.error(u'query="{0}", exception:\n{1}'.format(query, _exception_traceback()))
