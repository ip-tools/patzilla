# -*- coding: utf-8 -*-
# (c) 2014-2018 Andreas Motl <andreas.motl@ip-tools.org>
import timeit
import logging
import requests
from lxml import etree
from beaker.cache import cache_region
from requests.exceptions import ConnectionError, ConnectTimeout
from patzilla.access.generic.exceptions import NoResultsException, GenericAdapterException
from patzilla.access.generic.search import GenericSearchResponse, GenericSearchClient
from patzilla.access.sip import get_sip_client
from patzilla.util.data.container import SmartBunch

"""

elmyra.ip.access.sip: lowlevel adapter to search provider "SIP"

"""

log = logging.getLogger(__name__)


class SipException(GenericAdapterException):

    # TODO: Clean up this mess ;]

    def __init__(self, *args, **kwargs):
        self.sip_info = ''
        super(SipException, self).__init__(*args)
        if kwargs.has_key('sip_info'):
            self.sip_info = kwargs['sip_info']
        if kwargs.has_key('sip_response'):
            self.sip_info = kwargs['sip_response'].get_childvalue('Info')
        if self.sip_info:
            self.user_info = self.sip_info

class LoginException(SipException):
    pass

class SearchException(SipException):
    pass

class SipClient(GenericSearchClient):

    def __init__(self, uri, username=None, password=None, sessionid=None):

        self.backend_name = 'sip'

        self.search_method = sip_published_data_search
        self.crawl_max_count = 5000

        self.uri = uri
        self.username = username
        self.password = password
        self.sessionid = sessionid
        self.pagesize = 250
        self.stale = False

    def login(self):
        starttime = timeit.default_timer()

        try:
            response = requests.post(self.uri + '/login', data={'Username': self.username, 'Password': self.password}, timeout=(3, 30))

        except (ConnectionError, ConnectTimeout) as ex:
            log.error('SIP login for user "{username}" at "{uri}" failed. Reason: {0} {1}.'.format(
                ex.__class__, ex.message, username=self.username, uri=self.uri))
            self.logout()
            error = LoginException(ex.message)
            error.sip_info = 'Error or timeout while connecting to upstream database. Database might be offline.'
            raise error

        if response.status_code == 200:
            try:
                self.sessionid = self._login_parse_xml(response.content)
                duration = timeit.default_timer() - starttime
                log.info('SIP login succeeded. sessionid={0}, duration={1}s'.format(self.sessionid, round(duration, 1)))
                return True
            except Exception as ex:
                log.error('SIP login for user "{username}" failed. Reason: {0} {1}. status_code={2}, response={3}'.format(
                    ex.__class__, ex.message, response.status_code, response.content, username=self.username))
                self.logout()
                raise
        else:
            message = 'SIP login failed. status_code={0}, content={1}'.format(response.status_code, response.content)
            log.error(message)
            error = LoginException(message)
            error.sip_info = 'Login to upstream database failed.'
            self.logout()
            raise error

        self.sessionid = None
        return False

    def logout(self):
        log.info('Logging out user "{username}"'.format(username=self.username))
        self.stale = True

    def search(self, expression, options=None):

        options = options or SmartBunch()

        options.setdefault('offset', 0)
        options.setdefault('limit', self.pagesize)

        offset = options.offset
        limit  = options.limit

        log.info(u"{backend_name}: searching documents, expression='{0}', offset={1}, limit={2}".format(
            expression, offset, limit, **self.__dict__))

        if not self.sessionid or self.stale:
            self.login()

        starttime = timeit.default_timer()
        try:
            response = requests.post(self.uri + '/search/new', data={'session': self.sessionid, 'searchtree': expression})
        except (ConnectionError, ConnectTimeout) as ex:
            log.error(u'SIP search for user "{username}" at "{uri}" failed. Reason: {0} {1}.'.format(
                ex.__class__, ex.message, username=self.username, uri=self.uri))
            self.logout()
            raise SearchException(ex.message,
                sip_info=u'Error or timeout while connecting to upstream database. Database might be offline.')

        # Process search response
        if response.status_code == 200:
            #print "SIP search response (raw)"; print response.content        # debugging
            try:
                search_response = self._search_parse_xml(response.content)

                if search_response['success'] == 'false':
                    raise SearchException(u'Search failed', sip_response=search_response['response'])

                if 'ResultSetId' in search_response['data']:

                    search_info = search_response['data']
                    ResultSetId = search_info['ResultSetId']

                    # Inject offset and limit into metadata, pretend it comes from server
                    search_info['Offset'] = offset
                    search_info['Limit'] = limit

                    # perform second request to actually retrieve the results by ResultSetId
                    search_results = self.getresults(ResultSetId, options)
                    #print "SIP search results:", search_results

                    duration = timeit.default_timer() - starttime
                    log.info(u'Search succeeded. duration={0}s, search_info={1}'.format(round(duration, 1), search_info))

                    upstream_response = {
                        'info': search_info,
                        'results': search_results or [],
                    }

                    # Mogrify search response
                    # TODO: Generalize between all search backends
                    sr = SipSearchResponse(upstream_response, options=options)
                    result = sr.render()
                    duration = round(duration, 1)

                    # TODO: Unify between SIP and IFI CLAIMS
                    log.info(u'{backend_name}: Search succeeded. duration={duration}s, meta=\n{meta}'.format(
                        duration=duration, meta=result['meta'].prettify(), **self.__dict__))

                    if not result['numbers']:
                        log.warn(u'{backend_name} search from "{user}" for "{expression}" had empty results.'.format(
                            user=self.username, expression=expression, **self.__dict__
                        ))

                    return result

                else:
                    message = u'Search failed. Reason: Upstream response lacks valid ResultSetId. content={0}'.format(response.text)
                    raise SearchException(message, sip_info=u'Search failed. Search response could not be parsed.')

            except Exception as ex:
                log.error(u'Search failed. {name}: {message}. expression={expression}, response={response}'.format(
                    name=ex.__class__.__name__, message=ex.message, response=response.text, expression=expression))
                raise

        else:
            response_status = str(response.status_code) + ' ' + response.reason
            message = u'SIP search failed. Reason: response status != 200. status={0}, content={1}'.format(
                response_status,
                response.text)
            log.error(message)
            raise SearchException(message,
                sip_info=u'HTTP error "{status}" while searching upstream database'.format(status=response_status))


    def getresults(self, resultid, options):

        request_xml = '<getresult id="{0}" start="{1}" count="{2}" />'.format(resultid, options.offset, options.limit)
        log.info('SIP: Getting results: {}'.format(request_xml))

        starttime = timeit.default_timer()
        response = requests.post(self.uri + '/search/getresults', data={'session': self.sessionid, 'resultrequest': request_xml})
        if response.status_code == 200:
            #print response.content
            try:
                results = self._getresults_parse_xml(response.content)
                if results:

                    if len(results) == 1 and results[0]['docid'] == '0':
                        message = results[0]['title']
                        log.error(message)
                        raise SearchException(message)

                    duration = timeit.default_timer() - starttime
                    log.info(u'SIP getresults succeeded. duration={0}s'.format(round(duration, 1)))
                    return results

            except SearchException:
                raise

            except Exception as ex:
                message = u'SIP getresults failed. Unknown exception. Reason: {0} {1}'.format(
                    ex.__class__, ex.message)
                logmessage = u'{}. response={}'.format(message, response.text)
                log.error(logmessage)
                raise SearchException(message)

        else:
            message = u'SIP getresults failed. status_code={0}'.format(
                str(response.status_code) + ' ' + response.reason)
            logmessage = u'{}. response={}'.format(message, response.text)
            log.error(logmessage)
            raise SearchException(message)

    def _login_parse_xml(self, xml):
        response = SipXmlResponse(xml)
        success = response.get_childvalue('Success')
        if success == 'true':
            session = response.get_childvalue('Session')
            return session

        error = LoginException('No session information in XML login response', sip_response=response)
        if 'Server currently not available' in error.sip_info \
            or 'There was no endpoint listening' in error.sip_info \
            or 'Communication error' in error.sip_info:
            error.sip_info += '<br/><br/>' \
                              'The SIP API might be in maintenance mode, <br/>' \
                              'this happens regularly on Wednesday evenings at 17:00 hours UTC (19:00 hours CEST)<br/>' \
                              'and usually does not take longer than one hour.'

        if error.sip_info == u'i':
            error.sip_info = u'Login failed'
        raise error

    def _search_parse_xml(self, xml):
        response = SipXmlResponse(xml)
        success = response.get_childvalue('Success')

        info = {
            'success': success,
            'response': response,
            'data': {},
        }

        if success == 'true':
            payload = response.get_childdict()
            info['data'] = payload

        return info

    def _getresults_parse_xml(self, xml):
        response = SipXmlResponse(xml)
        results = response.get_childlist('Result')
        return results


