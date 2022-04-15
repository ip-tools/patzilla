# -*- coding: utf-8 -*-
# (c) 2014-2022 Andreas Motl <andreas.motl@ip-tools.org>
"""
About
=====

Acquire PDF documents from USPTO servers.


Synopsis
========
::

    # Sweep multiple samples.
    python -m patzilla.access.uspto.pdf

    # Acquire full document.
    python -m patzilla.access.uspto.pdf US20070231208A1 > US20070231208A1.pdf


Resources
=========

- US Published Patent Application Full-Page Images (ex. AppFT image server)
  https://appft.uspto.gov/netahtml/PTO/appimg.htm

- US Patent Full-Page Images (ex. PatFT image server)
  https://patft.uspto.gov/netahtml/PTO/patimg.htm


Examples
========

Applications
------------

- US20160105912
  - :view: https://pdfaiw.uspto.gov/.aiw?docid=20160105912
- US20160101909A1
  - :full: https://pdfaiw.uspto.gov/fdd/09/2016/19/010/0.pdf
  - :page: https://pdfaiw.uspto.gov/09/2016/19/010/2.pdf 
- US2022110447
  - :full: https://pdfaiw.uspto.gov/fdd/47/2022/04/011/0.pdf
  - :page: https://pdfaiw.uspto.gov/47/2022/04/011/2.pdf

Publications
------------

- US9317610
  - :view: https://pdfpiw.uspto.gov/.piw?docid=9317610
- US10194689B2 
  - :full: https://pdfpiw.uspto.gov/fdd/89/946/101/0.pdf
  - :page: https://pdfpiw.uspto.gov/89/946/101/5.pdf
- US05123456   
  - :full: https://pdfpiw.uspto.gov/fdd/56/234/051/0.pdf
  - :page: https://pdfpiw.uspto.gov/56/234/051/2.pdf

"""
import logging
import os
import socket
import sys
from collections import OrderedDict

import requests
from bs4 import BeautifulSoup
from beaker.cache import cache_region
from pyramid.httpexceptions import HTTPNotFound

from patzilla.util.config import to_list
from patzilla.util.network.browser import regular_user_agent
from patzilla.util.numbers.normalize import normalize_patent

logger = logging.getLogger(__name__)

http = requests.Session()


# Timeout for HTTP requests.
DEFAULT_TIMEOUT = 5.0


class UsptoPdfSection:
    FULL = -1
    FRONT_PAGE = 1
    DRAWINGS = 2
    SPECIFICATIONS = 3
    CLAIMS = 4


class UsptoPdfReferenceType:
    APPLICATION = 1
    PUBLICATION = 2


def get_reference_type(document):
    """
    Analyze document number to tell application vs. patent (publication, grant) numbers apart.
    The basic heuristic is to assume e.g. US2007231208A1 (4+6=10 chars) to be an application.
    """
    assert document is not None
    assert isinstance(document.number, str)
    number_length = len(document.number)
    reference_type = None
    if number_length <= 9:
        reference_type = UsptoPdfReferenceType.PUBLICATION
    elif number_length >= 10:
        reference_type = UsptoPdfReferenceType.APPLICATION
    return reference_type


def document_viewer_url(document_number, validate=True):

    document = normalize_patent(document_number, for_ops=False, as_dict=True, provider='uspto')
    reference_type = get_reference_type(document)
    url_tpl = None
    if reference_type == UsptoPdfReferenceType.APPLICATION:
        url_tpl = 'https://pdfaiw.uspto.gov/.aiw?docid={docid}'

    elif reference_type == UsptoPdfReferenceType.PUBLICATION:
        url_tpl = 'https://pdfpiw.uspto.gov/.piw?docid={docid}'

    if url_tpl:
        url = url_tpl.format(docid=document.number)

        result = {'location': url, 'origin': 'USPTO'}

        # Pre-flight check upstream url for existence of document.
        # TODO: Read and propagate upstream error message like
        #       `<b>Error Message: Unable to locate 0000000</b>`.
        if validate:
            try:
                response = fetch_url(url)
                print("response.content:", response.content)
                if 'is not a valid ID' in response.content or 'Unable to locate' in response.content:
                    raise HTTPNotFound('USPTO [PDF]: Resource at {} not found'.format(url))
            except HTTPNotFound:
                raise
            except Exception as ex:  # pragma: nocover
                raise ValueError('USPTO [PDF]: Failed to access resource at {}. Exception: {}'.format(url, ex))

        return result


@cache_region('static')
def fetch_url(url, method="get"):

    # Use default timeout.
    timeout = DEFAULT_TIMEOUT

    # On specific environments, reduce timeout to make the test suite not wait
    # for invalid but blocking HTTP requests.
    system_under_test = \
        "PYTEST_CURRENT_TEST" in os.environ and \
        "sink" in socket.gethostname()
    if system_under_test:
        timeout = 0.3

    # Invoke HTTP request with specified method.
    fun = getattr(http, method)
    response = fun(url, headers={'User-Agent': regular_user_agent}, timeout=timeout)

    # Handle the response.
    if response.status_code == 200:
        return response

    if response.status_code == 404:
        msg = 'USPTO [PDF]: Resource at {} not found'.format(url)
    else:
        msg = 'USPTO [PDF]: Accessing resource at {} failed. status={}, response={}'.format(
            url, response.status_code, response.content)
    raise HTTPNotFound(msg)


