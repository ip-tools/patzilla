# -*- coding: utf-8 -*-
# (c) 2014-2022 Andreas Motl <andreas.motl@ip-tools.org>
"""
About
=====

Acquire PDF documents from USPTO servers.

https://meta.ip-tools.org/t/uspto-introducing-ppubs-deprecating-patft-appft-pubeast-and-pubwest/178


Synopsis
========
::

    # Sweep multiple samples.
    python -m patzilla.access.uspto.pdf

    # Acquire full document.
    python -m patzilla.access.uspto.pdf US20070231208A1 > US20070231208A1.pdf


Resources
=========

- USPTO Patent Public Search tool (PPUBS)
  https://ppubs.uspto.gov/pubwebapp/


Examples
========

Applications
------------

- US20160105912
  - https://ppubs.uspto.gov/dirsearch-public/image-conversion/convert?url=us-pgpub/US/2016/0105/912/00000001.tif
- US20160101909A1
  - https://ppubs.uspto.gov/dirsearch-public/image-conversion/convert?url=us-pgpub/US/2016/0101/909/00000001.tif
- US2022110447
  - https://ppubs.uspto.gov/dirsearch-public/image-conversion/convert?url=us-pgpub/US/2022/0110/447/00000001.tif

Publications
------------

- US9317610
  - https://ppubs.uspto.gov/dirsearch-public/image-conversion/convert?url=uspat/US/09/317/610/00000001.tif
- US10194689B2
  - https://ppubs.uspto.gov/dirsearch-public/image-conversion/convert?url=uspat/US/G89/946/101/00000001.tif
- US05123456
  - https://ppubs.uspto.gov/dirsearch-public/image-conversion/convert?url=uspat/US/05/123/456/00000001.tif

"""
import logging
import os
import socket
import sys
from collections import OrderedDict

import requests
from beaker.cache import cache_region
from pyramid.httpexceptions import HTTPNotFound
from repoze.lru import lru_cache

from patzilla.access.generic.exceptions import SearchException
from patzilla.util.config import to_list
from patzilla.util.image.convert import pdf_join, to_pdf
from patzilla.util.network.browser import regular_user_agent
from patzilla.util.numbers.normalize import normalize_patent

logger = logging.getLogger(__name__)

http = requests.Session()
#http.headers["User-Agent"] = regular_user_agent
http.headers["User-Agent"] = "Python Patent Clientbot/{__version__} (parkerhancock@users.noreply.github.com)"


# Timeout for HTTP requests.
DEFAULT_TIMEOUT = 5.0


class UsptoPdfSection:
    FULL = -1
    FRONT_PAGE = 1
    BIBLIO = 2
    ABSTRACT = 3
    DRAWINGS = 4
    SPECIFICATIONS = 5
    DESCRIPTION = 6
    CLAIMS = 7
    SEARCH_REPORT = 8
    SUPPLEMENTAL = 9
    PTAB = 10
    CERT_CORRECTION = 11
    CERT_REEXAMINATION = 12


UsptoPdfSectionAttributeMap = {
    UsptoPdfSection.FRONT_PAGE: "frontPage",
    UsptoPdfSection.BIBLIO: "bib",
    UsptoPdfSection.ABSTRACT: "abstract",
    UsptoPdfSection.DRAWINGS: "drawings",
    UsptoPdfSection.SPECIFICATIONS: "specification",
    UsptoPdfSection.DESCRIPTION: "description",
    UsptoPdfSection.CLAIMS: "claims",
    UsptoPdfSection.SEARCH_REPORT: "searchReport",
    UsptoPdfSection.SUPPLEMENTAL: "supplemental",
    UsptoPdfSection.PTAB: "ptab",
    UsptoPdfSection.CERT_CORRECTION: "certCorrection",
    UsptoPdfSection.CERT_REEXAMINATION: "certReexamination",
}


class UsptoPdfReferenceType:
    APPLICATION = 1
    PUBLICATION = 2


