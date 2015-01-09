# -*- coding: utf-8 -*-
# (c) 2014 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
import re
import csv
import sys
import logging
import mechanize
import cookielib
from BeautifulSoup import BeautifulSoup
from elmyra.ip.util.numbers.normalize import normalize_patent


"""
Screenscraper for DPMA DEPATISnet
https://depatisnet.dpma.de/
"""


logger = logging.getLogger(__name__)

class DpmaDepatisnetAccess:

    def __init__(self):
        # http://wwwsearch.sourceforge.net/mechanize/
        self.browser = mechanize.Browser()
        self.browser.set_cookiejar(cookielib.LWPCookieJar())
        self.browser.addheaders = [('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1790.0 Safari/537.36')]
        # ignore robots.txt
        self.browser.set_handle_robots(False)

        self.baseurl = 'https://depatisnet.dpma.de/DepatisNet'
        self.searchurl = self.baseurl + '/depatisnet?action=experte&switchToLang=en'
        self.csvurl = self.baseurl + '/jsp2/downloadtrefferliste.jsp?&firstdoc=1'
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
            #error_message = 'did not match any documents'

        else:

            csv_response = self.browser.open(self.csvurl)
            #csv = csv_response.read().decode('latin-1')
            #print "csv:", csv

            results = self.csv_parse_publication_numbers(csv_response)

            results = [normalize_patent(result, fix_kindcode=True) or result for result in results]


        payload = {
            'query': query,
            'numbers': results,
            'hits': hits,
            'message': error_message,
        }
        return payload


    def csv_parse_publication_numbers(self, csv_response):
        csvreader = csv.reader(csv_response, delimiter=';')
        results = []
        for row in csvreader:
            #print row
            if row:
                publication_number = row[0]
                #print 'publication_number:', publication_number
                results.append(publication_number)

        if results:
            results = results[1:]

        return results


if __name__ == '__main__':

    logging.basicConfig()

    depatisnet = DpmaDepatisnetAccess()
    if len(sys.argv) > 1:
        data = depatisnet.search_patents(sys.argv[1])

    else:
        data = depatisnet.search_patents('BI=bagger and PC=DE')

    print data
