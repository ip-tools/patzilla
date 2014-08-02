# -*- coding: utf-8 -*-
# (c) 2014 Andreas Motl, Elmyra UG
import requests
from StringIO import StringIO
from lxml import etree as ET
from lxml.builder import E
from beaker.cache import cache_region
from elmyra.ip.util.numbers.normalize import normalize_patent

@cache_region('static')
def get_xml(number):
    """
    Fetch XML from EPD archive service
    """
    number_normalized = normalize_patent(number)
    # ***REMOVED***/download/xml:docinfo/DE202014004373U1.xml?nodtd=1
    url_tpl = '***REMOVED***/download/xml:docinfo/{number}.xml?nodtd=1'
    url = url_tpl.format(number=number_normalized)
    response = requests.get(url, verify=False)
    if response.status_code == 200:
        return response.content
    elif response.status_code == 404:
        raise KeyError('No XML document for "{0}" at DEPATISconnect'.format(number))
    else:
        raise ValueError('Retrieving XML document for "{0}" from DEPATISconnect failed'.format(number))


def get_xml_part(document_number, xpath):
    """
    Extract text and language from claims or description XML nodes
    """

    xml = get_xml(document_number)
    tree = ET.parse(StringIO(xml))

    content = tree.xpath(xpath)[0]
    payload = ET.tostring(content)

    lang = tree.xpath(xpath + '/@olan')[0]

    response = {
        'xml': payload,
        'lang': lang,
    }

    return response, content

def depatisconnect_claims(document_number):
    """
    Return DEPATISconnect claims fulltext
    Manipulate XML to visually enumerate claims sections in HTML
    """
    response, content = get_xml_part(document_number, '/DocInfoRes/Result/application-body/claims')

    # visually enumerate list of claims
    for claim in content.xpath('claim'):

        # get number of claim section
        claim_number = claim.xpath('@num')[0]

        # put number before section
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
    response, content = get_xml_part(document_number, '/DocInfoRes/Result/application-body/description')
    return response