def get_reference_type(document):
    """
    Analyze document number to tell application vs. patent (publication, grant) numbers apart.
    The basic heuristic is to assume e.g. US2007231208A1 (4+6=10 chars) to be an application.
    """
    if document is None or not (hasattr(document, "number") and isinstance(document.number, (int, str, unicode))):
        raise ValueError("Unknown document reference type: {}".format(document))
    number_length = len(str(document.number))
    reference_type = None
    if number_length <= 9:
        reference_type = UsptoPdfReferenceType.PUBLICATION
    elif number_length >= 10:
        reference_type = UsptoPdfReferenceType.APPLICATION
    return reference_type


def document_viewer_url(document_number):
    """
    Compute URL to document number.
    """
    access = UsptoDocumentAccess(document_number=document_number)
    url = access.get_page_url()
    return {"location": url, "origin": "USPTO"}


@cache_region('static')
def url_to_pdf(url):
    """
    Acquire page as PNG, and convert to PDF, cached.
    """
    return to_pdf(url).read()


@cache_region('static')
def fetch_url(url, method="get"):
    """
    Fetch response for URL.
    """

    # Use default timeout.
    timeout = DEFAULT_TIMEOUT

    # On specific environments, reduce timeout to make the test suite not wait
    # for invalid but blocking HTTP requests.
    system_under_test = \
        "PYTEST_CURRENT_TEST" in os.environ and \
        "sink" in socket.gethostname()
    if system_under_test:  # pragma: nocover
        timeout = 1.8

    # Invoke HTTP request with specified method.
    fun = getattr(http, method)
    response = fun(url, timeout=timeout)

    # Handle the response.
    if response.status_code == 200:
        return response

    if response.status_code == 404:
        msg = 'USPTO [PDF]: Resource at {} not found'.format(url)
    else:
        msg = 'USPTO [PDF]: Accessing resource at {} failed. status={}, response={}'.format(
            url, response.status_code, response.content)
    raise HTTPNotFound(msg)


def get_patent_number_patentcenter(any_number):
    """
    Inquire patent number from `patentcenter.uspto.gov`.

    TODO: This will quickly trigger `Service Unavailable  [PUBLIC], Max search limit reached.`.
          So, find another way to resolve USPTO application or publication numbers to patent numbers.
    """
    document = normalize_patent(any_number, for_ops=False, as_dict=True, provider='uspto-ng')
    if not document:
        return
    reference_type = get_reference_type(document)

    # US20140071615A1
    if reference_type == UsptoPdfReferenceType.APPLICATION:
        url_prefix = "https://patentcenter.uspto.gov/retrieval/public/v2/application/data?publicationNumber="

    # US07261559
    elif reference_type == UsptoPdfReferenceType.PUBLICATION:
        url_prefix = "https://patentcenter.uspto.gov/retrieval/public/v2/application/data?applicationNumberText="

    else:
        raise TypeError("Unknown document type: {}".format(reference_type))

    start_url = url_prefix + document.number
    logger.info("Inquiring information at: {}".format(start_url))
    try:
        response = http.get(start_url).json()
        if "error" in response:
            raise ValueError("Acquiring data failed. Reason: {}, {}".format(response["error"], response["message"]))
        return response["applicationMetaData"]["patentNumber"]
    except KeyError as ex:
        raise ValueError("USPTO document number not found or incorrect format: {}".format(any_number))


