# -*- coding: utf-8 -*-
# (c) 2014-2018 Andreas Motl <andreas.motl@ip-tools.org>
import os
import json
import logging
import requests
import xmlrpclib
from StringIO import StringIO
from ConfigParser import NoOptionError
from lxml import etree as ET
from lxml.builder import E
from cornice.util import to_list
from beaker.cache import cache_region, region_invalidate
from pyramid.httpexceptions import HTTPNotFound
from patzilla.util.network.requests_xmlrpclib import RequestsTransport
from patzilla.util.numbers.normalize import normalize_patent, depatisconnect_alternatives
from patzilla.util.web.util.xmlrpclib import XmlRpcTimeoutServer

log = logging.getLogger(__name__)


# ------------------------------------------
#   bootstrapping
# ------------------------------------------
use_https = False
archive_service_baseurl = None
def includeme(config):
    global use_https
    global archive_service_baseurl
    datasource_settings = config.registry.datasource_settings

    try:
        archive_service_baseurl = datasource_settings.datasource.depatisconnect.api_uri
    except:
        raise NoOptionError('api_uri', 'datasource_depatisconnect')

    if archive_service_baseurl.startswith('https'):
        use_https = True


class NotConfiguredError(Exception):
    pass


client = None
def get_client():
    global client
    if not client:
        client = requests.Session()
    return client


def sanity_check():
    if archive_service_baseurl is None:
        raise NotConfiguredError('Data source DEPATISconnect not configured')


def run_acquisition(document_number, doctypes=None):

    sanity_check()

    numbers = to_list(document_number)
    doctypes = doctypes or 'xml'
    doctypes = to_list(doctypes)
    log.info('PDF archive acquisition for doctypes={doctypes}, numbers={numbers}'.format(doctypes=doctypes, numbers=numbers))

    # v1: Native xmlrpclib
    #with XmlRpcTimeoutServer(archive_service_baseurl + '/RPC2', 15) as server:
    #    return server.runAcquisition(numbers, doctypes)

    # v2: With "requests" transport
    url = archive_service_baseurl + '/RPC2'
    transport = RequestsTransport(session=get_client(), timeout=(2, 17))
    transport.use_https = use_https
    server = xmlrpclib.ServerProxy(url, transport=transport)
    return server.runAcquisition(numbers, doctypes)

def fetch_xml(number):

    sanity_check()

    # /download/xml:docinfo/DE202014004373U1.xml?nodtd=1&fastpath=true
    url_tpl = archive_service_baseurl + '/download/xml:docinfo/{number}.xml?nodtd=1&fastpath=true'
    url = url_tpl.format(number=number)
    response = get_client().get(url, timeout=(2, 17))
    return response

def fetch_pdf(number, attempt=1):
    return fetch_pdf_real(number)

@cache_region('static')
def fetch_pdf_real(number):

    log.info('PDF {}: Accessing DEPATISconnect server'.format(number))

    sanity_check()

    # /download/pdf/EP666666B1.pdf
    url_tpl = archive_service_baseurl + '/download/pdf/{number}.pdf?fastpath=true'
    url = url_tpl.format(number=number)
    response = get_client().get(url, timeout=(2, 90))
    if response.status_code == 200:
        payload = response.content
        if payload:
            return payload
        else:
            raise HTTPNotFound('Empty PDF for document {0} found in archive'.format(number))

    else:
        raise HTTPNotFound('No PDF for document {0} found in archive'.format(number))

@cache_region('static', 'get_xml')
def get_xml(number):
    """
    Fetch XML from EPD archive service
    """
    number_normalized = normalize_patent(number)

    # 2015-01-13: apply patentnumber fixes for getting more out of DEPATISconnect
    numbers = depatisconnect_alternatives(number_normalized)

    for number_real in numbers:
        try:
            return get_xml_real(number_real)
        except KeyError:
            continue

    raise KeyError('No XML document for "{0}" at DPMA'.format(number))

def invalidate_xml(number):
    number_normalized = normalize_patent(number)
    region_invalidate(get_xml, None, 'get_xml', number_normalized)

def get_xml_real(number):

    response = fetch_xml(number)

    if response.status_code == 200:
        return response.content

    else:
        raise ValueError('Retrieving XML document for "{0}" from DPMA failed'.format(number))

    """
    elif response.status_code == 404:

        # fetch number from remote source and try again once
        if run_acquisition(number):
            response = fetch_xml(number)
            if response.status_code == 200:
                return response.content

        raise KeyError('No XML document for "{0}" at DPMA'.format(number))
    """

