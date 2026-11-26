# -*- coding: utf-8 -*-
# (c) 2013-2015 Andreas Motl, Elmyra UG
import logging
from beaker.cache import cache_region
from fastapi import APIRouter
from patzilla.access.generic.exceptions import ServiceError
from patzilla.access.google.search import GooglePatentsAccess

log = logging.getLogger(__name__)

router = APIRouter(tags=["google"])


@cache_region('search')
def google_published_data_search(query, offset, limit):
    google = GooglePatentsAccess()
    try:
        return google.search(query, offset, limit)
    except SyntaxError as ex:
        log.warning('Invalid query for Google Patents: %s' % ex.msg)
        raise


@router.get("/api/google/published-data/search", name="google-published-data-search",
            summary="Google Patents search interface")
def google_published_data_search_handler(query: str = '', range_begin: int = 1):
    """Search for published-data at Google Patents"""

    # CQL query string
    log.info('query raw: ' + query)

    #propagate_keywords(request, query_object)

    # lazy-fetch more entries up to maximum
    # TODO: get from patzilla.access.google
    limit = 100
    offset_local = range_begin
    offset_remote = int(offset_local / limit) * limit

    try:
        data = google_published_data_search(query, offset_remote, limit)
        return data

    except SyntaxError as ex:
        raise ServiceError('google-search', 'query', str(ex.msg))

    except ValueError as ex:
        raise ServiceError('google-search', 'query', str(ex))