class UsptoDocumentAccess:

    def __init__(self, document_number):
        self.document_number = document_number
        self.document = normalize_patent(self.document_number, for_ops=False, as_dict=True, provider="uspto-ng")

    @lru_cache(maxsize=None)
    def inquire_images(self):
        """
        Inquire patent number from `ppubs.uspto.gov`.
        """
        if not self.document:
            return

        # `07270540` would be an invalid query, so strip leading zeros.
        logger.info("Inquiring document: {}".format(self.document.number))
        query = '("{}").pn.'.format(self.document.number)
        query = '@PD>=20100101<=20101231 AND "tennis".TTL.'

        data = {
            "start": 0,
            "pageCount": 500,
            "sort": "date_publ desc",
            "docFamilyFiltering": "familyIdFiltering",
            "searchType": 1,
            "familyIdEnglishOnly": True,
            "familyIdFirstPreferred": "US-PGPUB",
            "familyIdSecondPreferred": "USPAT",
            "familyIdThirdPreferred": "FPRS",
            "showDocPerFamilyPref": "showEnglish",
            "queryId": 0,
            "tagDocSearch": False,
            "query": {
                #"caseId": 1623140,
                #"caseId": 16885434,
                "caseId": None,
                "hl_snippets": "2",
                "op": "OR",
                "q": query,
                "queryName": query,
                "highlights": "1",
                "qt": "brs",
                "spellCheck": False,
                "viewName": "tile",
                "plurals": True,
                "britishEquivalents": True,
                "databaseFilters": [
                    {"databaseName": "US-PGPUB", "countryCodes": []},
                    {"databaseName": "USPAT", "countryCodes": []},
                    {"databaseName": "USOCR", "countryCodes": []},
                ],
                "searchType": 1,
                "ignorePersist": True,
                "userEnteredQuery": query,
            },
        }

        response = http.post("https://ppubs.uspto.gov/dirsearch-public/searches/searchWithBeFamily", json=data)
        response.raise_for_status()
        if response.status_code == 202:
            raise SearchException("Empty response from USPTO, most probably caused by WAF blocking")
        data = response.json()

        # print(json.dumps(data, indent=2))

        if "error" in data and data["error"]:
            logger.error(data["error"])

        return data

    def get_page_url(self, page=1):
        """
        Get URL to PNG image, by page.
        """

        if page == 0:
            return

        data = self.inquire_images()
        if data["patents"]:
            first_hit = data["patents"][0]
            return _get_image_url(first_hit, page=page)
        else:
            message = "USPTO document number not found or incorrect format: {}".format(self.document_number)
            logger.warning(message)

            msg = 'USPTO [PDF]: Resource {} not found'.format(self.document_number)
            raise HTTPNotFound(msg)

    def get_allpages_urls(self):
        """
        Build list of URLs for all pages of a PDF document.
        """
        data = self.inquire_images()

        if not (data and data["patents"]):
            msg = 'USPTO [PDF]: Resource {} not found'.format(self.document_number)
            raise HTTPNotFound(msg)

        first_hit = data["patents"][0]
        page_count = first_hit["pageCount"]
        urls = []
        for page in range(1, page_count + 1):
            url = _get_image_url(first_hit, page=page)
            urls.append(url)
        return urls

    def pdf_index(self, include=None):
        """
        Build map from document section to (start) URL.
        """

        if include:
            include = to_list(include)

        # Compute index page URL.
        section_url_map = OrderedDict()
        data = self.inquire_images()

        if data["patents"]:
            first_hit = data["patents"][0]

            for section, attrprefix in UsptoPdfSectionAttributeMap.items():

                # When `include` option is given, only inquire specified sections to save resources.
                if include and section not in include:
                    continue

                start = first_hit.get(attrprefix + "Start")
                end = first_hit.get(attrprefix + "End")

                url = self.get_page_url(page=start)
                section_url_map[section] = url

        if not section_url_map:
            logger.warning("Unable to compute PDF section map for document {}".format(self.document_number))

        # logger.info("section_url_map: {}".format(section_url_map))

        return section_url_map


def _get_image_url(patent_data, page=1):
    """
    https://ppubs.uspto.gov/dirsearch-public/image-conversion/convert?url=uspat/US/02/548/918/00000001.tif
    """
    address = "{}/{}.tif".format(patent_data["imageLocation"], str(page).zfill(8))
    url = "https://ppubs.uspto.gov/dirsearch-public/image-conversion/convert?url={}".format(address)
    logger.debug("Computed URL: {}".format(url))
    return url


def get_page_url_by_patent_number(pn, page=1):
    address = "uspat/US/{}/{}/{}/{}.tif".format(pn[:-6].zfill(2), pn[-6:-3], pn[-3:], str(page).zfill(8))
    url = 'https://ppubs.uspto.gov/dirsearch-public/image-conversion/convert?url={}'.format(address)
    return url


