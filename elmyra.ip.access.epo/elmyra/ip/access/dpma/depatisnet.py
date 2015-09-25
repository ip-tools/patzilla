# -*- coding: utf-8 -*-
# (c) 2014-2015 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
import re
import sys
import logging
import mechanize
import cookielib
from BeautifulSoup import BeautifulSoup
from xlrd import open_workbook
from elmyra.ip.util.date import from_german, date_iso
from elmyra.ip.util.numbers.normalize import normalize_patent
from elmyra.ip.util.python import _exception_traceback


"""
Screenscraper for DPMA DEPATISnet
https://depatisnet.dpma.de/
"""


logger = logging.getLogger(__name__)

class DpmaDepatisnetAccess:

    def __init__(self):

        # PEP 476: verify HTTPS certificates by default (implemented from Python 2.7.9)
        # https://bugs.python.org/issue22417
        if sys.hexversion >= 0x02070900:
            import ssl
            ssl._create_default_https_context = ssl._create_unverified_context

        # http://wwwsearch.sourceforge.net/mechanize/
        self.browser = mechanize.Browser()
        self.browser.set_cookiejar(cookielib.LWPCookieJar())
        self.browser.addheaders = [('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1790.0 Safari/537.36')]
        # ignore robots.txt
        self.browser.set_handle_robots(False)

        self.baseurl = 'https://depatisnet.dpma.de/DepatisNet'
        self.searchurl = self.baseurl + '/depatisnet?action=experte&switchToLang=en'
        self.csvurl = self.baseurl + '/jsp2/downloadtrefferliste.jsp?&firstdoc=1'
        self.xlsurl = self.baseurl + '/jsp2/downloadtrefferlistexls.jsp?&firstdoc=1'
        self.hits_per_page = 250      # one of: 10, 25, 50 (default), 100, 250, 1000


    def search_patents(self, query, hits_per_page=None):

        hits_per_page = hits_per_page or self.hits_per_page

        logger.info("DEPATISnet: searching documents, query='%s', hits_per_page='%s'" % (query, hits_per_page))

        # 1. open search url
        response_searchform = self.browser.open(self.searchurl)

        # 2. submit form
        # http://wwwsearch.sourceforge.net/ClientForm/
        self.browser.select_form(nr=0)
        #self.browser.select_form(name='form')

        self.browser['query'] = query.encode('iso-8859-1')
        self.browser['hitsPerPage'] = [str(hits_per_page)]

        # turn on all fields
        self.browser['DocId'] = ['on']      # Publication number
        self.browser['Ti'] = ['on']         # Title
        self.browser['In'] = ['on']         # Inventor
        self.browser['Pa'] = ['on']         # Applicant/Owner
        self.browser['Pub'] = ['on']        # Publication date
        self.browser['Ad'] = ['on']         # Application date
        #self.browser['Icp'] = ['on']        # IPC search file
        #self.browser['Icm'] = ['on']        # IPC main class

        # sort by publication date, descending
        self.browser['sf'] = ['pd']
        self.browser['so'] = ['desc']

        response = self.browser.submit()

        # propagate error- and info-messages
        body = response.read().decode('iso-8859-1')
        #print response.info(); print 'body:', body
        if body == '':
            raise SyntaxError('Empty response from server')

        soup = BeautifulSoup(body)
        error_message = soup.find('div', {'class': 'error'})
        if error_message:
            [s.extract() for s in error_message('a')]
            [s.extract() for s in error_message('p', {'class': 'headline'})]
            error_message = str(error_message)
        else:
            error_message = ''

        if 'An error has occurred' in body:
            raise SyntaxError(error_message)


        # parse hit count
        hits = 0

        # Result list: 52 hits
        #
        matches = re.search('Result list:&nbsp;(\d+)&nbsp;hits', body)
        if matches:
            hits = int(matches.group(1))

        # Total hits: 230175    A random selection of 1000 hits is being displayed.  You can narrow your search by adding more search criteria.
        matches = re.search('Total hits:&nbsp;(\d+)', error_message)
        if matches:
            hits = int(matches.group(1))


        # retrieve results via csv

        if 'did not match any documents' in body:
            results = []
            numbers = []
            #error_message = 'did not match any documents'

        else:
            xls_response = self.browser.open(self.xlsurl)
            results = self.read_xls_response(xls_response)
            #print 'results:', results

            # normalize patent numbers
            numbers = [normalize_patent(result['pubnumber'], fix_kindcode=True) or result for result in results]


        payload = {
            'hits': hits,
            'results': results,
            'numbers': numbers,
            'query': query,
            'message': error_message,
        }
        return payload


    def read_xls_response(self, xls_response):
        data = excel_to_dict(xls_response.read())
        results = []
        for row in data:
            #print 'row:', row
            if row:
                try:
                    item = {
                        'pubnumber': normalize_patent(row['Publication number']),
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

    else:
        data = depatisnet.search_patents('BI=bagger and PC=DE')

    print data
