# -*- coding: utf-8 -*-
# (c) 2015-2016 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
#
# Lowlevel adapter to search provider "IFI Claims Direct"
#
import json
import time
import timeit
import logging
import requests
from pprint import pprint, pformat
from beaker.cache import cache_region
from requests.exceptions import ConnectionError, ConnectTimeout
from elmyra.ip.access.epo.imageutil import to_png
from elmyra.ip.access.ificlaims import get_ificlaims_client
from elmyra.ip.access.serviva import get_serviva_client
from elmyra.ip.util.data.container import SmartBunch
from elmyra.ip.util.numbers.normalize import normalize_patent

log = logging.getLogger(__name__)

class IFIClaimsException(Exception):
    def __init__(self, *args, **kwargs):
        self.user_info = ''
        if kwargs.has_key('user_info'):
            self.user_info = kwargs['user_info']
        super(IFIClaimsException, self).__init__(*args)

class LoginException(IFIClaimsException):
    pass

class SearchException(IFIClaimsException):
    pass

class IFIClaimsFormatException(IFIClaimsException):
    pass

class IFIClaimsClient(object):

    def __init__(self, uri, username=None, password=None, token=None):

        self.backend_name = 'IFI'
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

    def get_authentication_headers(self):
        headers = {'X-User': self.username, 'X-Password': self.password}
        return headers

    def search(self, expression, options=None):

        options = options or SmartBunch()

        offset = options.offset_remote or 0
        limit  = options.limit or self.pagesize

        log.info(u"{backend_name}: searching documents, expression='{0}', offset={1}, limit={2}".format(
            expression, offset, limit, **self.__dict__))

        if not self.token or self.stale:
            self.login()

        starttime = timeit.default_timer()

        # Define search request URI
        # https://cdws.ificlaims.com/search/query?q=pa:facebook
        # https://cdws.ificlaims.com/search/query?q=*:*&fl=ucid&rows=1
        uri     = self.uri + self.path_search

        # Define search request parameters
        # 'family.simple': True,
        params  = {'q': expression, 'fl': 'ucid,fam', 'start': offset, 'rows': limit, 'sort': 'pd desc, ucid asc'}

        log.info(u'IFI search. expression={expression}, uri={uri}, params={params}, options={options}'.format(
            expression=expression, uri=uri, params=params, options=options.dump()))

        # Perform search request
        headers = self.get_authentication_headers()
        headers.update({'Accept': 'application/json'})
        try:
            response = requests.get(
                uri,
                params=params,
                headers=headers,
                verify=self.tls_verify)
        except (ConnectionError, ConnectTimeout) as ex:
            log.error('IFI search for user "{username}" at "{uri}" failed. Reason: {0} {1}.'.format(
                ex.__class__, ex.message, username=self.username, uri=uri))
            #self.logout()
            self.stale = True
            raise SearchException(unicode(ex.__class__.__name__) + u': ' + unicode(ex.message),
                user_info='Error or timeout while connecting to upstream database. Database might be offline.')
        duration = timeit.default_timer() - starttime

        # Process search response
        if response.status_code == 200:

            #print "response:", response.content        # debugging

            try:
                search_results = self._search_parse_json(response.content)
                if search_results:

                    # Handle search errors
                    if 'error' in search_results['content']:
                        upstream_error = search_results['content']['error']
                        error = SearchException('Error in search expression')
                        error.details = 'code={code}, msg={msg}'.format(**upstream_error)
                        log.error('{backend_name}: Error in search expression: {0}'.format(pformat(upstream_error), **self.__dict__))
                        raise error

                    # Mogrify search response
                    # TODO: Generalize between all search backends
                    sr = IFIClaimsSearchResponse(search_results, options=options)
                    result = sr.render()
                    duration = round(duration, 1)

                    result['meta']['Offset'] = offset
                    result['meta']['Limit'] = limit

                    log.info('{backend_name}: Search succeeded. duration={duration}s, meta=\n{meta}'.format(
                        duration=duration, meta=result['meta'].prettify(), **self.__dict__))

                    if not result['numbers']:
                        log.warn('{backend_name}: Search had empty results. duration={duration}s, meta={meta}'.format(
                            duration=duration, meta=result['meta'].prettify(), **self.__dict__))

                    return result

                else:
                    log.error('{backend_name}: Search failed. Search response could not be parsed. content={0}'.format(
                        response.content, **self.__dict__))

            except Exception as ex:
                log.error('{backend_name}: Search failed. Reason: {0} {1}. response={2}'.format(
                    ex.__class__, ex.message, response.content, **self.__dict__))
                raise
        else:
            message = '{backend_name}: Search failed. status_code={0}, content={1}'.format(
                str(response.status_code) + ' ' + response.reason,
                response.content, **self.__dict__)
            log.error(message)
            raise SearchException(message)


    def crawl(self, constituents, expression, chunksize):
        # TODO: refactor into base class (from ftpro.search as well)

        if constituents not in ['pub-number', 'biblio']:
            raise ValueError('constituents "{0}" invalid or not implemented yet'.format(constituents))

        real_constituents = constituents
        if constituents == 'pub-number':
            constituents = ''

        # fetch first chunk (1-chunksize) from upstream
        #first_chunk = self.search(expression, 0, chunksize)
        first_chunk = ificlaims_search(expression, options=SmartBunch({'offset_remote': 0, 'limit': chunksize}))
        #print first_chunk

        total_count = int(first_chunk['meta'].get('pager', {}).get('totalEntries', 0))
        log.info('IFI: Crawl total_count: %s', total_count)

        # Limit maximum size
        # TODO: make configurable, put into instance variable
        total_count = min(total_count, 50000)

        # collect upstream results
        begin_second_chunk = chunksize
        chunks = [first_chunk]
        print 'range:', begin_second_chunk, total_count, chunksize
        log.info('IFI: Crawling {total_count} items with {chunksize} per request'.format(
            total_count=total_count, chunksize=chunksize))
        for range_begin in range(begin_second_chunk, total_count, chunksize):

            # countermeasure to robot flagging
            # <code>CLIENT.RobotDetected</code>
            # <message>Recent behaviour implies you are a robot. The server is at the moment busy to serve robots. Please try again later</message>
            time.sleep(1)

            log.info('IFI: Crawling from offset {offset}'.format(offset=str(range_begin)))
            #chunk = self.search(expression, range_begin, chunksize)
            chunk = ificlaims_search(expression, options=SmartBunch({'offset_remote': range_begin, 'limit': chunksize}))
            #print 'chunk:', chunk
            chunks.append(chunk)

        result_count = len(chunks)
        log.info('IFI: Crawling finished. result count: {result_count}'.format(result_count=result_count))

        #return chunks

        # merge chunks into single result
        all_numbers = []
        all_details = []
        # TODO: summarize elapsed_time
        for chunk in chunks:
            #print 'chunk:', chunk
            all_numbers += chunk['numbers']
            all_details += chunk['details']

        response = None
        if real_constituents == 'pub-number':
            response = first_chunk
            response['meta'] = {'Success': 'true', 'MemCount': str(len(all_numbers))}
            response['numbers'] = all_numbers
            del response['details']

        elif real_constituents == 'biblio':
            response = first_chunk
            #print 'all_details:', all_details
            response['meta'] = {'Success': 'true', 'MemCount': str(len(all_numbers))}
            response['details'] = all_details
            #del response['details']

        if not response:
            raise ValueError('constituents "{0}" invalid or not implemented yet'.format(constituents))

        return response


    #@cache_region('search')
    def text_fetch(self, ucid, format='xml'):

        """
        must normalize:
        EP666666A2 => EP0666666A2 (EP0666666A3, EP0666666B1)
        """

        log.info(u"{backend_name}: text_fetch, ucid={ucid}".format(ucid=ucid, **self.__dict__))

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


    #@cache_region('search')
    def attachment_list(self, ucid):

        log.info(u"{backend_name}: attachment_list, ucid={ucid}".format(ucid=ucid, **self.__dict__))

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


    #@cache_region('search')
    def attachment_fetch(self, path):

        log.info(u"{backend_name}: attachment_fetch, path={path}".format(path=path, **self.__dict__))

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

        log.info(u"{backend_name}: pdf_fetch, ucid={ucid}".format(ucid=ucid, **self.__dict__))

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
            tif_attachments = filter(lambda attachment: attachment['media'] == 'image/tiff', attachments)
            #print 'tif_attachments:'
            #pprint(tif_attachments)
            return tif_attachments


    def tif_fetch(self, ucid, seq=1):

        log.info(u"{backend_name}: tif_fetch, ucid={ucid}, seq={seq}".format(ucid=ucid, seq=seq, **self.__dict__))

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
        log.info(u"{backend_name}: png_fetch, ucid={ucid}, seq={seq}".format(ucid=ucid, seq=seq, **self.__dict__))
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

    def _search_parse_json(self, body):
        data = json.loads(body)
        if data['status'] == 'success':
            return data
        else:
            raise SearchException('Could not read result information from search response', response_body=body)


