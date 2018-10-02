# -*- coding: utf-8 -*-
# (c) 2015-2017 Andreas Motl <andreas.motl@ip-tools.org>
#
# Lowlevel adapter to search provider "IFI CLAIMS Direct"
# http://docs.ificlaims.com/
#
import re
import json
import timeit
import logging
import requests
from pprint import pprint
from beaker.cache import cache_region
from requests.exceptions import RequestException
from patzilla.util.image.convert import to_png
from patzilla.access.generic.exceptions import NoResultsException, GenericAdapterException, SearchException
from patzilla.access.generic.search import GenericSearchResponse, GenericSearchClient
from patzilla.access.ificlaims import get_ificlaims_client
from patzilla.util.data.container import SmartBunch
from patzilla.util.numbers.normalize import normalize_patent

log = logging.getLogger(__name__)

class IFIClaimsException(GenericAdapterException):
    pass

class LoginException(IFIClaimsException):
    pass

class IFIClaimsFormatException(IFIClaimsException):
    pass

class IFIClaimsClient(GenericSearchClient):

    def __init__(self, uri, username=None, password=None, token=None):

        self.backend_name = 'ificlaims'

        self.search_method = ificlaims_search
        self.crawl_max_count = 50000

        self.path_search            = '/search/query'
        self.path_text              = '/text/fetch'
        self.path_attachment_list   = '/attachment/list'
        self.path_attachment_fetch  = '/attachment/fetch'

        self.uri = uri
        self.username = username
        self.password = password
        self.token = token
        self.pagesize = 250
        self.stale = False

        self.tls_verify = True

    def login(self):
        self.token = True
        return True

    def logout(self):
        self.stale = True

    def get_authentication_headers(self):
        headers = {'X-User': self.username, 'X-Password': self.password}
        return headers

    @cache_region('search')
    def search(self, query, options=None):
        return self.search_real(query, options=options)

    def search_real(self, query, options=None):

        query.setdefault('filter', '')

        options = options or SmartBunch()
        options.setdefault('offset', 0)
        options.setdefault('limit', self.pagesize)

        offset = options.offset
        limit  = options.limit

        log.info(u"{backend_name}: searching documents, expression='{0}', offset={1}, limit={2}; user={username}".format(
            query.expression, offset, limit, **self.__dict__))

        if not self.token or self.stale:
            self.login()

        starttime = timeit.default_timer()

        # Define search request URI
        # https://cdws.ificlaims.com/search/query?q=pa:facebook
        # https://cdws.ificlaims.com/search/query?q=*:*&fl=ucid&rows=1
        uri     = self.uri + self.path_search

        # Define search request parameters
        # 'family.simple': True,
        params  = {
            'q': query.expression, 'fq': query.filter,
            'sort': 'pd desc, ucid asc',
            'fl': 'ucid,fam',
            'start': offset, 'rows': limit,
        }

        log.info(u'IFI CLAIMS search. query={query}, uri={uri}, params={params}, options={options}'.format(
            query=query, uri=uri, params=params, options=options.dump()))

        # Perform search request
        headers = self.get_authentication_headers()
        headers.update({'Accept': 'application/json'})
        try:
            response = requests.get(
                uri,
                params=params,
                headers=headers,
                verify=self.tls_verify)
        except RequestException as ex:
            self.logout()
            raise self.search_failed(
                ex=ex,
                user_info='Error or timeout while connecting to upstream database. Database might be offline.',
                meta={'username': self.username, 'uri': uri})
        duration = timeit.default_timer() - starttime

        #print "response:", response.content        # debugging

        # Process search response
        if response.status_code == 200:
            #print "response:", response.content        # debugging

            response_data = json.loads(response.content)
            if response_data['status'] == 'success':

                # Debugging: Simulate error
                #response_data['content']['error'] = {'code': 503, 'msg': 'no servers hosting shard'}

                # Handle search expression errors
                if 'error' in response_data['content']:
                    upstream_error = response_data['content']['error']

                    if 'msg' not in upstream_error:
                        upstream_error['msg'] = 'Reason unknown'

                    message = u'Response status code: {code}\n\n{msg}'.format(**upstream_error)

                    # Enrich "maxClauseCount" message, e.g. raised by {!complexphrase}text:"auto* AND leucht*"~5
                    if upstream_error["code"] == 500 and u'maxClauseCount is set to' in upstream_error["msg"]:
                        raise self.search_failed(
                            user_info=u'Too many terms in phrase expression, wildcard term prefixes might by too short.',
                            message=message,
                            response=response)

                    # Enrich "no servers hosting shard" message
                    elif upstream_error["code"] == 503 and \
                        (
                            u'no servers hosting shard' in upstream_error["msg"] or \
                            u'No server is available' in upstream_error["msg"]
                        ):
                        raise self.search_failed(
                            user_info=u'Error while connecting to upstream database. Database might be offline.',
                            message=message,
                            response=response)

                    # Regular traceback
                    elif upstream_error["code"] == 500 and 'trace' in upstream_error:
                        message = u'Response status code: {code}\n\n{trace}'.format(**upstream_error)
                        raise self.search_failed(
                            user_info=u'Unknown exception at search backend',
                            message=message,
                            response=response)

                    # Enrich "SyntaxError" exception
                    elif upstream_error["code"] == 400 and u'ParseException' in upstream_error["msg"]:
                        user_info = re.sub(
                            r'.*(Encountered.*at line.*?\.).*',
                            r'SyntaxError, can not parse query expression: \1',
                            upstream_error["msg"],
                            flags=re.DOTALL)
                        raise self.search_failed(
                            user_info=user_info,
                            message=message,
                            response=response)

                    else:
                        raise self.search_failed(
                            user_info=message,
                            response=response)

                # Mogrify search response
                # TODO: Generalize between all search backends
                sr = IFIClaimsSearchResponse(response_data, options=options)
                result = sr.render()
                duration = round(duration, 1)

                # TODO: Unify between IFI CLAIMS and SIP
                log.info('{backend_name}: Search succeeded. duration={duration}s, meta=\n{meta}'.format(
                    duration=duration, meta=result['meta'], **self.__dict__))

                if not result['numbers']:
                    log.warn('{backend_name}: Search had empty results. duration={duration}s, meta=\n{meta}'.format(
                        duration=duration, meta=result['meta'], **self.__dict__))

                return result

            elif response_data['status'] == 'error':

                user_info = None
                if response_data['message'] == 'JSON error: failed to read response object':
                    user_info = u'Error while connecting to upstream database. Database might be offline.'

                raise self.search_failed(
                    user_info=user_info,
                    message=response_data['message'],
                    response=response)

            else:
                raise self.search_failed('Search response could not be parsed', response=response)

        else:
            # print "response:", response.content        # debugging

            self.logout()

            # Strip HTML from response body
            response_content = response.content
            if response.headers['Content-Type'].startswith('text/html'):
                response_content = re.sub('<[^<]+?>', '', response_content).strip().replace('\r\n', ', ')

            # Build alternative basic error structure
            upstream_error = {
                'code': response.status_code,
                'reason': response.reason,
                'content': response_content,
            }

            message = json.dumps(upstream_error)

            raise self.search_failed(
                user_info=u'Error while connecting to upstream database. Database might be offline.',
                message=message,
                response=response)


        raise self.search_failed(response=response)


    @cache_region('search')
    def text_fetch(self, ucid, format='xml'):

        """
        must normalize:
        EP666666A2 => EP0666666A2 (EP0666666A3, EP0666666B1)
        """

        log.info(u"{backend_name}: text_fetch, ucid={ucid}; user={username}".format(ucid=ucid, **self.__dict__))

        starttime = timeit.default_timer()

        if not self.token or self.stale:
            self.login()

        if format == 'xml':
            mimetype = 'text/xml'
        elif format == 'json':
            mimetype = 'application/json'
        else:
            raise ValueError('Unknown format "{0}" requested'.format(format))

        # https://cdws.ificlaims.com/text/fetch?ucid=US-20100077592-A1
        headers = self.get_authentication_headers()
        headers.update({'Accept': mimetype})
        response = requests.get(
            self.uri + self.path_text,
            params={'ucid': ucid},
            headers=headers,
            verify=self.tls_verify)
        duration = timeit.default_timer() - starttime

        if response.status_code == 200:
            return response.content


    @cache_region('medium')
    def attachment_list(self, ucid):

        log.info(u"{backend_name}: attachment_list, ucid={ucid}; user={username}".format(ucid=ucid, **self.__dict__))

        if not self.token or self.stale:
            self.login()

        starttime = timeit.default_timer()

        # https://cdws.ificlaims.com/attachment/list?ucid=US-20100077592-A1
        headers = self.get_authentication_headers()
        headers.update({'Accept': 'application/json'})
        response = requests.get(
            self.uri + self.path_attachment_list,
            params={'ucid': ucid},
            headers=headers,
            verify=self.tls_verify)
        duration = timeit.default_timer() - starttime

        if response.status_code == 200:
            #print response.content
            data = json.loads(response.content)
            return data
        else:
            log.error(u"{backend_name}: attachment_list, ucid={ucid}, status={status}, response={response}".format(
                ucid=ucid, status=response.status_code, response=response.content , **self.__dict__))


    @cache_region('longer')
    def attachment_fetch(self, path):

        log.info(u"{backend_name}: attachment_fetch, path={path}; user={username}".format(path=path, **self.__dict__))

        if not self.token or self.stale:
            self.login()

        starttime = timeit.default_timer()

        # https://cdws.ificlaims.com/attachment/fetch?path=/b4knn/vj86f/v01zz/lt6r6/US-20100077592-A1-20100401/US20100077592A1
        #path = '/b4knn/vj86f/v01zz/lt6r6/US-20100077592-A1-20100401/US20100077592A1'
        log.info('Attachment path: {path}'.format(path=path))
        log.info(self.uri + self.path_attachment_fetch)
        headers = self.get_authentication_headers()
        response = requests.get(
            self.uri + self.path_attachment_fetch,
            params={'path': path},
            headers=headers,
            verify=self.tls_verify)
        duration = timeit.default_timer() - starttime

        if response.status_code == 200:
            #print 'response.content:', response.content
            return response.content

        else:
            log.error(u"{backend_name}: attachment_fetch, path={path}, status={status}, response={response}".format(
                path=path, status=response.status_code, response=response.content , **self.__dict__))


    def pdf_fetch(self, ucid):

        log.info(u"{backend_name}: pdf_fetch, ucid={ucid}; user={username}".format(ucid=ucid, **self.__dict__))

        attachments_response = self.attachment_list(ucid)
        if not attachments_response:
            return

        print 'attachments_response:'
        pprint(attachments_response)

        attachments = attachments_response['attachments']
        if attachments:

            """
            {u'attachments': [{u'filename': u'00000001.tif',
                               u'media': u'image/tiff',
                               u'path': u'/EP/20030102/A3/000000/66/66/66/00000001.tif',
                               u'pkey': u'EP-0666666-A3-20030102',
                               u'size': 10248},
                              {u'filename': u'90000001.tif',
                               u'media': u'image/tiff',
                               u'path': u'/EP/20030102/A3/000000/66/66/66/90000001.tif',
                               u'pkey': u'EP-0666666-A3-20030102',
                               u'size': 47860},
                              {u'filename': u'90010001.tif',
                               u'media': u'image/tiff',
                               u'path': u'/EP/20030102/A3/000000/66/66/66/90010001.tif',
                               u'pkey': u'EP-0666666-A3-20030102',
                               u'size': 32986},
                              {u'filename': u'EP0666666A320030102.pdf',
                               u'media': u'application/pdf',
                               u'path': u'/EP/20030102/A3/000000/66/66/66/EP0666666A320030102.pdf',
                               u'pkey': u'EP-0666666-A3-20030102',
                               u'size': 161904}],
             u'count': 4,
             u'status': u'success',
             u'time': u'0.012695'}
            """

            # find pdf reference
            pdf_attachment = None
            for attachment in attachments:
                if attachment['media'] == 'application/pdf':
                    pdf_attachment = attachment
                    break

            if pdf_attachment:
                path = pdf_attachment['path']
                return self.attachment_fetch(path)

    def tif_attachments(self, ucid):

        attachments_response = self.attachment_list(ucid)
        if not attachments_response:
            return

        print 'attachments_response:'
        pprint(attachments_response)

        attachments = attachments_response['attachments']
        if attachments:

            """
            {u'attachments': [{u'filename': u'EP0666666A219950809.pdf',
                               u'media': u'application/pdf',
                               u'path': u'/EP/19950809/A2/000000/66/66/66/EP0666666A219950809.pdf',
                               u'pkey': u'EP-0666666-A2-19950809',
                               u'size': 448486},
                              {u'filename': u'imgaf001.tif',
                               u'media': u'image/tiff',
                               u'path': u'/EP/19950809/A2/000000/66/66/66/imgaf001.tif',
                               u'pkey': u'EP-0666666-A2-19950809',
                               u'size': 4140},
                              {u'filename': u'imgf0001.tif',
                               u'media': u'image/tiff',
                               u'path': u'/EP/19950809/A2/000000/66/66/66/imgf0001.tif',
                               u'pkey': u'EP-0666666-A2-19950809',
                               u'size': 15213},
                              {u'filename': u'imgf0002.tif',
                               u'media': u'image/tiff',
                               u'path': u'/EP/19950809/A2/000000/66/66/66/imgf0002.tif',
                               u'pkey': u'EP-0666666-A2-19950809',
                               u'size': 13718}],
             u'count': 4,
             u'status': u'success',
             u'time': u'0.015832'}
            """

            # filter tif references only
            tif_attachments = filter(lambda attachment: attachment['media'] in ['image/tiff', 'image/jpeg'], attachments)
            #print 'tif_attachments:'
            #pprint(tif_attachments)
            return tif_attachments


    def tif_fetch(self, ucid, seq=1):

        log.info(u"{backend_name}: tif_fetch, ucid={ucid}, seq={seq}; user={username}".format(ucid=ucid, seq=seq, **self.__dict__))

        tif_attachments = self.tif_attachments(ucid)

        if tif_attachments:

            # find tif sequence
            tif_attachment = None
            for index, attachment in enumerate(tif_attachments):
                if index == seq - 1:
                    tif_attachment = attachment
                    break

            log.info('Found TIF attachment: {0}'.format(tif_attachment))

            if tif_attachment:
                path = tif_attachment['path']
                return self.attachment_fetch(path)

    def png_fetch(self, ucid, seq=1):
        log.info(u"{backend_name}: png_fetch, ucid={ucid}, seq={seq}; user={username}".format(ucid=ucid, seq=seq, **self.__dict__))
        tif = self.tif_fetch(ucid, seq)
        if tif:
            png = to_png(tif)
            return png


    def _login_parse_token(self, body):

        data = json.loads(body)

        if 'token' in data:
            return data['token']
        else:
            error = LoginException('Could not read token information from login response', response_body=body)
            raise error


