# -*- coding: utf-8 -*-
# (c) 2011,2014,2015 Andreas Motl <andreas.motl@elmyra.de>
import sys
import re
import logging
from pprint import pformat
from collections import namedtuple
import mechanize
import cookielib
from BeautifulSoup import BeautifulSoup


"""
Screenscraper for DPMAregister
http://register.dpma.de/
"""


logger = logging.getLogger(__name__)

class DpmaRegisterAccess:

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
        self.browser.set_cookiejar(cookielib.LWPCookieJar())
        self.browser.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; de; rv:1.9.0.5) Gecko/2008120122 Firefox/3.0.5')]
        # ignore robots.txt
        self.browser.set_handle_robots(False)

        # alternative direct link
        # https://register.dpma.de/DPMAregister/pat/experte/autoRecherche/de?queryString=AKZ%3D2020131020184

        self.baseurl = 'http://register.dpma.de/DPMAregister/pat/'
        self.searchurl = self.baseurl + 'einsteiger'
        self.accessurl = self.baseurl + 'register:showalleverfahrenstabellen?AKZ=%s'
        self.reference_pattern = re.compile('.*\?AKZ=(.+?)&.*')
        self.link_css = './assets/dpmabasis_d.css'


    def fetch(self, patent, html_raw=False, html_stripped=True, data=False):

        document = self.fetch_html(patent)

        result = {
            'html_raw': None,
            'html_stripped': None,
            'data': None,
            }

        if html_raw:
            result['html_raw'] = document.html

        if html_stripped:
            result['html_stripped'] = self.document_strip_html(document)

        if data:
            result['data'] = self.document_parse_html(document.html)

        return result

    def fetch_html(self, patent):

        # 1. search patent reference for direct download
        results = self.search_patent_smart(patent)

        # 2. download patent information by direct reference
        search_entry = results[0]
        return self.fetch_reference(search_entry)


    def get_document_url(self, patent):
        
        # Shortcut for DE applications
        if patent.startswith('DE'):
            checksum = 0
            patent_number = patent[2:]
            for i, n in enumerate(reversed(patent_number)):
                checksum += int(n, 10) * (i + 2)
            checksum = checksum%11
            if checksum:
                checksum = 11 - checksum
            akz = patent + str(checksum)
            url = self.accessurl % akz
            logger.info('document url: {0}'.format(url))
            return url
        
        results = self.search_patent_smart(patent)
        # TODO: review this logic
        if results:
            url = self.accessurl % results[0].reference
            logger.info('document url: {0}'.format(url))
            return url


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
            errmsg = "search result for '%s' is empty" % (patent)
        elif len(results) >= 2:
            errmsg = "search result for '%s' is ambiguous: count=%s, results=%s" % (patent, len(results), results)

        if errmsg:
            logger.warning(errmsg)
            #raise Exception(errmsg)

        return results


    def search_patent(self, patent):

        logger.info("searching document(s), patent='%s'" % patent)

        patent_country = patent[:2].upper()
        patent_number = patent[2:]

        #if patent_country != 'DE':
        #    msg = "country '%s' not valid, must be 'DE'" % patent_country
        #    logger.fatal(msg)
        #    raise Exception(msg)


        # 1. open search url
        response_searchform = self.browser.open(self.searchurl)


        # 2. submit form
        # http://wwwsearch.sourceforge.net/ClientForm/
        self.browser.select_form(nr=0)
        #self.browser.select_form(name='form')
        self.browser['akzPn'] = patent_number
        response = self.browser.submit()

        # 2013-05-11: DPMA changed the interface
        # searching now jumps directly to the result detail page
        # if there's just a single result
        # => so let's parse the reference (AKZ) from the response html
        #    and make up a single result from that
        url = self.browser.geturl()
        if '/pat/register' in url:
            soup = BeautifulSoup(response)
            reference_link = soup.find('a', {'href': self.reference_pattern})
            reference, label = self.parse_reference_link(reference_link, patent)
            entry = self.ResultEntry(reference = reference, label = None)
            return [entry]

        # debugging
        #dump_response(response_searchresult)
        #sys.exit()

        html_searchresult = response.read() #.decode('utf-8')
        #print html_searchresult

        # sanity check
        if 'div class="error"' in html_searchresult:
            logger.warn("no search results for '%s'" % patent)
            return


        # 3. parse result table
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

        logger.info("success for '%s': %s unfiltered results" % (patent, len(results)))

        return results

    def parse_reference_link(self, link, patent):
        m = self.reference_pattern.match(link['href'])
        if m:
            reference = m.group(1)
        else:
            msg = "could not parse document reference from link '%s' (patent='%s')" % (link, patent)
            logger.error(msg)
            raise Exception(msg)
        label = link.find(text=True)
        return reference, label

    def fetch_reference(self, result):
        """open document url and return html"""
        url = self.accessurl % result.reference
        html_document = self.browser.open(url).read() #.decode('utf-8')
        return self.Document(result = result, url = url, html = html_document)


    def document_strip_html(self, document):
        """
        TODO: insert link to original document, insert link to pdf
        <a shape="rect" class="button" target="_blank" href="register?AKZ=100068189&amp;VIEW=pdf">PDF-Download</a>
        """

        soup = BeautifulSoup(document.html)

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
            link['href'] = self.baseurl + link['href']
            if link.img:
                link.img.extract()

        for link in soup.findAll('a', {'href': re.compile('^./register.*')}):
            if link.contents:
                link.replaceWith(link.contents[0])

        document_source_link = str(document.url)
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


    def dump_response(response, dump_metadata = False):
        #print dir(response)
        #print br.title()
        if dump_metadata:
            print response.geturl()
            print response.info()  # headers
        print response.read()  # body



class DpmaRegisterDocument(object):

    def __init__(self, identifier, html=None):
        self.identifier = identifier
        self.html = html
        self.table_basicdata = None
        self.table_legaldata = None
        self.events = []

        self.parse_html()
        self.events = self.table_legaldata

    def __str__(self):
        return str(self.identifier) + ':\n' + pformat(self.events)

    def parse_html(self):
        """
        parse document results from html tables
        FIXME: unfinished!
        """
        soup = BeautifulSoup(self.html)
        soup_table_basicdata = soup.find("table")
        soup_table_legaldata = soup_table_basicdata.findNextSibling("table")

        self.table_basicdata = self.soup_parse_table(soup_table_basicdata, header_row_index = 1)
        self.table_legaldata = self.soup_parse_table(soup_table_legaldata, header_row_index = 1)

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

    logging.basicConfig()

    register = DpmaRegisterAccess()
    if len(sys.argv) > 1:
        data = register.fetch(sys.argv[1])

    else:
        #data = register.fetch('DE10001499.2')   # leads to two results, take the non-"E" one
        #data = register.fetch('DE3831719')      # search and follow to 3831719.2
        #data = register.fetch('WO2007037298')   # worked with DPINFO only
        #data = register.fetch('WO2008034638')   # leads to two results, take the non-"E" one
        #data = register.fetch('DE102006006014') # just one result, directly redirects to detail page

        #data = register.fetch('DE19630877')
        data = register.fetch('DE102012009645')
        #print register.get_document_url('DE102012009645')

    print data['html_stripped']

    #f = file('./tmp/out.html', 'w')
    #f.write(data['html_stripped'])
    #f.close()

    #print dictify_data(data)