class IFIClaimsSearchResponse(object):

    def __init__(self, input, options=None):

        # arguments
        self.input = input
        self.options = options or {}

        # setup
        self.setup()

        # actions
        self.enrich()
        self.compat()

        if 'feature_family_remove' in self.options and self.options['feature_family_remove']:
            self.remove_family_members()

    def setup(self):

        meta = SmartBunch.bunchify({
            'navigator': {},
            # TODO: Move to "upstream"
            'time': self.input['time'],
            'status': self.input['status'],
            'params': self.input['content']['responseHeader']['params'],
            'pager': self.input['content']['responseHeader'].get('pager', {}),
        })

        self.response = self.input['content']['response']
        self.output = SmartBunch.bunchify({
            'meta': meta,
            'numbers': [],
            'details': [],
            'navigator': {},
        })


    def enrich(self):
        for result in self.response['docs']:
            try:
                ucid = result[u'ucid']
                cc, docno, kindcode = ucid.split('-')
                number = cc + docno + kindcode
            except (KeyError, TypeError):
                number = None
            number_normalized = normalize_patent(number)
            #print 'number:', number, number_normalized
            if number_normalized:
                number = number_normalized
            result[u'publication_number'] = number
            result[u'upstream_provider'] = u'ifi'

    def compat(self):
        meta = self.output.meta
        meta.navigator.count_total = int(self.output.meta.pager.totalEntries)
        meta.navigator.count_page  = int(self.output.meta.pager.entriesOnThisPage)
        meta.navigator.offset      = int(self.output.meta.params.start)
        meta.navigator.limit       = int(self.output.meta.params.rows)
        meta.navigator.postprocess = SmartBunch()

    def render(self):

        if self.output.meta.pager.totalEntries:
            # TODO: Generalize between"FulltextPRO "and IFI
            # meta['ResultLength'] = sr.get_length()
            self.output.numbers = self.get_numberlist()
            self.output.details = self.get_details()

        return self.output

    def get_length(self):
        return len(self.response['docs'])

    def get_numberlist(self):
        numbers = []
        for result in self.response['docs']:
            number = result['publication_number']
            numbers.append(number)
        return numbers

    def get_details(self):
        return self.response['docs']

    def remove_family_members(self):

        # Filtering mechanics: Deduplicate by family id
        seen = {}
        removed = []
        stats = SmartBunch(removed = 0)
        def family_remover(item):

            fam = item['fam']

            # Sanity checks on family id
            # Do not remove documents without valid family id
            if not fam or fam in [u'0', u'-1']:
                return True

            # "Seen" filtering logic
            if fam in seen:
                stats.removed += 1
                removed.append(item)
                return False
            else:
                seen[fam] = True
                return True


        # Update metadata and content

        # 1. Apply family cleansing filter to main documents response
        self.response['docs'] = filter(family_remover, self.response['docs'])

        # 2. Add list of removed family members to output
        self.output.navigator.family_members = {'removed': removed}
        #self.output['family-members-removed'] = removed

        # 3. Update metadata
        self.output.meta.navigator.postprocess.action = 'feature_family_remove'
        self.output.meta.navigator.postprocess.info   = stats


def ificlaims_client(options=None):
    options = options or SmartBunch()
    if 'vendor' in options and options.vendor == 'serviva':
        client = get_serviva_client()
    else:
        client = get_ificlaims_client()
    return client

#@cache_region('static')
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
        return client.search(query, options)

    except SearchException as ex:
        client.stale = True
        raise

    except SyntaxError as ex:
        log.warn('Invalid query for IFI: %s' % ex.msg)
        raise


@cache_region('search')
def ificlaims_crawl(constituents, query, chunksize, options=None):
    client = ificlaims_client(options=options)
    try:
        return client.crawl(constituents, query, chunksize)
    except SyntaxError as ex:
        log.warn('Invalid query for IFI: %s' % ex.msg)
        raise


