# -*- coding: utf-8 -*-
# (c) 2014-2015 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
import re
import csv
import sys
import logging
import mechanize
import cookielib
import codecs
import HTMLParser
from StringIO import StringIO
from BeautifulSoup import BeautifulSoup
from elmyra.ip.util.date import from_german, date_iso
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

            csv_response = self.browser.open(self.csvurl)
            #csv = csv_response.read().decode('latin-1')
            #csv_response.seek(0)
            #print "csv:", csv

            # read and decode payload
            payload = csv_response.read()
            payload = payload.decode('iso-8859-1')

            # replace html entities I
            # pc=(de) and ic=(A45D34/00) and py >= 1990 and py <= 1994
            # Kušnir, Elena Vladimir, Kievskaya oblast', Borispolsky, SU Kušnir, Vladimir Markovič
            # Ukrainskij naučno-issledovatel'skij institut po plemennomu delu v životnovodstve "Ukrniiplem", Kievskaja oblast', SU
            # Ku&scaron;nir => Kušnir
            # Markovi&ccaron; => Markovič
            # &zcaron;ivotnovodstve => životnovodstve
            payload = payload.replace(u'&ccaron;', u'č')
            payload = payload.replace(u'&zcaron;', u'ž')

            # replace html entities II
            # http://fredericiana.com/2010/10/08/decoding-html-entities-to-text-in-python/
            #payload = payload.replace('&amp;', '&')
            #payload = payload.replace('&nbsp;', ' ')
            #payload = re.sub('&([^;]+);', lambda m: unichr(htmlentitydefs.name2codepoint[m.group(1)]), payload, re.MULTILINE)
            htmlparser = HTMLParser.HTMLParser()
            payload = htmlparser.unescape(payload).encode('utf-8')

            # convert manipulated payload back to stream
            csv_response = StringIO(payload)

            # parse csv data
            results = self.csv_parse_publication_numbers(csv_response)
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


    def csv_parse_publication_numbers(self, csv_response):
        #print 'csv_response:', csv_response.read()
        #csv_response.seek(0)
        csvreader = FieldStrippingDictReader(csv_response, delimiter=';', encoding='utf-8')
        results = []
        for row in csvreader:
            #print 'row:', row
            if row:
                item = {
                    'pubnumber': normalize_patent(row['Publication number']),
                    'pubdate': row['Publication date'] and date_iso(from_german(row['Publication date'])) or None,
                    'appdate': row['Application date'] and date_iso(from_german(row['Application date'])) or None,
                    'title': row['Title'],
                    'applicant': row['Applicant/Owner'],
                    'inventor': row['Inventor'],
                }
                results.append(item)

        return results

class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    https://docs.python.org/2/library/csv.html#examples
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")

class UnicodeDictReader(csv.DictReader):
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    https://docs.python.org/2/library/csv.html#examples
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        csv.DictReader.__init__(self, f, dialect=dialect, **kwds)

    def next(self):
        row = csv.DictReader.next(self)
        for key, value in row.iteritems():
            #print 'value:', value
            row[key] = unicode(value, "utf-8")
        return row

    def __iter__(self):
        return self

class FieldStrippingDictReader(UnicodeDictReader):

    @property
    def fieldnames(self):
        if self._fieldnames is None:
            try:
                self._fieldnames = self.reader.next()
                self._fieldnames = map(str.strip, self._fieldnames)
            except StopIteration:
                pass
        self.line_num = self.reader.line_num
        return self._fieldnames

    def next(self):
        data = UnicodeDictReader.next(self)
        for key, value in data.iteritems():
            data[key] = value.strip()
        return data

if __name__ == '__main__':

    logging.basicConfig()

    depatisnet = DpmaDepatisnetAccess()
    if len(sys.argv) > 1:
        data = depatisnet.search_patents(sys.argv[1])

    else:
        data = depatisnet.search_patents('BI=bagger and PC=DE')

    print data
