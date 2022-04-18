# -*- coding: utf-8 -*-
# (c) 2014-2022 Andreas Motl <andreas.motl@ip-tools.org>
"""
About
=====

Acquire first drawing(s) of PDF documents from USPTO servers.


Synopsis
========
::

    # Sweep multiple samples.
    python -m patzilla.access.uspto.image

    # Acquire drawing from specific document.
    python -m patzilla.access.uspto.image US20070231208A1 > US20070231208A1-first-drawing.tiff


Resources
=========

- Applications
  US20160101909A1: https://pdfaiw.uspto.gov/09/2016/19/010/2.pdf

- Publication
  US10194689B2: https://pdfpiw.uspto.gov/89/946/101/5.pdf

"""
import logging
import sys

from patzilla.access.uspto.pdf import fetch_pdf, UsptoPdfSection, run_examples
from patzilla.util.image.convert import pdf_extract_image

log = logging.getLogger(__name__)


def fetch_first_drawing(patent):

    if isinstance(patent, dict):
        docnumber = patent['country'] + patent['number'] + patent['kind']
    else:
        docnumber = patent

    log.info('Fetching first drawing of document {docnumber}'.format(docnumber=docnumber))
    drawing_pdf = fetch_pdf(docnumber, section=UsptoPdfSection.DRAWINGS)
    drawing_tiff = pdf_extract_image(drawing_pdf)
    return drawing_tiff


if __name__ == '__main__':  # pragma: nocover
    """
    Demo program for fetching first drawing(s) of documents from USPTO servers.
    """

    from patzilla.boot.cache import configure_cache_backend
    from patzilla.boot.logging import setup_logging

    setup_logging()

    # configure_cache_backend("memory")
    configure_cache_backend("filesystem")

    if len(sys.argv) == 2:
        number = sys.argv[1]
        print(fetch_first_drawing(number))

    else:
        run_examples(fetch_first_drawing, "len(response)")