class SipXmlResponse(object):

    def __init__(self, xml):
        self.xml = xml
        self.tree = etree.fromstring(self.xml)
        self.xml_namespaces = {
            'dc-search': 'http://schemas.datacontract.org/2004/07/Search',
        }

    def get_childvalue(self, tagname):
        value = self.tree.find('dc-search:{0}'.format(tagname), namespaces=self.xml_namespaces).text
        return value

    def get_childdict(self, node=None):
        node = node or self.tree
        return self._getddict(node)

    def get_childlist(self, tagname):
        children = self.tree.findall('dc-search:{0}'.format(tagname), namespaces=self.xml_namespaces)
        entries = []
        for child in children:
            entries.append(self._getddict(child))

        return entries

    def _getddict(self, node):
        entry = {}
        attributes = node.getchildren()
        for attribute in attributes:
            tag = attribute.tag.replace('{' + self.xml_namespaces['dc-search'] + '}', '')
            text = attribute.text
            entry[tag] = text
        return entry


class SipSearchResponse(GenericSearchResponse):

    def read(self):

        # Read metadata
        """
        in:
        "info": {
            "Info": "Search processed in 2905",
            "Success": "true",
            "ResultLength": 250,
            "FamCount": "1200",
            "DocCount": "5432",
            "MemCount": "3599",
            "Limit": 250,
            "Offset": 0,
            "ResultSetId": "4153687"
        },
        """
        self.meta.upstream.update(self.input['info'])
        self.meta.upstream.update({
            'name': 'sip',
            # TODO: Reference from IFI CLAIMS, fill up/unify.
            #'time': self.input['time'],
            #'status': self.input['status'],
            #'params': SmartBunch.bunchify(self.input['content']['responseHeader']['params']),
            #'pager': SmartBunch.bunchify(self.input['content']['responseHeader'].get('pager', {})),
        })

        self.meta.navigator.count_total = int(self.meta.upstream.MemCount)
        self.meta.navigator.count_page  = len(self.input['results'])
        self.meta.navigator.offset      = int(self.meta.upstream.Offset)
        self.meta.navigator.limit       = int(self.meta.upstream.Limit)
        self.meta.navigator.postprocess = SmartBunch()

        # Read content
        """
        in:
        "results": [{
        }],
        """
        self.documents = self.input['results']
        self.read_documents()

    def document_to_number(self, document):
        number = document['cc'] + document['docno'] + document['kd']
        return number

    def document_to_family_id(self, document):
        return document['famid']


