# -*- coding: utf-8 -*-
# (c) 2014-2019 Andreas Motl <andreas.motl@ip-tools.org>
import logging
import requests
from beaker.cache import cache_region
from pyramid.httpexceptions import HTTPNotFound

from patzilla.util.network.browser import regular_user_agent
from patzilla.util.numbers.normalize import normalize_patent

logger = logging.getLogger(__name__)


def document_viewer_url(document, validate=True):

    document = normalize_patent(document, for_ops=False)

    reference_type = None
    if len(document.number) <= 9:
        reference_type = 'publication'
    elif len(document.number) >= 10:
        reference_type = 'application'

    url_tpl = None
    if reference_type == 'application':
        # AppFT image server
        # http://pdfaiw.uspto.gov/.aiw?docid=20160105912
        url_tpl = 'http://pdfaiw.uspto.gov/.aiw?docid={docid}'

    elif reference_type == 'publication':
        # PatFT image server
        # http://pdfpiw.uspto.gov/.piw?docid=9317610
        url_tpl = 'http://pdfpiw.uspto.gov/.piw?docid={docid}'

    if url_tpl:
        url = url_tpl.format(docid=document.number)

        result = {'location': url, 'origin': 'USPTO'}

        # Pre-flight check upstream url for existence of document
        if validate:
            try:
                response = requests.get(url)
                if 'is not a valid ID' in response.content:
                    return
            except:
                return

        return result


def pdf_url(document_number):
    """
    # Application
    >>> pdf_url('US2016101909A1')
    'http://pdfaiw.uspto.gov/fdd/09/2016/19/010/0.pdf'

    # Grant I
    >>> pdf_url('US10194689B2')
    'http://pdfpiw.uspto.gov/fdd/89/946/101/0.pdf'

    # Grant II
    >>> pdf_url('US2548918')
    'http://pdfpiw.uspto.gov/fdd/18/489/025/0.pdf'
    """

    document = normalize_patent(document_number, for_ops=False, as_dict=True, provider='uspto')
    if not document:
        return

    # Application
    if len(document.number) == 11:
        n = document.number
        # US20160101909A1
        # http://pdfaiw.uspto.gov/fdd/09/2016/19/010/0.pdf
        url = 'http://pdfaiw.uspto.gov/fdd/{}/{}/{}/{}/0.pdf'.format(n[9:11], n[0:4], n[7:9], n[4:7])

    # Grant
    elif len(document.number) == 8:
        n = document.number
        # US10194689B2
        # http://pdfpiw.uspto.gov/fdd/89/946/101/0.pdf
        url = 'http://pdfpiw.uspto.gov/fdd/{}/{}/{}/0.pdf'.format(n[6:8], n[3:6], n[0:3])

    else:
        raise ValueError('US document number "{}" has unexpected length'.format(document_number))

    return url


@cache_region('static')
def fetch_pdf(document_number):
    """
    Retrieve PDF document from the USPTO document servers.

    Blueprint addresses:

    - Application: US2016101909A1
      http://pdfaiw.uspto.gov/fdd/09/2016/19/010/0.pdf

    - Grant: US10194689B2
      http://pdfpiw.uspto.gov/fdd/89/946/101/0.pdf
    """

    url = pdf_url(document_number)

    logger.info('PDF {}: Accessing USPTO document server: {}'.format(document_number, url))
    response = requests.get(url, headers={'User-Agent': regular_user_agent})

    # Debugging
    #print 'response.content:\n', response.content

    if response.status_code == 200:
        payload = response.content
        return payload

    else:
        msg = 'Document "{}" not found at USPTO document server'.format(document_number)
        raise HTTPNotFound(msg)


if __name__ == '__main__':
    appnumber = 'US2016101909A1'
    pubnumber = 'US10194689B2'

    print(pdf_url(appnumber))
    print(pdf_url(pubnumber))
