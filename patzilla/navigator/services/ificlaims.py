# -*- coding: utf-8 -*-
# (c) 2015-2018 Andreas Motl <andreas.motl@ip-tools.org>
#
# Cornice services for search provider "IFI CLAIMS Direct"
#
import re
import json
import time
import logging
from cornice.service import Service
from pyramid.settings import asbool
from pymongo.errors import OperationFailure
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest
from patzilla.navigator.services import handle_generic_exception
from patzilla.util.expression.keywords import keywords_to_response
from patzilla.navigator.services.util import request_to_options
from patzilla.access.generic.exceptions import NoResultsException, SearchException
from patzilla.access.ificlaims.api import ificlaims_download, ificlaims_download_multi
from patzilla.access.ificlaims.client import IFIClaimsException, IFIClaimsFormatException, LoginException, ificlaims_search, ificlaims_crawl, ificlaims_client
from patzilla.access.ificlaims.expression import should_be_quoted, IFIClaimsParser
from patzilla.util.data.container import SmartBunch
from patzilla.util.data.zip import zip_multi
from patzilla.util.python import _exception_traceback

log = logging.getLogger(__name__)

ificlaims_published_data_search_service = Service(
    name='ificlaims-published-data-search',
    path='/api/ificlaims/published-data/search',
    description="IFI CLAIMS search interface")
ificlaims_published_data_crawl_service = Service(
    name='ificlaims-published-data-crawl',
    path='/api/ificlaims/published-data/crawl{dummy1:\/?}{constituents:.*?}',
    description="IFI CLAIMS crawler interface")

ificlaims_download_service = Service(
    name='ificlaims-download',
    path='/api/ificlaims/download/{resource}.{format}',
    description="IFI CLAIMS download interface")
ificlaims_deliver_service = Service(
    name='ificlaims-deliver',
    path='/api/ificlaims/deliver/{kind}',
    description="IFI CLAIMS deliver interface")

status_upstream_ificlaims = Service(
    name='status_ificlaims',
    path='/api/status/upstream/ificlaims/direct',
    description="Checks IFI CLAIMS upstream for valid response")


@status_upstream_ificlaims.get()
def status_upstream_ificlaims_handler(request):
    client = ificlaims_client()
    query = SmartBunch({
        'expression': 'pn:EP0666666',
    })
    data = client.search_real(query)
    assert data, 'Empty response from IFI CLAIMS'
    return "OK"

@ificlaims_download_service.get(renderer='null')
def ificlaims_download_handler(request):
    """Download resources from IFI CLAIMS Direct"""

    resource = request.matchdict['resource']
    format   = request.matchdict['format'].lower()
    pretty   = asbool(request.params.get('pretty'))
    seq      = int(request.params.get('seq', 1))
    options = {'pretty': pretty, 'seq': seq}

    try:
        response = ificlaims_download(resource, format, options)

    except IFIClaimsException, ex:
        if type(ex) is IFIClaimsFormatException:
            raise HTTPNotFound(ex)
        else:
            raise HTTPBadRequest(ex)


    if response.payload:

        request.response.content_type = response.mimetype

        # http://tools.ietf.org/html/rfc6266#section-4.2
        disposition = response.disposition_inline and 'inline' or 'attachment'

        content_disposition = '{disposition}; filename={filename}'.format(disposition=disposition, filename=response.filename)
        request.response.headers['Content-Disposition'] = content_disposition
        request.response.headers['Data-Source'] = 'ifi'

        return response.payload

    else:
        msg = "Resource '%s' with format='%s' not found" % (resource, format)
        log.warning(msg)
        raise HTTPNotFound(msg)


@ificlaims_deliver_service.get(renderer='null')
def ificlaims_deliver_handler(request):
    """Deliver resources from IFI CLAIMS Direct in bulk"""

    kind = request.matchdict['kind']
    formats = map(unicode.strip, request.params.get('formats', u'').lower().split(u','))
    numberlist = filter(lambda item: bool(item), map(unicode.strip, re.split('[\n,]', request.params.get('numberlist', u''))))

    if kind == 'zip':
        multi = ificlaims_download_multi(numberlist, formats)

        #for entry in multi['results']:
        #    print 'entry:', entry
        print 'report:'
        print json.dumps(multi['report'], indent=4)

        payload = zip_multi(multi)

        disposition = 'attachment'
        zipname = time.strftime('ificlaims-delivery_%Y%m%d-%H%M%S.zip')

        content_disposition = '{disposition}; filename={filename}'.format(disposition=disposition, filename=zipname)
        request.response.content_type = 'application/zip'
        request.response.headers['Content-Disposition'] = content_disposition
        request.response.headers['Data-Source'] = 'ifi'

        return payload
    else:
        raise HTTPBadRequest("Unknown delivery kind '{kind}'".format(**locals()))





# TODO: implement as JSON POST
@ificlaims_published_data_search_service.get(accept="application/json")
@ificlaims_published_data_search_service.post(accept="application/json")
def ificlaims_published_data_search_handler(request):
    """Search for published-data at IFI CLAIMS Direct"""

    # Get hold of query expression and filter
    query = SmartBunch({
        'expression': request.params.get('expression', ''),
        'filter':     request.params.get('filter', ''),
    })
    log.info('Query: {}'.format(query))

    # Parse expression, extract and propagate keywords to user interface
    parser = IFIClaimsParser(query.expression)
    keywords_to_response(request, parser)

    # Fixup query: wrap into quotes if cql string is a) unspecific, b) contains spaces and c) is still unquoted
    if should_be_quoted(query.expression):
        query.expression = '"%s"' % query.expression

    # Lazy-fetch more entries
    # TODO: get from patzilla.access.ificlaims
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
        data = ificlaims_search(query, options)
        #print data.prettify()      # debugging
        return data

    except LoginException as ex:
        request.errors.add('ificlaims-search', 'login', ex.details)
        log.warn(request.errors)

    except SyntaxError as ex:
        request.errors.add('ificlaims-search', 'expression', unicode(ex.msg))
        log.warn(request.errors)

    except SearchException as ex:
        message = ex.get_message()
        request.errors.add('ificlaims-search', 'search', message)
        log.warn(request.errors)

    except NoResultsException as ex:
        # Forward response to let the frontend recognize zero hits
        request.response.status = HTTPNotFound.code
        return ex.data

    except OperationFailure as ex:
        message = unicode(ex)
        request.errors.add('ificlaims-search', 'internals', message)
        log.error(request.errors)

    except Exception as ex:
        message = handle_generic_exception(request, ex, 'ificlaims-search', query)
        request.errors.add('ificlaims-search', 'search', message)

@ificlaims_published_data_crawl_service.get(accept="application/json")
@ificlaims_published_data_crawl_service.post(accept="application/json")
def ificlaims_published_data_crawl_handler(request):
    """Crawl published-data at IFI CLAIMS Direct"""

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
        result = ificlaims_crawl(constituents, query, chunksize)
        return result

    except Exception as ex:
        request.errors.add('ificlaims-crawl', 'crawl', unicode(ex))
        log.error(request.errors)
        log.error(u'query="{0}", exception:\n{1}'.format(query, _exception_traceback()))
