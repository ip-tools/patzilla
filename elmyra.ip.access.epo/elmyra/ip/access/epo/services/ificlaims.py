# -*- coding: utf-8 -*-
# (c) 2015-2016 Andreas Motl, Elmyra UG
#
# Cornice services for search provider "IFI Claims Direct"
#
import re
import cgi
import json
import time
import logging
from cornice.service import Service
from pymongo.errors import OperationFailure
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest
from pyramid.settings import asbool
from elmyra.ip.access.epo.services.util import request_to_options
from elmyra.ip.access.ificlaims.api import ificlaims_download, ificlaims_download_multi
from elmyra.ip.access.ificlaims.client import IFIClaimsException, IFIClaimsFormatException, LoginException, SearchException, ificlaims_search, ificlaims_crawl
from elmyra.ip.access.ificlaims.expression import should_be_quoted
from elmyra.ip.util.data.container import SmartBunch
from elmyra.ip.util.data.zip import zip_multi
from elmyra.ip.util.python import _exception_traceback

log = logging.getLogger(__name__)

ificlaims_published_data_search_service = Service(
    name='ificlaims-published-data-search',
    path='/api/ifi/published-data/search',
    description="IFI Claims search interface")
ificlaims_published_data_crawl_service = Service(
    name='ificlaims-published-data-crawl',
    path='/api/ifi/published-data/crawl{dummy1:\/?}{constituents:.*?}',
    description="IFI Claims crawler interface")

ificlaims_download_service = Service(
    name='ificlaims-download',
    path='/api/ifi/download/{resource}.{format}',
    description="IFI Claims download interface")
ificlaims_deliver_service = Service(
    name='ificlaims-deliver',
    path='/api/ifi/deliver/{kind}',
    description="IFI Claims deliver interface")


@ificlaims_download_service.get(renderer='null')
def ificlaims_download_handler(request):
    """Download resources from IFI Claims Direct"""

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

        raise HTTPNotFound("Resource '%s' with format='%s' not found" % (resource, format))


@ificlaims_deliver_service.get(renderer='null')
def ificlaims_deliver_handler(request):
    """Deliver resources from IFI Claims Direct in bulk"""

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
def ificlaims_published_data_search_handler(request):
    """Search for published-data at IFI Claims Direct"""

    # query expression
    query = request.params.get('query', '')
    log.info('query raw: ' + query)

    # fixup query: wrap into quotes if cql string is a) unspecific, b) contains spaces and c) is still unquoted
    if should_be_quoted(query):
        query = '"%s"' % query

    #propagate_keywords(request, query_object)

    # Lazy-fetch more entries
    # TODO: get from elmyra.ip.access.ificlaims
    limit = 250
    offset_local = int(request.params.get('range_begin', 0))
    offset_remote = int(offset_local / limit) * limit

    # Compute query options, like
    # - limit
    # - sorting
    # - whether to remove family members
    options = SmartBunch(vendor=None)
    options.update({
        'limit': limit,
        'offset_local': offset_local,
        'offset_remote': offset_remote,
    })

    # Propagate request parameters to search options parameters
    request_to_options(request, options)

    try:
        data = ificlaims_search(query, options)
        #print data.prettify()      # debugging
        return data

    except LoginException as ex:
        request.errors.add('IFI', 'login', ex.details)

    except SearchException as ex:
        message = unicode(ex.message)
        if hasattr(ex, 'details'):
            message += ': <pre>{details}</pre>'.format(details=cgi.escape(ex.details))
        request.errors.add('IFI', 'search', message)

    except SyntaxError as ex:
        request.errors.add('IFI', 'query', unicode(ex.msg))

    except OperationFailure as ex:
        log.error(ex)
        message = unicode(ex)
        request.errors.add('IFI', 'internals', message)


@ificlaims_published_data_crawl_service.get(accept="application/json")
def ificlaims_published_data_crawl_handler(request):
    """Crawl published-data at IFI Claims Direct"""

    # query expression
    query = request.params.get('query', '')
    log.info('query raw: ' + query)

    if should_be_quoted(query):
        query = '"%s"' % query

    # constituents: abstract, biblio and/or full-cycle
    constituents = request.matchdict.get('constituents', 'full-cycle')
    print 'constituents:', constituents

    chunksize = int(request.params.get('chunksize', '5000'))

    try:
        result = ificlaims_crawl(constituents, query, chunksize)
        return result

    except Exception as ex:
        log.error(u'IFI Claims crawler error: query="{0}", reason={1}, Exception was:\n{2}'.format(query, ex, _exception_traceback()))
        request.errors.add('ificlaims-published-data-crawl', 'query', str(ex))
