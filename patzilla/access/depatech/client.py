# -*- coding: utf-8 -*-
# (c) 2017 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
#
# Lowlevel adapter to search provider "MTC depa.tech"
# https://depa.tech/api/depa-index/
#
import json
import timeit
import logging
import requests
from beaker.cache import cache_region
from requests import RequestException
from patzilla.access.depatech import get_depatech_client
from patzilla.access.generic.exceptions import NoResultsException, GenericAdapterException, SearchException
from patzilla.access.generic.search import GenericSearchResponse, GenericSearchClient
from patzilla.util.data.container import SmartBunch
from patzilla.util.numbers.normalize import normalize_patent

log = logging.getLogger(__name__)

class DepaTechException(GenericAdapterException):
    pass

class LoginException(DepaTechException):
    pass

class DepaTechFormatException(DepaTechException):
    pass

class DepaTechClient(GenericSearchClient):

    def __init__(self, uri, username=None, password=None, token=None):

        self.backend_name = 'depatech'

        self.search_method = depatech_search

        self.search_max_hits = 10000
        self.crawl_max_count = 50000

        self.path_search = '/es/deparom/_search'
        self.path_dqt = '/dqt/query/es'

        self.uri = uri
        self.username = username
        self.password = password
        self.token = token
        self.pagesize = 250
        self.stale = False

        self.tls_verify = True

    @cache_region('search')
    def search(self, query, options=None):
        return self.search_real(query, options=options)

    def search_real(self, query, options=None):
        options = options or SmartBunch()

        options.setdefault('offset', 0)
        options.setdefault('limit', self.pagesize)
        options.setdefault('max_hits', self.search_max_hits)

        offset = options.offset
        limit  = options.limit
        transport = 'querystring'

        # Use DEPAROM Query Translator
        # https://depa.tech/api/manual/dqt-translator/
        # https://api.depa.tech/dqt/query/es
        query.setdefault('syntax', None)
        if query.expression and query.syntax == 'deparom':
            transport = 'json'
            query.expression = self.translate_deparom_query(query.expression)

        log.info(u"{backend_name}: searching documents, expression='{0}', offset={1}, limit={2}; user={username}".format(
            query.expression, offset, limit, **self.__dict__))

        starttime = timeit.default_timer()

        # Define search request URI
        # https://api.depa.tech/es/deparom/_search?q=AB:cloud-computing
        uri = self.uri + self.path_search

        # Define search request parameters
        # 'family.simple': True,
        params = {
            'q': query.expression,
            #'fq': query.filter,
            #'sort': 'pd desc, ucid asc',
            #'fl': 'ucid,fam',
            'from': offset, 'size': limit,
        }

        log.info(u'{backend_name}: query={query}, uri={uri}, params={params}, options={options}'.format(
            query=query, uri=uri, params=params, options=options.dump(), backend_name=self.backend_name))

        # Perform search request
        headers = {}
        headers.update({'Accept': 'application/json'})
        try:
            if transport == 'querystring':
                response = requests.get(
                    uri,
                    params=params,
                    headers=headers,
                    auth=(self.username, self.password),
                    verify=self.tls_verify)
            else:
                response = requests.post(
                    uri,
                    data=query.expression,
                    headers=headers,
                    auth=(self.username, self.password),
                    verify=self.tls_verify)
        except RequestException as ex:
            raise self.search_failed(
                ex=ex,
                user_info='Error or timeout while connecting to upstream database. Database might be offline.',
                meta={'username': self.username, 'uri': uri})
        duration = timeit.default_timer() - starttime

        # Process search response
        if response.status_code == 200:
            #print "response:", response.content        # debugging

            response_data = json.loads(response.content)
            if True:

                # Debugging: Simulate error
                #response_data['content']['error'] = {'code': 503, 'msg': 'no servers hosting shard'}

                # Mogrify search response
                # TODO: Generalize between all search backends
                sr = DepaTechSearchResponse(response_data, options=options)
                result = sr.render()
                duration = round(duration, 1)

                # TODO: Unify between IFI CLAIMS and depa.tech
                log.info('{backend_name}: Search succeeded. duration={duration}s, meta=\n{meta}'.format(
                    duration=duration, meta=result['meta'].prettify(), **self.__dict__))

                if not result['numbers']:
                    log.warn('{backend_name}: Search had empty results. duration={duration}s, meta=\n{meta}'.format(
                        duration=duration, meta=result['meta'].prettify(), **self.__dict__))

                return result

            #elif response_data['status'] == 'error':
            #    raise self.search_failed(response_data['message'], response=response)

            else:
                raise self.search_failed('Search response could not be parsed', response=response)

        elif response.status_code in [400, 500] and response.headers.get('Content-Type', '').startswith('application/json'):

            response_data = json.loads(response.content)

            # Handle search expression errors
            if 'error' in response_data:
                upstream_error = response_data['error']['caused_by']
                upstream_error['code'] = response_data['status']

                if 'reason' not in upstream_error:
                    upstream_error['reason'] = 'Reason unknown'

                message = u'Response status code: {code}\n\n{reason}'.format(**upstream_error)

                raise self.search_failed(
                    user_info=u'Error searching depa.tech.',
                    message=message,
                    response=response)

        raise self.search_failed(response=response)

    def translate_deparom_query(self, expression):
        uri = self.uri + self.path_dqt

        upstream_prefix = 'DEPAROM V1.0\n1\n'

        expression = expression.replace(upstream_prefix, '').replace('deparom:', '')

        log.info(u'{backend_name}: Translate DEPAROM query expression={expression}, uri={uri}'.format(
            expression=expression, uri=uri, backend_name=self.backend_name))

        expression = upstream_prefix + expression

        # Perform search request
        headers = {}
        headers.update({'Accept': 'application/json'})
        try:
            response = requests.post(
                uri,
                data=expression,
                headers=headers,
                auth=(self.username, self.password),
                verify=self.tls_verify,
            )
        except RequestException as ex:
            raise self.search_failed(
                ex=ex,
                user_info='Error or timeout while connecting to upstream database. Database might be offline.',
                meta={'username': self.username, 'uri': uri})

        # Process search response
        if response.status_code == 200:
            #print "response:", response.content        # debugging

            response_data = json.loads(response.content)
            result = {'query': response_data}
            return json.dumps(result)

        elif response.status_code >= 400:

            message = u'Reason unknown'

            if response.headers.get('Content-Type', '').startswith('application/json'):

                response_data = json.loads(response.content)

                # Handle search expression errors
                if 'error' in response_data:
                    upstream_error = response_data['error']['caused_by']
                    upstream_error['code'] = response_data['status']

                    if 'reason' not in upstream_error:
                        upstream_error['reason'] = u'Reason unknown'

                    message = u'Response status code: {code}\n\n{reason}'.format(**upstream_error)

            else:
                message = response.content

            raise self.search_failed(
                user_info=u'Translating DEPAROM query expression failed',
                message=message,
                response=response)

        raise self.search_failed(response=response)


