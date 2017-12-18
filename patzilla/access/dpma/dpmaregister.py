# -*- coding: utf-8 -*-
# (c) 2011,2014,2015,2017 Andreas Motl <andreas.motl@elmyra.de>
import re
import sys
import json
import time
import logging
import mechanize
from pprint import pformat
from collections import namedtuple, OrderedDict
from BeautifulSoup import BeautifulSoup
from patzilla.access.dpma.util import dpma_file_number


logger = logging.getLogger(__name__)


class DpmaRegisterAccess:
    """
    Screen scraper for DPMAregister "beginner's search" web interface
    https://register.dpma.de/DPMAregister/pat/einsteiger?lang=en

    Alternative direct link, e.g.
    https://register.dpma.de/DPMAregister/pat/experte/autoRecherche/de?queryString=AKZ%3D2020131020184
    https://register.dpma.de/DPMAregister/pat/experte/autoRecherche/de?queryString=EPN%3D666666
    https://register.dpma.de/DPMAregister/pat/experte/autoRecherche/de?queryString=PN%3DWO2008034638

    Todo:
    - Provide command line interface
    - Maybe switch to MechanicalSoup, see https://mechanicalsoup.readthedocs.io/
    - Improve response data chain
    - Decode ST.36 XML document
    - Introduce caching
    """

    baseurl = 'https://register.dpma.de/DPMAregister/pat/'

    ResultEntry = namedtuple('ResultEntry', ['label', 'reference'])
    Document = namedtuple('Document', ['result', 'url', 'html'])

    def __init__(self):

        # PEP 476: verify HTTPS certificates by default (implemented from Python 2.7.9)
        # https://bugs.python.org/issue22417
        if sys.hexversion >= 0x02070900:
            import ssl
            ssl._create_default_https_context = ssl._create_unverified_context

        # http://wwwsearch.sourceforge.net/mechanize/
        self.browser = mechanize.Browser()
        self.http_session_valid = False

        # Enable debug logging for "mechanize" module
        #self.browser.set_debug_http(True)

        # Set cookie jar
        #self.browser.set_cookiejar(cookielib.LWPCookieJar())

        # Set custom user agent header
        self.browser.set_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.112 Safari/537.36')

        # Ignore robots.txt, sorry for being rude.
        self.browser.set_handle_robots(False)

        self.language = 'en'
        self.searchurl = self.baseurl + 'einsteiger?lang={}'.format(self.language)
        self.accessurl = self.baseurl + 'register:showalleverfahrenstabellen?AKZ=%s&lang={}'.format(self.language)

        self.reference_pattern = re.compile('.*\?AKZ=(.+?)&.*')

    def start_http_session(self):
        if not self.http_session_valid:
            # 1. Open search url to initialize HTTP session
            response = self.browser.open(self.searchurl)
            self.http_session_valid = True

    def fetch(self, patent):
        document_intermediary = self.search_and_fetch(patent)
        if document_intermediary:
            document = DpmaRegisterDocument.from_result_document(document_intermediary)
            return document

    def search_first(self, patent):

        # 1. Search patent reference
        results = self.search_patent_smart(patent)

        # 2. Acquire page with register information
        # Remark: This just uses the first search result
        # TODO: Review this logic
        if results:
            return results[0]

    def search_and_fetch(self, patent):
        """
        search_entry = self.search_first(patent)
        if search_entry:
            return self.fetch_reference(search_entry)
        """
        file_reference = self.resolve_file_reference(patent)
        if file_reference:
            return self.fetch_reference(file_reference)

    def resolve_file_reference(self, patent):

        # Compute DPMA file number (Aktenzeichen) from DE publication/application number
        # by calculating the checksum of the document number.
        # This is a shortcut because we won't have to go through the search step.
        # It only works for DE applications, though.
        if patent.startswith('DE'):
            file_number = dpma_file_number(patent)
            result = self.ResultEntry(reference = file_number, label = patent)

        # For all other numbers, we have to kick off
        # a search request and scrape the response.
        else:
            result = self.search_first(patent)

        if result:
            logger.info('DPMA file number for {} is {}'.format(patent, result.reference))
        else:
            logger.warning('Could not resolve DPMA file number for {}'.format(patent))

        return result

    def get_document_url(self, patent):

        file_reference = self.resolve_file_reference(patent)
        url = self.accessurl % file_reference.reference
        logger.info('Document URL for {} is {}'.format(patent, url))
        return url

    def fetch_st36xml(self, patent):

        # Fetch main HTML resource of document
        result = self.search_and_fetch(patent)

        if not result:
            logger.warning('Could not find document {}'.format(patent))
            return

        # Parse link to ST.36 XML document from HTML
        soup = BeautifulSoup(result.html)
        st36xml_anchor = soup.find("a", {'name': 'st36xml'})
        st36xml_href = st36xml_anchor['href']

        # Download ST.36 XML document and return response body
        return self.browser.open(st36xml_href).read()

    def fetch_pdf(self, patent):

        # Fetch main HTML resource of document
        result = self.search_and_fetch(patent)

        if not result:
            logger.warning('Could not find document {}'.format(patent))
            return

        # Derive mechanize request from link to ST.36 XML document from HTML
        request = self.browser.click_link(url_regex='register/PAT_.*VIEW=pdf')

        # Download ST.36 XML document and return response body
        return self.browser.open(request).read()

    def search_patent_smart(self, patent):

        patent = patent.upper()

        # 1. search patent reference for direct download
        results = self.search_patent(patent)
        #print results

        # reduce result list by applying certain rules for guessing the right one
        # just gets applied when getting multiple results
        if results and len(results) > 1:
            if patent.startswith('DE'):
                results = [result for result in results if not result.reference.startswith('E')]
            if patent.startswith('WO'):
                results = [result for result in results if result.label.startswith('PCT')]

        errmsg = None
        if not results:
            errmsg = "Search result for '%s' is empty" % (patent)
        elif len(results) >= 2:
            errmsg = "Search result for '%s' is ambiguous: count=%s, results=%s" % (patent, len(results), results)

        if errmsg:
            logger.warning(errmsg)
            #raise Exception(errmsg)

        return results

    def search_patent(self, patent):

        logger.info("Searching document(s), patent='%s'" % patent)

        # 1. Open search url to initialize HTTP session
        self.start_http_session()

        # 2017-12-18: The DPMA seems to have put a throttling machinery in place by
        # means of the "reg.check" cookie, e.g. "reg.check1239723693=-853246121".
        # Let's honor this by also throttling the client. Otherwise, the response
        # might contain a valid result list but containing zero results.
        time.sleep(0.75)

        # Debugging
        #self.dump_response(response, dump_metadata=True)
        #sys.exit()


        # 2. Send inquiry

        # Fill form fields
        # http://wwwsearch.sourceforge.net/ClientForm/
        #self.browser.select_form(name='form')
        self.browser.select_form(nr=0)

        # Aktenzeichen or publication number
        self.browser.form['akzPn'] = patent

        # Simulate another form field set by Tapestry in Javascript
        self.browser.form.new_control('text', 't:submit', {})
        self.browser.form['t:submit'] = '["rechercheStarten","rechercheStarten"]'

        # Submit form
        response = self.browser.submit()

        # Debugging
        #self.dump_response(response, dump_metadata=True)
        #sys.exit()


        # 3. Evaluate response

        # 2013-05-11: The DPMA changed the HTTP interface: Searching now jumps
        # directly to the result detail page if there's just a single result.
        # Honor this by parsing the file number (Aktenzeichen) from the
        # response HTML and making up a single result from that.
        url = self.browser.geturl()
        if '/pat/register' in url:
            soup = BeautifulSoup(response)
            reference_link = soup.find('a', {'href': self.reference_pattern})
            reference, label = self.parse_reference_link(reference_link, patent)
            entry = self.ResultEntry(reference = reference, label = None)
            return [entry]

        html_searchresult = response.read() #.decode('utf-8')

        # Sanity checks
        if 'div class="error"' in html_searchresult:
            logger.warning("No search results for '%s'" % patent)
            return []


        # 4. Parse result table
        results = []

        soup = BeautifulSoup(html_searchresult)
        result_table = soup.find("table")
        for row in result_table.findAll('tr'):
            columns = row.findAll('td')
            if not columns: continue
            link_column = columns[2]
            if not link_column: continue
            link = link_column.find('a')

            reference, label = self.parse_reference_link(link, patent)
            entry = self.ResultEntry(reference = reference, label = label)
            results.append(entry)

        logger.info("Searching for %s yielded %s results" % (patent, len(results)))

        return results

    def parse_reference_link(self, link, patent):
        m = self.reference_pattern.match(link['href'])
        if m:
            reference = m.group(1)
        else:
            msg = "Could not parse document reference from link '%s' (patent='%s')" % (link, patent)
            logger.error(msg)
            raise Exception(msg)
        label = link.find(text=True)
        return reference, label

    def fetch_reference(self, result):
        """open document url and return html"""

        # 1. Open search url to initialize HTTP session
        self.start_http_session()

        url = self.accessurl % result.reference
        logger.info('Accessing URL {}'.format(url))
        html_document = self.browser.open(url).read() #.decode('utf-8')
        return self.Document(result = result, url = url, html = html_document)

    def dump_response(self, response, dump_metadata = False):
        """
        Dump response from "mechanize". Metadata and body.
        """
        #print dir(response)
        #print br.title()
        if dump_metadata:
            print response.geturl()
            print response.info()  # headers
        print response.read()  # body