def png_url(document_number, section=UsptoPdfSection.DRAWINGS):
    """
    # Application
    >>> png_url('US2016101909A1', section=UsptoPdfSection.DRAWINGS)
    'https://ppubs.uspto.gov/dirsearch-public/image-conversion/convert?url=us-pgpub/US/2016/0101/909/00000002.tif'

    # Grant I
    >>> png_url('US10194689B2', section=UsptoPdfSection.DESCRIPTION)
    'https://ppubs.uspto.gov/dirsearch-public/image-conversion/convert?url=uspat/US/G89/946/101/00000015.tif'

    # Grant II
    >>> png_url('US2548918', section=UsptoPdfSection.CLAIMS)
    'https://ppubs.uspto.gov/dirsearch-public/image-conversion/convert?url=uspat/US/02/548/918/00000003.tif'
    """

    logger.debug("Computing PDF URL for {}".format(document_number))

    document = normalize_patent(document_number, for_ops=False, as_dict=True, provider="uspto-ng")
    logger.debug("Normalized document number: {}".format(document))
    if not document:
        return

    if section == UsptoPdfSection.FULL:
        raise NotImplementedError("As of 2022, there is no direct URL to the full PDF document at USPTO")
    else:
        access = UsptoDocumentAccess(document_number=document_number)
        index = access.pdf_index()
        url = index.get(section)
        return url


def fetch_pdf(document_number, section=UsptoPdfSection.FULL):
    """
    Retrieve PDF document from the USPTO document servers.

    Blueprint addresses:

    - Application: US2016101909A1
      https://ppubs.uspto.gov/dirsearch-public/image-conversion/convert?url=us-pgpub/US/2016/0101/909/00000001.tif

    - Grant: US10194689B2
      https://ppubs.uspto.gov/dirsearch-public/image-conversion/convert?url=uspat/US/G89/946/101/00000001.tif
    """
    logger.info("Fetching PDF for {}".format(document_number))
    access = UsptoDocumentAccess(document_number=document_number)

    if section == UsptoPdfSection.FULL:
        pdf_payloads = []
        urls = access.get_allpages_urls()
        for url in urls:
            logger.info("Fetching page from {}".format(url))
            pdf = url_to_pdf(url)
            pdf_payloads.append(pdf)
        outcome = pdf_join(pdf_payloads)
        return outcome

    else:

        raise NotImplementedError("Conversion of single pages from PNG to PDF not implemented yet")


def fetch_png(document_number, section=UsptoPdfSection.FULL):
    if section == UsptoPdfSection.FULL:
        raise NotImplementedError("Acquiring a full document as PNG not possible")
    else:
        url = png_url(document_number, section=section)
        logger.info('Accessing document {} at {}'.format(document_number, url))
        response = fetch_url(url)

        # Debugging
        # print('response.status:  {}'.format(response.status_code))
        # print('response.content: {}'.format(response.content))

        return response.content


example_numbers = [
    # Applications
    # https://patentcenter.uspto.gov/retrieval/public/v2/application/data?publicationNumber=US20160101909A1
    'US20140071615A1',
    'US20140075562A1',
    'US2016101909A1',
    'US20070231208A1', 'US2007231208A1',

    # Publications
    # https://patentcenter.uspto.gov/retrieval/public/v2/application/data?applicationNumberText=07261559
    # 7-char numbers
    'US5051145A',
    'US7261559B2',
    'US07270540B2',     # Access `childContinuityBag[0][patentNumber]==5101689`?
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

    Synopsis::

        python -m patzilla.access.uspto.pdf
        python -m patzilla.access.uspto.pdf US20140071638A1
        python -m patzilla.access.uspto.pdf US20070231208A1
    """

    from patzilla.boot.cache import configure_cache_backend
    from patzilla.boot.logging import setup_logging

    setup_logging()

    # configure_cache_backend("memory")
    configure_cache_backend("filesystem")

    if len(sys.argv) == 2:
        number = sys.argv[1]
        print(fetch_pdf(number))

    else:
        def worker(document_number):
            access = UsptoDocumentAccess(document_number=document_number)
            return access.get_page_url()
        run_examples(worker)