class DepaTechSearchResponse(GenericSearchResponse):

    def read(self):

        #print 'input:', self.input

        # Read metadata
        """
        input:
        {
            "_shards": {
                "failed": 0,
                "successful": 5,
                "total": 5
            },
            "hits": {
                "hits": [
                    {
                        "_id": "DE.000202013003344.U1",
                        "_index": "deparom",
                        "_score": 13.234067,
                        "_source": {
                            "AB": "<p num=\"0000\">Rettungsensemble (1) mit Seilklemmen (2, 3), dadurch gekennzeichnet, dass es folgende, miteinander über einen Seilzug (4) verbundene Komponenten umfasst: <br/>– eine erste Seilklemme (2) mit wenigstens einer Umlenkrolle (21), zum verschieblichen Fixieren des Körpers des Benutzers an einem Seil; <br/>– eine zweite Seilklemme (3) mit wenigstens einer Umlenkrolle (31), zur verschieblichen Befestigung an dem Seil oberhalb der Position der ersten Seilklemme (2); wobei <br/>– der Seilzug (4) mit seinem einen Ende an der zweiten Seilklemme (3) oder einer ihrer Umlenkrollen (31) befestigt und in die Umlenkrollen der ersten und zweiten Seilklemme eingelegt ist, diese miteinander verbindet und zusammen mit diesen einen Flaschenzug bildet, und dessen anderes Ende frei hängt und zur Bedienung des Flaschenzugs vorgesehen ist.</p><p num=\"\"><de-figure num=\"0\"></de-figure></p>",
                            "AD": "20130410",
                            "AN": "DE202013003344",
                            "DE": "202013003344",
                            "DP": "20131205",
                            "GT": "Rettungsensemble zur Bergung aus Gletscherspalten",
                            "IC": [
                                "A63B",
                                "A63B0029",
                                "A63B002900"
                            ],
                            "KI": "U1",
                            "MC": [
                                "A63B",
                                "A63B0029",
                                "A63B002900"
                            ],
                            "NP": "CH64912",
                            "PA": "Mammut Sports Group AG, Seon, CH",
                            "PC": "DE",
                            "PD": "20120509",
                            "RN": "Bogensberger Patent- & Markenbüro, Eschen, LI"
                        },
                        "_type": "DEP"
                    }
                ],
                "max_score": 13.234067,
                "total": 1
            },
            "timed_out": false,
            "took": 7
        }
        """
        self.meta.upstream.update({
            'name': 'depatech',
            'time': self.input['took'],
            'status': 'success',
            #'params': SmartBunch.bunchify(self.input['content']['responseHeader']['params']),
            #'pager': SmartBunch.bunchify(self.input['content']['responseHeader'].get('pager', {})),
        })

        self.meta.navigator.count_total = int(self.input['hits']['total'])
        #self.meta.navigator.count_page  = int(self.meta.upstream.pager.entriesOnThisPage)
        self.meta.navigator.offset      = int(self.options.offset)
        self.meta.navigator.limit       = int(self.options.limit)
        self.meta.navigator.max_hits   = int(self.options.max_hits)
        self.meta.navigator.postprocess = SmartBunch()

        # Read content
        self.documents = self.input['hits']['hits']
        self.read_documents()

    def document_to_number(self, document):
        _id = document[u'_id']
        cc, docno, kindcode = _id.split('.')
        publication_number = cc + docno + kindcode
        number = normalize_patent(publication_number)
        return number

    def document_to_family_id(self, document):
        return document['fam']


def depatech_search(query, options=None):

    options = options or SmartBunch()

    client = get_depatech_client()
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
def depatech_crawl(constituents, query, chunksize, options=None):
    client = get_depatech_client()
    try:
        return client.crawl(constituents, query, chunksize)
    except SyntaxError as ex:
        log.warn('Invalid query for depa.tech: %s' % ex.msg)
        raise
