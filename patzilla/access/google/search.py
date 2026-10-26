# -*- coding: utf-8 -*-
# (c) 2014 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
import json
import re
from typing import cast

from pyramid.encode import urlencode
# py27 import re
import sys
import logging
import requests
# py27 from BeautifulSoup import BeautifulSoup
from bs4 import BeautifulSoup

from patzilla.util.expression.keywords import keywords_from_boolean_expression
from patzilla.util.numbers.normalize import normalize_patent


"""
Scraper for Google Patents
http://patents.google.com/
"""

logger = logging.getLogger(__name__)

class GooglePatentsAccess:

    def __init__(self):
        self.baseurl = 'https://www.google.com/search?tbo=p&tbm=pts&hl=en'
        self.pagesize = 100      # one of: 10 (default), 20, 30, 50, 100

        self.user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2107.0 Safari/537.36'

    def search(self, expression, offset=0, limit=None):

        limit = limit or self.pagesize

        logger.info("Google: searching documents, expression='{0}', offset={1}, limit={2}".format(expression, offset, limit))

        # 1. compute url parameter
        parameters = {
            'start': offset,
            'num': limit,
        }

        # expression might be fulltext or json
        try:
            json_params = json.loads(expression)
            parameters.update(json_params)

        except ValueError:
            parameters['q'] = expression

        if not parameters['q']:
            parameters['q'] = ''

        # 2. perform search
        url = self.baseurl + '&' + urlencode(parameters)
        logger.info("Google search url: {0}".format(url))
        response = requests.get(url, headers={'User-Agent': self.user_agent})

        #print "google status:", response.status_code
        #print "google response:", response.text

        payload = {
            'query': expression,
        }
        if response.status_code == 200:
            payload.update(self.parse_response(response.text))

        elif response.status_code == 503 and 'CaptchaRedirect' in response.text:
            payload['message'] = self.tweak_captcha_response(response.text)

        else:
            message = 'Accessing Google Patent Search failed with status={0} for url {1}'.format(
                str(response.status_code) + ' ' + response.reason, url)
            logger.error(message + ' body:\n' + response.text)
            raise ValueError(message)

        return payload

    def tweak_captcha_response(self, body):
        soup = BeautifulSoup(body)

        baseurl = 'https://ipv4.google.com'

        captcha_image = soup.find('img')
        if not captcha_image:
            raise ValueError("No image found in HTML document")
        #print dir(head)
        #head.append(Tag(soup, 'base', [('href', 'https://ipv4.google.com')]))
        captcha_image['src'] = baseurl + cast(str, captcha_image['src'])

        captcha_form = soup.find('form')
        if not captcha_form:
            raise ValueError("No form found in HTML document")
        captcha_form['action'] = baseurl + '/' + cast(str, captcha_form['action'])

        newbody = str(soup)
        print(newbody)
        return newbody

    def parse_response(self, body):

        soup = BeautifulSoup(body)

        # 1. parse hit count
        # <div id="resultStats">1 result<nobr> (0.32 seconds)&nbsp;</nobr></div>
        # <div id="resultStats">About 24,100,000 results<nobr> (0.19 seconds)&nbsp;</nobr></div>
        # <div id="resultStats">Page 2 of about 50,600 results<nobr> (0.32 seconds)&nbsp;</nobr></div>
        #result_stats_pattern = re.compile('?P<hits>(?:About (.+?) results|(.+?) result)')
        result_stats_node = soup.find('div', {'id': 'resultStats'})
        hits = None
        page = 1
        if result_stats_node:
            result_stats = result_stats_node.getText()
            patterns = [
                '(?P<hits>.+?) result<nobr>',
                'About (?P<hits>.+?) results',
                'Page (?P<page>.+?) of about (?P<hits>.+?) results',
            ]
            for pattern in patterns:
                m = re.match(pattern, result_stats)
                if m:
                    break

            if m:
                hits = int(m.group('hits').replace(',', ''))
                page = 1
                try:
                    page = int(m.group('page'))
                except IndexError:
                    pass


        # 2. parse result numbers
        results = []
        # <h3 class="r"><a href="https://www.google.com/patents/US351065?dq=matrix&amp;hl=en&amp;sa=X&amp;ei=TrJaVJfSNYbWPcyPgLAI&amp;ved=0CO8CEOgBMDA">Dental matrix</a></h3>
        href_pattern = re.compile('https://www.google.com/patents/(.+?)\?.*')
        entries = soup.find_all('h3', attrs={'class': 'r'})
        for entry in entries:
            anchor = entry.find('a')
            if not anchor:
                raise ValueError("No anchor found in HTML element")

            # https://www.google.com/patents/US4912874?dq=matrix&hl=en&sa=X&ei=lLhaVLXEIcftO7CEgLAM&ved=0CB8Q6AEwAA
            href = anchor['href']
            if not href:
                raise ValueError("Unable to extract href from HTML element")

            m = href_pattern.match(cast(str, href))
            if m:
                number = m.group(1)
                results.append(number)


        # 3. check for messages
        message = None
        if 'did not match' in body:

            hits = 0

            #print dir(soup)
            ucs_element = soup.find('div', {'id': 'ucs'})
            res_element = soup.find('div', {'id': 'res'})

            if ucs_element and res_element:

                ucs_node = ucs_element.get_text()
                res_node = res_element.find('div', {'class': 'med card-section'})

                message = ''
                if ucs_node:
                    message += str(ucs_node) + '<br/>'
                message += str(res_node)

        payload = {
            'numbers': results,
            'hits': hits,
            'page': page,
            'message': message,
        }

        return payload


