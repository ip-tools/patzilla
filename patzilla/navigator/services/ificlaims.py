# -*- coding: utf-8 -*-
# (c) 2015-2018 Andreas Motl <andreas.motl@ip-tools.org>
#
# HTTP API for search provider "IFI CLAIMS Direct"
#
import re
import json
import time
import logging

from fastapi import APIRouter, HTTPException, Response
from pymongo.errors import OperationFailure
from patzilla.navigator.services import handle_generic_exception
from patzilla.util.expression.keywords import keywords_to_response
from patzilla.navigator.services.util import request_to_options
from patzilla.access.generic.exceptions import NoResultsException, SearchException, ServiceError
from patzilla.access.ificlaims.api import ificlaims_download, ificlaims_download_multi
from patzilla.access.ificlaims.client import IFIClaimsException, IFIClaimsFormatException, LoginException, ificlaims_search, ificlaims_crawl
from patzilla.access.ificlaims.expression import should_be_quoted, IFIClaimsParser
from patzilla.util.data.container import SmartMunch
from patzilla.util.data.zip import zip_multi
from patzilla.util.python import _exception_traceback
from patzilla.web.dependencies import IfiClaimsClient, LenientBool, Params

log = logging.getLogger(__name__)

router = APIRouter(tags=["ificlaims"])


@router.get("/api/status/upstream/ificlaims/direct", name="status_ificlaims",
            summary="Checks IFI CLAIMS upstream for valid response")
def status_upstream_ificlaims_handler(client: IfiClaimsClient):
    query = SmartMunch({
        'expression': 'pn:EP0666666',
    })
    data = client.search_real(query)
    assert data, 'Empty response from IFI CLAIMS'
    return "OK"


@router.get("/api/ificlaims/download/{resource}.{format}", name="ificlaims-download",
            summary="IFI CLAIMS download interface")
def ificlaims_download_handler(resource: str, format: str, client: IfiClaimsClient,
                               pretty: LenientBool = False, seq: int = 1):
    """Download resources from IFI CLAIMS Direct"""

    format = format.lower()
    options = {'pretty': pretty, 'seq': seq}

    try:
        response = ificlaims_download(client, resource, format, options)

    except IFIClaimsException as ex:
        if type(ex) is IFIClaimsFormatException:
            raise HTTPException(404, str(ex))
        else:
            raise HTTPException(400, str(ex))

    if response.payload:

        # http://tools.ietf.org/html/rfc6266#section-4.2
        disposition = response.disposition_inline and 'inline' or 'attachment'

        content_disposition = '{disposition}; filename={filename}'.format(disposition=disposition, filename=response.filename)
        return Response(response.payload, media_type=response.mimetype, headers={
            'Content-Disposition': content_disposition,
            'Data-Source': 'ifi',
        })

    else:
        msg = "Resource '%s' with format='%s' not found" % (resource, format)
        log.warning(msg)
        raise HTTPException(404, msg)


@router.get("/api/ificlaims/deliver/{kind}", name="ificlaims-deliver", summary="IFI CLAIMS deliver interface")
def ificlaims_deliver_handler(kind: str, client: IfiClaimsClient, formats: str = '', numberlist: str = ''):
    """Deliver resources from IFI CLAIMS Direct in bulk"""

    formats = list(map(str.strip, formats.lower().split(',')))
    numberlist = [item for item in map(str.strip, re.split('[\n,]', numberlist)) if bool(item)]

    if kind == 'zip':
        multi = ificlaims_download_multi(client, numberlist, formats)

        #for entry in multi['results']:
        #    print 'entry:', entry
        print('report:')
        print(json.dumps(multi['report'], indent=4))

        payload = zip_multi(multi)

        disposition = 'attachment'
        zipname = time.strftime('ificlaims-delivery_%Y%m%d-%H%M%S.zip')

        content_disposition = '{disposition}; filename={filename}'.format(disposition=disposition, filename=zipname)
        return Response(payload, media_type='application/zip', headers={
            'Content-Disposition': content_disposition,
            'Data-Source': 'ifi',
        })
    else:
        raise HTTPException(400, "Unknown delivery kind '{kind}'".format(**locals()))


# TODO: implement as JSON POST
@router.api_route("/api/ificlaims/published-data/search", methods=["GET", "POST"],
                  name="ificlaims-published-data-search", summary="IFI CLAIMS search interface")
def ificlaims_published_data_search_handler(response: Response, client: IfiClaimsClient, params: Params):
    """Search for published-data at IFI CLAIMS Direct"""

    # Get hold of query expression and filter
    query = SmartMunch({
        'expression': params.get('expression', ''),
        'filter':     params.get('filter', ''),
    })
    log.info('Query: {}'.format(query))

    # Parse expression, extract and propagate keywords to user interface
    parser = IFIClaimsParser(query.expression)
    keywords_to_response(response, parser)

    # Fixup query: wrap into quotes if cql string is a) unspecific, b) contains spaces and c) is still unquoted
    if should_be_quoted(query.expression):
        query.expression = '"%s"' % query.expression

    # Lazy-fetch more entries
    # TODO: get from patzilla.access.ificlaims
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
        data = ificlaims_search(client, query, options)
        #print data.prettify()      # debugging
        return data

    except LoginException as ex:
        error = ServiceError('ificlaims-search', 'login', ex.get_message())
        log.warning(error.errors)
        raise error

    except SyntaxError as ex:
        error = ServiceError('ificlaims-search', 'expression', str(ex.msg))
        log.warning(error.errors)
        raise error

    except SearchException as ex:
        message = ex.get_message()
        error = ServiceError('ificlaims-search', 'search', message)
        log.warning(error.errors)
        raise error

    except NoResultsException as ex:
        # Forward response to let the frontend recognize zero hits
        response.status_code = 404
        return ex.data

    except OperationFailure as ex:
        message = str(ex)
        error = ServiceError('ificlaims-search', 'internals', message)
        log.error(error.errors)
        raise error

    except Exception as ex:
        message = handle_generic_exception(ex, 'ificlaims-search', query)
        raise ServiceError('ificlaims-search', 'search', message)


@router.api_route("/api/ificlaims/published-data/crawl", methods=["GET", "POST"],
                  name="ificlaims-published-data-crawl", summary="IFI CLAIMS crawler interface")
@router.api_route("/api/ificlaims/published-data/crawl/{constituents:path}", methods=["GET", "POST"],
                  name="ificlaims-published-data-crawl")
def ificlaims_published_data_crawl_handler(client: IfiClaimsClient, params: Params, constituents: str = 'full-cycle'):
    """Crawl published-data at IFI CLAIMS Direct"""

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
        result = ificlaims_crawl(client, constituents, query, chunksize)
        return result

    except Exception as ex:
        error = ServiceError('ificlaims-crawl', 'crawl', str(ex))
        log.error(error.errors)
        log.error('query="{0}", exception:\n{1}'.format(query, _exception_traceback()))
        raise error
