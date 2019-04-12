# -*- coding: utf-8 -*-
# (c) 2014-2015 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
import re
import sys
import json
import types
import logging
import urllib2
import mechanize
import cookielib
from BeautifulSoup import BeautifulSoup
from xlrd import open_workbook
from patzilla.access.generic.search import GenericSearchResponse
from patzilla.util.date import from_german, date_iso
from patzilla.util.network.browser import regular_user_agent
from patzilla.util.numbers.normalize import normalize_patent
from patzilla.util.python import _exception_traceback


"""
Screenscraper for DPMA DEPATISnet
https://depatisnet.dpma.de/
"""


logger = logging.getLogger(__name__)

class DpmaDepatisnetAccess:

    # values of these indexes will be considered keywords
    keyword_fields = [

        # DEPATISnet
        'ti', 'pa', 'in',
        'ab', 'de', 'cl', 'bi',

        # classes
        'ic', 'icb', 'icm', 'ics', 'ica', 'ici',
        'icmv', 'icsv', 'icav',
        'icml', 'icsl', 'ical',
        'mcd', 'mcm', 'mcs', 'mca', 'mcml', 'mcsl', 'mcal',
        'icp',

    ]

    def __init__(self):
        print 'DpmaDepatisnetAccess.__init__'
        self.baseurl = 'https://depatisnet.dpma.de/DepatisNet'
        self.searchurl_cql    = self.baseurl + '/depatisnet?action=experte&switchToLang=en'
        self.searchurl_ikofax = self.baseurl + '/depatisnet?action=ikofax&switchToLang=en'
        self.csvurl = self.baseurl + '/jsp2/downloadtrefferliste.jsp?&firstdoc=1'
        self.xlsurl = self.baseurl + '/jsp2/downloadtrefferlistexls.jsp?&firstdoc=1'
        self.hits_per_page = 250      # one of: 25, 50, 100, 250. [default: 50]
        self.search_max_hits = 10000  # one of: 100, 250, 500, 1000, 5000, 10000. [default: 1000]
        self.setup_browser()

    def setup_browser(self):

        # PEP 476: verify HTTPS certificates by default (implemented from Python 2.7.9)
        # https://bugs.python.org/issue22417
        if sys.hexversion >= 0x02070900:
            import ssl
            ssl._create_default_https_context = ssl._create_unverified_context

        # http://wwwsearch.sourceforge.net/mechanize/
        self.browser = mechanize.Browser()
        self.browser.set_cookiejar(cookielib.LWPCookieJar())
        self.browser.addheaders = [('User-Agent', regular_user_agent)]
        # ignore robots.txt
        self.browser.set_handle_robots(False)

    def logout(self):
        self.browser = None

    def search_patents(self, query, options=None):

        # search options
        options = options or {}

        # Set search range defaults.
        options.setdefault('limit', self.hits_per_page)
        options.setdefault('max_hits', self.search_max_hits)

        limit = options.get('limit')
        max_hits = options.get('max_hits')

        logger.info(u'Searching documents. query="%s", options=%s' % (query, options))

        # 0. create browser instance
        if not self.browser:
            self.setup_browser()

        # 1. Open search url
        search_url = self.searchurl_cql
        if options.get('syntax') == 'ikofax':
            search_url = self.searchurl_ikofax
        try:
            self.browser.open(search_url)
        except urllib2.HTTPError as ex:
            logger.critical('Hard error with DEPATISnet: {}'.format(ex))
            self.logout()
            raise

        # 2. submit form
        # http://wwwsearch.sourceforge.net/ClientForm/
        self.browser.select_form(nr=0)
        #self.browser.select_form(name='form')

        self.browser['query'] = query.encode('iso-8859-1')
        self.browser['hitsPerPage'] = [str(limit)]
        self.browser['maxHitsUser'] = [str(max_hits)]

        # turn on all fields
        # 2016-10-06: Field got disabled upstream
        #self.browser['DocId'] = ['on']      # Publication number
        self.browser['Ti'] = ['on']         # Title
        self.browser['In'] = ['on']         # Inventor
        self.browser['Pa'] = ['on']         # Applicant/Owner
        self.browser['Pub'] = ['on']        # Publication date
        self.browser['Ad'] = ['on']         # Application date
        #self.browser['Icp'] = ['on']        # IPC search file
        #self.browser['Icm'] = ['on']        # IPC main class

        # sort by publication date, descending
        #self.browser['sf'] = ['pd']
        #self.browser['so'] = ['desc']

        # sort by user selection
        if 'sorting' in options and type(options['sorting']) is types.DictionaryType:
            self.browser['sf'] = [options['sorting']['field']]
            self.browser['so'] = [options['sorting']['order']]

        # submit form
        response = self.browser.submit()

        # decode response
        body = response.read().decode('iso-8859-1')

        # hit count
        hits = 0

        # list of result entries
        results = []

        # check for error messages
        error_message = self.find_errors(body)

        # remove family members
        if 'feature_family_remove' in options:

            # push the button
            response = self.browser.follow_link(url_regex=re.compile("content=removefam"))

            # decode response
            body = response.read().decode('iso-8859-1')

            # check for error messages
            error_message = self.find_errors(body)

        # replace family members
        elif 'feature_family_replace' in options:

            # push the button
            response = self.browser.follow_link(url_regex=re.compile("content=replacefam"))

            # decode response
            body = response.read().decode('iso-8859-1')

            # check for error messages
            error_message = self.find_errors(body)


        # Collect result count

        # Total hits: 230175    A random selection of 1000 hits is being displayed.  You can narrow your search by adding more search criteria.
        matches = re.search('Total hits:&nbsp;(\d+)', error_message)
        if matches:
            hits = int(matches.group(1))

        # Result list: 42 hits
        matches = re.search('Result list:&nbsp;(\d+)&nbsp;hits', body)
        if matches:
            hits = int(matches.group(1))


        if 'did not match any documents' in body:
            #error_message = 'did not match any documents'
            pass

        else:
            logger.debug('DEPATISnet xlsurl: %s' % self.xlsurl)

            # Retrieve results via csv
            try:
                xls_response = self.browser.open(self.xlsurl)
                results = self.read_xls_response(xls_response)
            except Exception as ex:
                logger.error('Problem downloading results in XLS format: {}'.format(ex))
                ex.http_response = ex.read()
                raise

            # debugging
            #print 'results:', results

        upstream_response = {
            'hits': hits,
            'results': results,
            'query': query,
            'message': error_message,
        }

        options['normalize_fix_kindcode'] = True
        sr = DPMADepatisnetSearchResponse(upstream_response, options=options)
        result = sr.render()
        #print result.prettify()

        return result

    def find_errors(self, body):

        if body == '':
            self.logout()
            raise SyntaxError('Empty response from DPMA server. Please check your search criteria for syntax errors, '
                              'otherwise don\'t hesitate to report this problem to us.')

        # Check for error messages
        soup = BeautifulSoup(body)
        error_message = soup.find('div', {'class': 'error'})
        if error_message:
            parts = []
            [s.extract() for s in error_message('a')]
            [parts.append(s.extract()) for s in error_message('p', {'class': 'headline'})]
            reason = ', '.join([part.getText() for part in parts])
            error_message = u'{}\n{}'.format(reason, str(error_message))
        else:
            error_message = ''

        if u'An error has occurred' in body:
            error_message = error_message.replace('\t', '').replace('\r\n', '\n').strip()
            raise SyntaxError(error_message)

        return error_message

    def read_xls_response(self, xls_response):
        data = excel_to_dict(xls_response.read())
        results = []
        for row in data:
            #print 'row:', row
            if row:
                try:
                    item = {
                        'pubnumber': row['Publication number'],
                        'pubdate': row['Publication date'] and date_iso(from_german(row['Publication date'])) or None,
                        'appdate': row['Application date'] and date_iso(from_german(row['Application date'])) or None,
                        'title': row['Title'],
                        'applicant': row['Applicant/Owner'],
                        'inventor': row['Inventor'],
                    }
                except KeyError as ex:
                    logger.error('Could not decode row from DEPATISnet. row={row}, exception={exception}\n{trace}'.format(
                        row=row, exception=ex, trace=_exception_traceback()))
                    raise
                results.append(item)

        return results