class GooglePatentsExpression:

    """

    q=
        patent:
        intitle:
        ininventor:
        inassignee:
        intlpclass:"B60R+16/00"
        cpclass:"B60R+16/00"

    tbs=
        ptso:de (us,ep,wo,cn,ca)
        sort by relevance: -
        sort by latest: sbd:1
        sort by oldest: sbdo:1

    all words: q=matrix+water
    exact phrase: q="matrix+water"
    at least one: q=matrix+OR+water
    without: q=-matrix+-water

    """

    fieldmap = {
        'patentnumber': {'name': 'patent',      'parameter': 'q', },
        'fulltext':     {'name': None,          'parameter': 'q', },
        'applicant':    {'name': 'inassignee',  'parameter': 'q', },
        'inventor':     {'name': 'ininventor',  'parameter': 'q', },
        'class':        {'name': 'intlpclass',  'parameter': 'q', },
        'country':      {'name': 'ptso',        'parameter': 'tbs', },
        #'pubdate':      {'name': 'pd',  },
        #'appdate':      {'name': 'ap',  },
        #'citation':     {'name': 'ct',  },
        }

    def __init__(self, criteria=None, query=''):
        criteria = criteria or {}
        self.criteria = criteria
        self.query = query

    @classmethod
    def pair_to_term(cls, key, value):

        try:
            fieldname = cls.fieldmap[key]['name']
            parameter = cls.fieldmap[key]['parameter']
        except KeyError:
            return

        if fieldname:
            if key == 'country':
                value = value.lower()
            elif key == 'patentnumber':
                value_normalized = normalize_patent(value)
                if value_normalized:
                    value = value_normalized
            term = '{0}:{1}'.format(fieldname, value)
        else:
            term = value

        term_data = {
            'parameter': parameter,
            'term': term,
        }

        return term_data

    def serialize(self):
        """
        inassignee:siemens and ininventor:"Timothy Thomas"
        """
        query_params = []
        tbs_params = []
        for key, value in self.criteria.items():
            term = self.pair_to_term(key, value)
            if term['parameter'] == 'q':
                query_params.append(term['term'])
            elif term['parameter'] == 'tbs':
                tbs_params.append(term['term'])

        tbs_params.append('sbd:1')

        query_expression = ' and '.join(query_params)
        tbs_expression = ','.join(tbs_params)

        url_parameters = {
            'q': query_expression or self.query,
            'tbs': tbs_expression,
        }

        #return urlencode(url_parameters)
        return json.dumps(url_parameters, indent=4)

    def get_keywords(self):
        keywords = []
        for key, value in self.criteria.items():
            keywords += keywords_from_boolean_expression(key, value)
        return keywords


if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO)

    google = GooglePatentsAccess()
    if len(sys.argv) > 1:
        data = google.search(sys.argv[1])

    else:
        #data = google.search('matrix', 19900)
        data = google.search('intitle:matrix', 19900)

    print(data)
