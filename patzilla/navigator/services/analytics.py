# -*- coding: utf-8 -*-
# (c) 2013-2018 Andreas Motl <andreas.motl@ip-tools.org>
import logging
import datetime
import operator
import HTMLParser
from arrow.arrow import Arrow
from cornice.service import Service
from dateutil.relativedelta import relativedelta
from jsonpointer import JsonPointer
from transitions.core import Machine
from patzilla.access.epo.ops.api import analytics_family, ops_published_data_search, _result_list_compact
from patzilla.access.sip.client import sip_published_data_search, sip_published_data_crawl
from patzilla.navigator.services.dpma import dpma_published_data_search
from patzilla.navigator.services.util import make_expression_filter

log = logging.getLogger(__name__)


analytics_family_service = Service(
    name='analytics-applicant-family',
    path='/api/analytics/family/overview',
    renderer='prettyjson',
    description="Family analytics interface")

@analytics_family_service.get()
def analytics_family_handler(request):
    # TODO: respond with proper 4xx codes if something fails

    # decode query parameters into datasource and criteria
    expression_data = _decode_expression_from_query(request)

    query = make_expression_filter({
        'datasource': expression_data.get('datasource', 'ops'),
        'format': 'comfort',
        'criteria': expression_data['criteria'],
    })['expression']

    response = analytics_family(query)
    return response



analytics_daterange_service = Service(
    name='analytics-daterange',
    path='/api/analytics/daterange/{kind}',
    renderer='prettyjson',
    description="Daterange analytics interface")

@analytics_daterange_service.get()
def analytics_daterange_handler(request):
    # TODO: respond with proper 4xx codes if something fails

    kind = request.matchdict['kind'].lower()

    # decode query parameters into datasource and criteria
    expression_data = _decode_expression_from_query(request)

    response = analytics_daterange(expression_data['datasource'], kind, expression_data['criteria'])
    return response

def _decode_expression_from_query(request):
    # decode query parameters into datasource and criteria
    decoded = {}
    params = dict(request.params)
    if params.has_key('datasource'):
        decoded['datasource'] = params['datasource'].lower()
        del params['datasource']
    decoded.update({'criteria': params})
    return decoded

class QueryDateRangeNarrower(object):

    states = ['init', 'whole', 'left', 'right', 'finished', 'asleep']
    OLDEST = 1
    NEWEST = 2

    def __init__(self, datasource, criteria, kind):

        self.datasource = datasource
        self.criteria = criteria
        self.kind = kind

        self.maxcount = 50
        self.hits = -1

        self.querycount = 0

        self.machine = Machine(model=self, states=QueryDateRangeNarrower.states, initial='asleep')

        self.machine.add_transition('start', '*',     'init', after='work')
        self.machine.add_transition('check', '*',     'finished', conditions=['is_ready'])
        self.machine.add_transition('step',  'init',  'finished', conditions='is_century_out_of_bounds')
        self.machine.add_transition('step',  'init',  'whole',  after=['runquery', 'check'])
        self.machine.add_transition('step',  'whole', 'init',  conditions='no_hits', after='range_next_century')


        if self.kind == self.OLDEST:
            self.date_from = Arrow.fromdatetime(datetime.datetime(1800, 01, 01))
            self.date_to   = Arrow.fromdatetime(datetime.datetime(1899, 12, 31))
            self.factor    = +1

            self.machine.add_transition('step',  'whole', 'left',  unless='is_ready', after=['range_whole_left', 'runquery', 'check'])
            self.machine.add_transition('step',  'left',  'right', conditions='no_hits', after=['range_left_right', 'runquery', 'check'])
            self.machine.add_transition('step',  'left',  'whole', unless='is_ready', after=['range_shrink'])
            self.machine.add_transition('step',  'right', 'whole', unless='is_ready', after=['range_shrink'])

        elif self.kind == self.NEWEST:
            self.date_from = Arrow.fromdatetime(datetime.datetime(2000, 01, 01))
            self.date_to   = Arrow.utcnow()
            self.date_to   += relativedelta(months=12-self.date_to.month, days=31-self.date_to.day)
            self.factor    = -1

            self.machine.add_transition('step',  'whole', 'right',  unless='is_ready', after=['range_whole_right', 'runquery', 'check'])
            self.machine.add_transition('step',  'right',  'left', conditions='no_hits', after=['range_right_left', 'runquery', 'check'])
            self.machine.add_transition('step',  'right',  'whole', unless='is_ready', after=['range_shrink'])
            self.machine.add_transition('step',  'left', 'whole', unless='is_ready', after=['range_shrink'])

        else:
            raise ValueError('kind must be self.OLDEST or self.NEWEST')

        self.delta = (self.date_to - self.date_from) / 2


    def runquery(self):
        criteria = self.criteria.copy()
        criteria['pubdate'] = u'within {date_from},{date_to}'.format(
                         date_from=self.date_from.format('YYYY-MM-DD'), date_to=self.date_to.format('YYYY-MM-DD'))

        query = make_expression_filter({
            'datasource': self.datasource,
            'format': 'comfort',
            'criteria': criteria,
        })['expression']

        if self.datasource == 'ops':
            self.response, self.hits = query_ops(query, limit=self.maxcount)

        elif self.datasource == 'depatisnet':
            self.response, self.hits = query_depatisnet(query, limit=self.maxcount)

        elif self.datasource == 'sip':
            self.response, self.hits = query_sip(query, limit=self.maxcount)

        else:
            raise ValueError('Data source "{0}" not implemented'.format(self.datasource))

        self.querycount += 1

    def no_hits(self):
        return self.hits == 0

    def is_ready(self):
        return self.hits > 0 and self.hits <= self.maxcount


    # for "oldest" searches
    def range_whole_left(self):
        self.date_to -= self.delta

    def range_left_right(self):
        self.date_from += self.delta
        self.date_to   += self.delta


    # for "newest" searches
    def range_whole_right(self):
        self.date_from += self.delta

    def range_right_left(self):
        self.date_from -= self.delta
        self.date_to   -= self.delta


    def range_shrink(self):
        self.delta /= 2

    def range_next_century(self):

        century = self.date_from.year / 100
        century += self.factor

        year_begin = century * 100 + 00
        year_end   = century * 100 + 99

        self.date_from += relativedelta(
            years   = year_begin - self.date_from.year,
            months  = -self.date_from.month + 1,
            days    = -self.date_from.day + 1)
        self.date_to   += relativedelta(
            years   = year_end - self.date_to.year,
            months  = 12 - self.date_to.month,
            days    = 31 - self.date_to.day)

    def is_century_out_of_bounds(self):
        return self.date_from.year > Arrow.utcnow().year or self.date_to.year < 1800

    def work(self):
        debug = False
        while True:
            if debug:
                print '-' * 42
                print 'state:', self.state
                print 'delta:', self.delta
                print 'querycount:', self.querycount
            if self.state == 'finished' or self.querycount > 15:
                break
            self.step()


