# -*- coding: utf-8 -*-
# (c) 2014 Andreas Motl, Elmyra UG
import logging
import requests
from beaker.cache import cache_region
from pyramid.httpexceptions import HTTPNotFound
from elmyra.ip.util.numbers.normalize import normalize_patent

log = logging.getLogger(__name__)

def fetch_pdf(number):
    number_normalized = normalize_patent(number)
    return fetch_pdf_real(number_normalized)

@cache_region('static')
def fetch_pdf_real(number):

    log.info('PDF - trying archive (1): {0}'.format(number))

    # ***REMOVED***/download/pdf/EP666666B1.pdf
    url_tpl = '***REMOVED***/download/pdf/{number}.pdf'
    url = url_tpl.format(number=number)
    response = requests.get(url, verify=False)
    if response.status_code == 200:
        payload = response.content
        if payload:
            return payload
        else:
            raise HTTPNotFound('Empty PDF for document {0} found in archive'.format(number))

    else:
        raise HTTPNotFound('No PDF for document {0} found in archive'.format(number))