class DpmaRegisterDocument(object):
    """
    Decode information from DPMAregister HTML response.
    """

    def __init__(self, identifier, html=None, url=None):

        self.identifier = identifier
        self.html = html
        self.url = url

        self.biblio = None
        self.events = None

        # Link to local CSS file
        self.link_css = './assets/dpmabasis_d.css'

    @classmethod
    def from_result_document(cls, doc):
        return cls(doc.result.reference, html=doc.html, url=doc.url)

    def __str__(self):
        return str(self.identifier) + ':\n' + pformat(self.events)

    def html_compact(self):
        """
        Strip all HTML information just leaving the tables containing register information.

        TODO: insert link to original document, insert link to pdf
        <a shape="rect" class="button" target="_blank" href="register?AKZ=100068189&amp;VIEW=pdf">PDF-Download</a>
        """

        soup = BeautifulSoup(self.html)

        # propagate Content-Type
        soup_content_type = soup.find('meta', {'http-equiv': 'Content-Type'})

        # FIX for BeautifulSoup
        if soup_content_type['content'] == 'Content-Type':
            soup_content_type['content'] = 'text/html; charset=UTF-8'

        soup_content = soup.find('div', {'id': 'inhalt'})

        # remove some tags
        remove_stuff = [
            ('div', {'class': 'objektblaettern'}),
            ('a', {'class': 'button'}),
            ('br', {'clear': 'none'}),
            ('div', {'class': 'clearer'}),
            ('p', {'style': 'clear:both'}),
            ('div', {'class': 't-invisible'}),
            ('div', {'class': 'regauskunft'}),
            ('a', {'href': re.compile('^./register:hideverfahrenstabelle.*')}),
            ('a', {'class': 'hidden'}),
        ]
        [[tag.extract() for tag in soup_content.findAll(item[0], item[1])] for item in remove_stuff]

        # <a href="./PatSchrifteneinsicht
        # <a shape="rect" href="./register:sortVerfahrensUebersicht

        # manipulate some links
        for link in soup.findAll('a', {'href': re.compile('^./PatSchrifteneinsicht.*')}):
            link['href'] = DpmaRegisterAccess.baseurl + link['href']
            if link.img:
                link.img.extract()

        for link in soup.findAll('a', {'href': re.compile('^./register.*')}):
            if link.contents:
                link.replaceWith(link.contents[0])

        document_source_link = str(self.url)
        css_local_link = self.link_css

        tpl = """
<html>
    <head>
        %(soup_content_type)s
        <link type="text/css" rel="stylesheet" href="%(css_local_link)s"/>
        <style type="text/css"><!-- ins {background: #bfb} del{background: #fcc} ins,del {text-decoration: none} --></style>
    </head>
    <body id="body">
        <div id="sourcelinkbox" align="left" style="padding: 10px">
            Quelle:
            <a href="%(document_source_link)s" target="_blank">HTML</a>,
            <a href="%(document_source_link)s&VIEW=pdf" target="_blank">PDF</a>
        </div>
        %(soup_content)s
    </body>
</html>
""".strip()

        # render
        html_stripped = tpl % locals()

        # fixup
        html_stripped = html_stripped.replace('Verfahrensansicht \xc2\xa0 \xc2\xa0', '')

        return html_stripped

    def asdict(self):
        self.parse_html()
        payload = OrderedDict()
        payload['biblio'] = self.biblio
        payload['events'] = self.events
        return payload

    def asjson(self):
        return json.dumps(self.asdict(), indent=4)

    def parse_html(self):
        """
        parse document results from html tables
        FIXME: unfinished!
        """
        soup = BeautifulSoup(self.html)
        soup_table_basicdata = soup.find("table")
        soup_table_legaldata = soup_table_basicdata.findNextSibling("table")

        self.biblio = self.soup_parse_table(soup_table_basicdata, header_row_index = 1)
        self.events = self.soup_parse_table(soup_table_legaldata, header_row_index = 1)

    def soup_parse_table(self, soup_table, contains_header = True, header_row_index = 0, header_tag = 'th'):

        table = []
        header_columns = []

        rows = soup_table.findAll('tr')

        # 1. find header columns
        if contains_header:
            header_row = rows[header_row_index]
            #header_columns = [header_column.contents[0] for header_column in header_row.findAll(header_tag)]
            header_columns = header_row.findAll(header_tag, text=True)
            rows = rows[header_row_index+1:]
            #print rows

        #print header_columns

        # 2. grep data area
        Cell = namedtuple('Cell', ['name', 'value'])
        for soup_data_row in rows:
            data_row = []
            for index, values in enumerate(soup_data_row.findAll('td')):
                #print index, value
                name = header_columns[index]
                cell = Cell(name, [value.replace('&nbsp;', '').strip() for value in values.findAll(text=True)])
                data_row.append(cell)
            table.append(data_row)

        return table


if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO)

    register = DpmaRegisterAccess()

    document = None
    if len(sys.argv) > 1:
        document = register.fetch(sys.argv[1])

    else:
        #document = register.fetch('10001499.2')     # leads to two results, take the non-"E" one
        document = register.fetch('DE3831719')      # search and follow to 3831719.2
        #document = register.fetch('WO2007037298')   # worked with DPINFO only
        #document = register.fetch('WO2008034638')   # leads to two results, take the non-"E" one
        #document = register.fetch('DE102006006014') # just one result, directly redirects to detail page

        #document = register.fetch('DE19630877')
        #document = register.fetch('DE102012009645')
        #document = register.fetch('EP666666')

        #print register.get_document_url('10001499.2')
        #print register.get_document_url('DE10001499.2')
        #print register.get_document_url('DE10001499')
        #print register.get_document_url('DE102012009645')

        #print register.fetch_st36xml('DE10001499')
        #print register.fetch_st36xml('EP666666')
        #print register.fetch_st36xml('10001499.2')

        #print register.fetch_pdf('10001499.2')
        #print register.fetch_pdf('DE10001499')

    if document:
        print document.html_compact()
        #print document.asdict()
        #print document.asjson()