def pdf_index(document_number, include=None):

    if include:
        include = to_list(include)

    # Normalize document number and compute reference type (application vs. publication).
    document = normalize_patent(document_number, for_ops=False, as_dict=True, provider='uspto')
    reference_type = get_reference_type(document)

    # Compute index page URL.
    if reference_type == UsptoPdfReferenceType.APPLICATION:
        baseurl = 'https://pdfaiw.uspto.gov'
        pageurl = '/.aiw?docid={}'
    elif reference_type == UsptoPdfReferenceType.PUBLICATION:
        baseurl = 'https://pdfpiw.uspto.gov'
        pageurl = '/.piw?docid={}'

    url = baseurl + pageurl.format(document.number)

    logger.info("Acquiring document index at {}".format(url))

    # Fetch and parse HTML pages to create map of section => URLs.
    # <embed src="//pdfpiw.uspto.gov/89/946/101/5.pdf" width="100%" height="850" type=application/pdf name="10194689" ></embed>
    section_url_map = OrderedDict()
    for section in [UsptoPdfSection.FRONT_PAGE, UsptoPdfSection.DRAWINGS, UsptoPdfSection.SPECIFICATIONS, UsptoPdfSection.CLAIMS]:

        # When `include` option is given, only inquire specified sections to save resources.
        if include and section not in include:
            continue

        # Fetch single HTML page.
        url_to_section = url + "&SectionNum={}".format(section)
        response = fetch_url(url_to_section)

        # Read `src` attribute from `<embed>` element.
        soup = BeautifulSoup(response.content, features="lxml")
        embed = soup.find("embed", attrs={"type": "application/pdf"})
        embed_src = embed["src"]

        # Compute full URL to PDF document.
        # If any host name (`uspto.gov`) is already present in the URL, it means the `embed.src`
        # is something like `//pdfpiw.uspto.gov/59/615/072/3.pdf`. In this case, make sure to
        # prefix it with the HTTP scheme `https:`.
        if "uspto.gov" in embed_src:
            pdfurl = "https:" + embed_src
        else:
            pdfurl = baseurl + embed_src
        section_url_map[section] = pdfurl

    if not section_url_map:
        logger.warning("Unable to compute PDF section map for document {}".format(document_number))

    return section_url_map


def pdf_url(document_number, section=UsptoPdfSection.FULL):
    """
    # Application
    >>> pdf_url('US2016101909A1')
    'https://pdfaiw.uspto.gov/fdd/09/2016/19/010/0.pdf'

    # Grant I
    >>> pdf_url('US10194689B2')
    'https://pdfpiw.uspto.gov/fdd/89/946/101/0.pdf'

    # Grant II
    >>> pdf_url('US2548918')
    'https://pdfpiw.uspto.gov/fdd/18/489/025/0.pdf'
    """

    document = normalize_patent(document_number, for_ops=False, as_dict=True, provider='uspto')
    if not document:
        return

    fdd_infix = ""
    if section == UsptoPdfSection.FULL:
        fdd_infix = "fdd/"
        page = 0
    else:
        index = pdf_index(document, include=UsptoPdfSection.DRAWINGS)
        url = index.get(section)
        return url

    # Application
    if len(document.number) == 11:
        n = document.number
        url = 'https://pdfaiw.uspto.gov/{}{}/{}/{}/{}/{}.pdf'.format(fdd_infix, n[9:11], n[0:4], n[7:9], n[4:7], page)

    # Publication and Grant
    elif len(document.number) == 8:
        n = document.number
        url = 'https://pdfpiw.uspto.gov/{}{}/{}/{}/{}.pdf'.format(fdd_infix, n[6:8], n[3:6], n[0:3], page)

    else:  # pragma: nocover
        raise ValueError('US document number "{}" has unexpected format'.format(document_number))

    return url


def fetch_pdf(document_number, section=UsptoPdfSection.FULL):
    """
    Retrieve PDF document from the USPTO document servers.

    Blueprint addresses:

    - Application: US2016101909A1
      :full: https://pdfaiw.uspto.gov/fdd/09/2016/19/010/0.pdf
      :page: https://pdfaiw.uspto.gov/09/2016/19/010/2.pdf

    - Grant: US10194689B2
      :full: https://pdfpiw.uspto.gov/fdd/89/946/101/0.pdf
      :page: https://pdfpiw.uspto.gov/89/946/101/5.pdf
    """

    url = pdf_url(document_number, section=section)

    logger.info('Accessing document {} at {}'.format(document_number, url))
    response = fetch_url(url)

    # Debugging
    # print('response.status:  {}'.format(response.status_code))
    # print('response.content: {}'.format(response.content))

    return response.content


example_numbers = [
    # Applications
    'US20140071615A1',
    'US20140075562A1',
    'US2016101909A1',
    'US20070231208A1', 'US2007231208A1',

    # Publications
    # 7-char numbers
    'US7261559B2',
    'US07270540B2',
    'US7493690B2',
    'US7494593B1', 'US7494597B2',
    # 8-char numbers
    'US10194689B2',
]


def run_examples(fun, ev=None):  # pragma: nocover
    for number in example_numbers:
        response = fun(number)
        if response:
            if ev:
                response = eval(ev)
            msg = "{:<16} {}".format(number, response)
        else:
            msg = "{:<16} {}".format(number, "not found")
        print(msg)


if __name__ == '__main__':  # pragma: nocover
    """
    Demo program for computing the direct access URL to PDF document(s) on USPTO servers.
    """

    from patzilla.util.cache.backend import configure_cache_backend
    from patzilla.util.logging import setup_logging

    setup_logging()

    # configure_cache_backend("memory")
    configure_cache_backend("filesystem")

    if len(sys.argv) == 2:
        number = sys.argv[1]
        print(fetch_pdf(number))

    else:
        run_examples(pdf_url)