def get_claims_or_description(document_number, xpath):
    """
    Extract text and language from "claims" or "description" XML elements
    """

    xml = get_xml(document_number)
    tree = ET.parse(StringIO(xml))

    try:
        element = tree.xpath(xpath)[0]
        content = ET.tostring(element)
        content = content.strip(' \n')
    except IndexError:
        element = None
        content = ''

    try:
        lang = tree.xpath(xpath + '/@olan')[0]
    except IndexError:
        lang = None

    response = {
        'xml': content,
        'lang': lang,
    }

    return response, element


def get_abstracts(document_number, xpath):
    """
    Extract text and language from "Ab" XML elements (abstracts)
    """

    xml = get_xml(document_number)
    tree = ET.parse(StringIO(xml))

    content = ''
    elements = tree.xpath(xpath)
    for element in elements:
        content += ET.tostring(element)
    content = content.strip(' \n')

    languages = tree.xpath(xpath + '/@lancode')
    languages = [item.upper() for item in languages]
    lang = ','.join(languages)

    response = {
        'xml': content,
        'lang': lang,
    }

    return response, elements


def depatisconnect_claims(document_number, invalidate=False):
    """
    Return DEPATISconnect claims fulltext
    Manipulate XML to visually enumerate claims sections in HTML
    """

    # invalidate cache
    if invalidate:
        invalidate_xml(document_number)

    response, content = get_claims_or_description(document_number, '/DocInfoRes/Result/application-body/claims')

    # visually enumerate list of claims
    for claim in content.xpath('claim'):

        # get number of claim section
        claim_number = claim.xpath('@num')[0]

        # put number before section
        claim_number_stripped = claim_number.lstrip('0')
        if '<claim-text><b>{}</b>'.format(claim_number_stripped) not in ET.tostring(claim):
            claim.insert(0, E.span(claim_number + '. '))

        # put some space after section
        claim.append(E.br())
        claim.append(E.br())

    # re-serialize manipulated dom
    response['xml'] = ET.tostring(content)

    return response

def depatisconnect_description(document_number):
    """
    Return DEPATISconnect description fulltext
    """
    response, content = get_claims_or_description(document_number, '/DocInfoRes/Result/application-body/description')
    response['source'] = 'depatisconnect'
    return response


def depatisconnect_abstracts(document_number, language=None, invalidate=False):
    """
    Return DEPATISconnect abstract, optionally filtered by language
    """

    # invalidate cache
    if invalidate:
        invalidate_xml(document_number)

    xpath = '/DocInfoRes/Result/Bibl/Ab'
    if language:
        xpath += '[@lancode="{0}"]'.format(language.lower())
    response, content = get_abstracts(document_number, xpath)
    return response


if __name__ == '__main__':

    """
    About
    =====
    Run requests to data provider "DEPATISconnect" from the command line.

    Synopsis
    ========
    ::

        export PATZILLA_CONFIG=patzilla/config/development-local.ini

        python patzilla/access/dpma/depatisconnect.py
        python patzilla/access/dpma/depatisconnect.py | jq --raw-output '.xml'
        python patzilla/access/dpma/depatisconnect.py | jq .
        python patzilla/access/dpma/depatisconnect.py | jq --raw-output '.xml' | xmllint --format -
    """

    from patzilla.util.web.pyramid.commandline import setup_commandline_pyramid
    configfile = os.environ['PATZILLA_CONFIG']

    env = setup_commandline_pyramid(configfile)
    logger = logging.getLogger(__name__)

    # Populate archive_service_baseurl again because "includeme" runs in a different thread
    registry = env['registry']
    archive_service_baseurl = registry.datasource_settings.datasource.depatisconnect.api_uri
    if archive_service_baseurl.startswith('https'):
        use_https = True

    #response = depatisconnect_abstracts('DE19653398A1', 'DE')
    #response = depatisconnect_description('DE19653398A1')

    #response = depatisconnect_abstracts('DE0001301607B', 'DE')
    #response = depatisconnect_description('DE1301607B')
    #response = depatisconnect_description('DE7909160U1')
    #response = depatisconnect_abstracts('DE7909160U1', 'DE')

    #print depatisconnect_claims('US2014250599A1')
    response = depatisconnect_claims('US2014339530A1')
    #response = depatisconnect_claims('DE102006019883A1')

    # Failed on 2018-04-23
    #response = depatisconnect_claims('USD813591S')

    print json.dumps(response)
