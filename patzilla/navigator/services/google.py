# -*- coding: utf-8 -*-
# (c) 2013-2015 Andreas Motl, Elmyra UG
import logging
from beaker.cache import cache_region
from cornice.service import Service
from patzilla.access.google.search import GooglePatentsAccess

log = logging.getLogger(__name__)

google_published_data_search_service = Service(
    name='google-published-data-search',
    path='/api/google/published-data/search',
    description="Google Patents search interface")

@cache_region('search')
def google_published_data_search(query, offset, limit):
    google = GooglePatentsAccess()
    try:
        return google.search(query, offset, limit)
    except SyntaxError as ex:
        log.warn('Invalid query for Google Patents: %s' % ex.msg)
        raise

@google_published_data_search_service.get(accept="application/json")
def google_published_data_search_handler(request):
    """Search for published-data at Google Patents"""

    # CQL query string
    query = request.params.get('query', '')
    log.info('query raw: ' + query)

    #propagate_keywords(request, query_object)

    # lazy-fetch more entries up to maximum
    # TODO: get from patzilla.access.google
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