@cache_region('search', 'sip_search')
def sip_published_data_search(query, options):

    # <applicant type="inpadoc">grohe</applicant>
    # <applicant type="inpadoc">siemens</applicant>

    sip = get_sip_client()
    try:
        data = sip.search(query, options)

        # Raise an exception on empty results to skip caching this response
        if data.meta.navigator.count_total == 0:
            raise NoResultsException('No results', data=data)

        return data

    except SyntaxError as ex:
        log.warn('Invalid query for SIP: %s' % ex.msg)
        raise

    except SearchException as ex:
        if 'Call LOGIN' in ex.sip_info:
            sip.logout()
        raise


@cache_region('search')
def sip_published_data_crawl(constituents, query, chunksize):
    sip = get_sip_client()
    try:
        return sip.crawl(constituents, query, chunksize)
    except SyntaxError as ex:
        log.warn('Invalid query for SIP: %s' % ex.msg)
        raise


if __name__ == '__main__':
    logging.basicConfig(level='INFO')

    # 2014bis
    #sip = SipClient(uri='http://62.245.145.108:2000', username='gartzen@elmyra.de', password='fAaVq4GwXi')

    # 2016-04-17: inventionnavigator.com, 46.245.182.230
    sip = SipClient(uri='http://inventionnavigator.com:2000', sessionid='MFbZjdAKJ0mfg4VvwFZZbWqeygU=')

    #sip.login()
    #xml = '<LoginResult xmlns="http://schemas.datacontract.org/2004/07/Search" xmlns:i="http://www.w3.org/2001/XMLSchema-instance"><Session>XorMTLpxuUmAkSNf5hnCsDdDz88=</Session><Success>true</Success></LoginResult>'
    #sip.login_parse_xml(xml)
    results = sip.search('<applicant type="inpadoc">hexal</applicant>')
    print(results)
    #pprint(results)

    #results = sip.search('<applicant type="inpadoc">siemens</applicant>')
    #print(results)