class IFIClaimsSearchResponse(GenericSearchResponse):

    def read(self):

        # Read metadata
        """
        out:
        "meta": {
            "status": "success",
            "params": {
                "sort": "pd desc, ucid asc",
                "rows": "250",
                "indent": "true",
                "qt": "premium",
                "timeAllowed": "300000",
                "q": "text:vibrat* AND (ic:G01F000184 OR cpc:G01F000184)",
                "start": "0",
                "wt": "json",
                "fl": "ucid,fam"
            },
            "pager": {
                "totalEntries": 6872,
                "entriesOnThisPage": 250,
                "firstPage": 1,
                "lastPage": 28,
                "previousPage": null,
                "currentPage": 1,
                "entriesPerPage": "250",
                "nextPage": 2
            },
            "name": "ifi",
            "time": "4.836163"
        }
        """
        self.meta.upstream.update({
            'name': 'ifi',
            'time': self.input['time'],
            'status': self.input['status'],
            'params': SmartBunch.bunchify(self.input['content']['responseHeader']['params']),
            'pager': SmartBunch.bunchify(self.input['content']['responseHeader'].get('pager', {})),
        })

        self.meta.navigator.count_total = int(self.meta.upstream.pager.totalEntries)
        self.meta.navigator.count_page  = int(self.meta.upstream.pager.entriesOnThisPage)
        self.meta.navigator.offset      = int(self.meta.upstream.params.start)
        self.meta.navigator.limit       = int(self.meta.upstream.params.rows)
        self.meta.navigator.postprocess = SmartBunch()

        # Read content
        self.documents = self.input['content']['response']['docs']
        self.read_documents()

    def document_to_number(self, document):
        ucid = document[u'ucid']
        cc, docno, kindcode = ucid.split('-')
        number = cc + docno + kindcode
        number_normalized = normalize_patent(number)
        if number_normalized:
            number = number_normalized
        return number

    def document_to_family_id(self, document):
        return document['fam']


