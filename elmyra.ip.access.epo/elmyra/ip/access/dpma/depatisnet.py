# -*- coding: utf-8 -*-
# (c) 2014 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
import csv
import sys
import logging
import mechanize
import cookielib


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
        self.searchurl = self.baseurl + '/depatisnet?action=experte'
        self.csvurl = self.baseurl + '/jsp2/downloadtrefferliste.jsp?&firstdoc=1'


    def search_patents(self, query):

        logger.info("searching documents, query='%s'" % query)

        # 1. open search url
        response_searchform = self.browser.open(self.searchurl)

        # 2. submit form
        # http://wwwsearch.sourceforge.net/ClientForm/
        self.browser.select_form(nr=0)
        #self.browser.select_form(name='form')
        self.browser['query'] = query
        response = self.browser.submit()


        # TODO: check for errors like...
        """
        Beim Überprüfen Ihrer Expertensuchanfrage ist ein Fehler aufgetreten.

        Fehlercode: 1203 - Das Suchfeld ist nicht bekannt
        Fehlerposition: 1
        BIA=bagger and PC=DE
        """

        csv_response = self.browser.open(self.csvurl)
        #csv = csv_response.read().decode('latin-1')
        #print "csv:", csv

        results = self.csv_parse_publication_numbers(csv_response)
        return results


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
            return results[1:]


if __name__ == '__main__':

    logging.basicConfig()

    depatisnet = DpmaDepatisnetAccess()
    if len(sys.argv) > 1:
        data = depatisnet.search_patents(sys.argv[1])

    else:
        data = depatisnet.search_patents('BI=bagger and PC=DE')

    print data