class DPMADepatisnetSearchResponse(GenericSearchResponse):

    def read(self):

        # Read metadata
        """
        in:
        {
            'hits': 263,
            'results': [
                {'appdate': '2004-06-03',
                 'applicant': u'Rosemount Inc., Eden Prairie, Minn., US',
                 'inventor': u'...',
                 'pubdate': '2008-07-24',
                 'pubnumber': u'DE602004008910T2',
                 'title': u'[DE] FEHLERDIAGNOSEVORRICHTUNG UND -VERFAHREN BEI EINER PROZESSEINRICHTUNG UNTER VERWENDUNG EINES PROZESSABH\xc4NGIGEN SENSORSIGNALS'},
                {'appdate': '2014-05-14',
                 'applicant': u'Berkin B.V., Ruurlo, NL',
                 'inventor': u'',
                 'pubdate': '2014-08-28',
                 'pubnumber': u'DE202014102258U1',
                 'title': u'[DE] Str\xf6mungsmessvorrichtung zum Messen einer Str\xf6mung eines Mediums'},
                # ...
            ]
            'numbers': [u'DE602004008910T2',
                u'DE202014102258U1',
                u'DE112004002042T5',
                u'DE112004001503T5',
                # ...
            ]
            'query': u'(pc=DE) and (bi=vibrat?) and (ic=G01F1/84)',
            'message': 'Total hits:&nbsp;3283 &nbsp;&nbsp;  A random selection of&nbsp;1000&nbsp;hits is being displayed.',
        }
        """
        self.meta.upstream.update({
            'name': 'depatisnet',
            'query': self.input['query'],
            #'message': self.input['message'],
            # TODO: Reference from IFI CLAIMS, fill up/unify.
            #'time': self.input['time'],
            #'status': self.input['status'],
            #'params': SmartBunch.bunchify(self.input['content']['responseHeader']['params']),
            #'pager': SmartBunch.bunchify(self.input['content']['responseHeader'].get('pager', {})),
        })

        self.meta.navigator.count_total = int(self.input['hits'])
        self.meta.navigator.count_page  = len(self.input['results'])
        self.meta.navigator.max_hits    = int(self.options.max_hits)
        # TODO: Fill up?
        #self.meta.navigator.offset      = int(self.meta.upstream.Offset)
        #self.meta.navigator.limit       = int(self.meta.upstream.Limit)
        #self.meta.navigator.postprocess = SmartBunch()


        # Propagate user message
        if self.input['message']:
            self.output.navigator.user_info = {'message': self.input['message'], 'kind': 'warning'}


        # Read content
        """
        in:
        "results": [{
        }],
        """
        self.documents = self.input['results']
        self.read_documents()

    def document_to_number(self, document):
        number = document['pubnumber']
        return number

    def remove_family_members(self):
        """
        DPMA provides "Remove family members" upstream
        """
        pass


def excel_to_dict(payload):

    # http://stackoverflow.com/questions/23568409/xlrd-python-reading-excel-file-into-dict-with-for-loops/23568655#23568655

    book = open_workbook(file_contents=payload)
    sheet = book.sheet_by_index(0)

    start_row = 0

    # upstream added new status line to first row, e.g. "Search query: pn=(EP666666) Status: 25.09.2015"
    if u'Search query' in sheet.cell(0, 0).value:
        start_row = 1

    # read header values
    keys = [sheet.cell(start_row, col_index).value for col_index in xrange(sheet.ncols)]

    # read sheet content
    dict_list = []
    for row_index in xrange(start_row + 1, sheet.nrows):
        d = {keys[col_index]: sheet.cell(row_index, col_index).value
             for col_index in xrange(sheet.ncols)}
        dict_list.append(d)

    return dict_list


if __name__ == '__main__':

    logging.basicConfig()

    depatisnet = DpmaDepatisnetAccess()
    if len(sys.argv) > 1:
        data = depatisnet.search_patents(sys.argv[1])
        #data = depatisnet.search_patents(sys.argv[1], options={'feature_family_remove': True})

    else:
        data = depatisnet.search_patents('BI=bagger and PC=DE')

    print json.dumps(data)