def ificlaims_client(options=None):
    options = options or SmartBunch()
    if 'vendor' in options and options.vendor == 'serviva':
        client = get_serviva_client()
    else:
        client = get_ificlaims_client()
    return client

@cache_region('static')
def ificlaims_fetch(resource, format, options=None):
    options = options or {}
    client = ificlaims_client(options=options)
    if format in ['xml', 'json']:
        return client.text_fetch(resource, format)
    elif format == 'pdf':
        return client.pdf_fetch(resource)
    elif format == 'tif':
        return client.tif_fetch(resource, options.get('seq', 1))
    elif format == 'png':
        return client.png_fetch(resource, options.get('seq', 1))
    else:
        msg = "Unknown format '{0}' requested for resource '{1}'".format(format, resource)
        log.warning(msg)
        raise IFIClaimsFormatException(msg)


@cache_region('search')
def ificlaims_search(query, options=None):

    options = options or SmartBunch()

    client = ificlaims_client(options=options)
    try:
        data = client.search(query, options)
        # Raise an exception on empty results to skip caching this response
        if data.meta.navigator.count_total == 0:
            raise NoResultsException('No results', data=data)
        return data

    except SearchException as ex:
        client.stale = True
        raise


@cache_region('search')
def ificlaims_crawl(constituents, query, chunksize, options=None):
    client = ificlaims_client(options=options)
    try:
        return client.crawl(constituents, query, chunksize)
    except SyntaxError as ex:
        log.warn('Invalid query for IFI: %s' % ex.msg)
        raise