def analytics_daterange(datasource, kind, criteria):

    fsm_kind = QueryDateRangeNarrower.NEWEST
    if kind == 'oldest':
        fsm_kind = QueryDateRangeNarrower.OLDEST

    fsm = QueryDateRangeNarrower(datasource, criteria, fsm_kind)
    fsm.start()

    #print 'state:', fsm.state
    #print 'hits:', fsm.hits
    #print 'response:', fsm.response

    items = []
    sort_field = None
    if fsm.datasource == 'ops':
        items = _result_list_compact(fsm.response)
        sort_field = 'pubdate'

    elif fsm.datasource == 'depatisnet':
        items = fsm.response['results']
        sort_field = 'pubdate'

    elif fsm.datasource == 'sip':
        items = fsm.response['details']
        sort_field = 'Priority'

    else:
        raise ValueError('Data source "{0}" not implemented'.format(fsm.datasource))

    items = sorted(items, key=operator.itemgetter(sort_field))
    if fsm.kind == QueryDateRangeNarrower.NEWEST:
        items = list(reversed(items))

    return items



def query_ops(query, limit=50):
    #print 'query:', query
    response = ops_published_data_search('biblio', query, '1-{0}'.format(limit))
    #print response

    pointer_total_count = JsonPointer('/ops:world-patent-data/ops:biblio-search/@total-result-count')
    total_count = int(pointer_total_count.resolve(response))
    log.info('query: %s, total_count: %s', query, total_count)

    return response, total_count

def query_depatisnet(query, limit=50):
    response = dpma_published_data_search(query, limit)
    log.info('query: %s, total_count: %s', query, response['hits'])
    return response, response['hits']

def query_sip(query, limit=50):
    response = sip_published_data_search(query, {'offset': 1, 'limit': limit})
    total_count = int(response['meta']['MemCount'])
    log.info('query: %s, total_count: %s', query, total_count)
    return response, total_count




analytics_applicants_distinct_service = Service(
    name='analytics-applicants-distinct',
    path='/api/analytics/applicants-distinct',
    renderer='prettyjson',
    description='Applicants distinct analytics interface')

@analytics_applicants_distinct_service.get()
def analytics_applicants_distinct_handler(request):
    # TODO: respond with proper 4xx codes if something fails

    # decode query parameters into datasource and criteria
    expression_data = _decode_expression_from_query(request)

    query = make_expression({
        'datasource': 'sip',
        'format': 'comfort',
        'criteria': expression_data['criteria'],
    })

    results = sip_published_data_crawl('biblio', query, 2500)
    #print 'results:', results

    applicants = {}
    htmlparser = HTMLParser.HTMLParser()
    for item in results['details']:
        applicant = item.get('applicant')
        if applicant:
            applicant = htmlparser.unescape(applicant)
        applicants.setdefault(applicant, 0)
        applicants[applicant] += 1

    response = applicants
    return response
