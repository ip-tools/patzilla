# -*- coding: utf-8 -*-
# (c) 2013,2014 Andreas Motl, Elmyra UG
import logging
from pyramid.httpexceptions import HTTPNotFound, HTTPError, HTTPInternalServerError
from pyramid.threadlocal import get_current_request
from cornice.util import json_error, to_list
from simplejson.scanner import JSONDecodeError
from beaker.cache import cache_region
from elmyra.ip.access.epo.util import object_attributes_to_dict
from elmyra.ip.access.epo.client import oauth_client_create
from elmyra.ip.access.epo.imageutil import tiff_to_png, pdf_join, pdf_set_metadata, pdf_make_metadata
from elmyra.ip.util.numbers.common import split_patent_number

log = logging.getLogger(__name__)


ops_service_url = 'https://ops.epo.org/3.1/rest-services/'


ops_client = None
def get_ops_client():
    global ops_client
    if not ops_client:
        ops_client = oauth_client_create()
    return ops_client


@cache_region('search')
def ops_published_data_search(constituents, query, range):

    # query EPO OPS REST service
    url_tpl = "https://ops.epo.org/3.1/rest-services/published-data/search/{constituents}"
    url = url_tpl.format(constituents=constituents)

    # v1: anonymous
    #import requests; client = requests

    # v2: with oauth
    client = get_ops_client()

    response = client.get(url, headers={'Accept': 'application/json'}, params={'q': query, 'Range': range})

    # TODO: use POST for large "q" requests, move "Range" to "X-OPS-Range" header
    #response = client.post(url, headers={'Accept': 'application/json'}, data={'q': query})

    #print "request-url:", url
    #print "status-code:", response.status_code
    #print "response:", response
    #print "response body:", response.content


    if response.status_code == 200:
        #print "content-type:", response.headers['content-type']
        if response.headers['content-type'] == 'application/json':
            return response.json()
        else:
            return
    else:
        response = handle_error(response, 'ops-published-data-search')
        raise response


@cache_region('search')
def inquire_images(patent):

    p = split_patent_number(patent)
    patent = p['country'] + p['number'] + '.' + p['kind']

    #print "inquire_images:", patent

    url_image_inquriy_tpl = 'https://ops.epo.org/3.1/rest-services/published-data/publication/docdb/{patent}/images'
    url_image_inquriy = url_image_inquriy_tpl.format(patent=patent)

    error_msg_access = 'No image information for document={0}'.format(patent)
    error_msg_process = 'Error while processing image information for document={0}'.format(patent)

    client = get_ops_client()
    response = client.get(url_image_inquriy, headers={'Accept': 'application/json'})
    if response.status_code != 200:

        # make 404s cacheable
        if response.status_code == 404:
            log.warn(error_msg_access)
            return

        else:
            log.error(error_msg_access + '\n' + str(response) + '\n' + str(response.content))
            error = HTTPError(error_msg_access)
            error.status_code = response.status_code

        # TODO: respond with proper json error
        raise error

    try:
        data = response.json()
    except JSONDecodeError as ex:
        # TODO: respond with proper json error
        error_msg_process += ': {0}'.format(str(ex))
        log.error(error_msg_process)
        error = HTTPError(error_msg_process)
        error.status_code = 500
        raise error

    result = data['ops:world-patent-data']['ops:document-inquiry']['ops:inquiry-result']

    info = {}
    for node in to_list(result['ops:document-instance']):
        key = node['@desc']
        info[key] = node

    enrich_image_inquiry_info(info)

    return info


def enrich_image_inquiry_info(info):
    """enrich image inquiry information"""

    meta = {}

    # compute page offset to first drawing
    entry = info.get('FullDocument')
    if entry and entry.has_key('ops:document-section'):
        sections = entry.get('ops:document-section', [])
        for section in to_list(sections):
            if section['@name'] == 'DRAWINGS':
                meta['drawing-start-page'] = int(section['@start-page'])
                break

    # clone number of drawings
    if meta.has_key('drawing-start-page'):
        meta['drawing-total-count'] = info['Drawing']['@number-of-pages']

    info['META'] = meta


def get_ops_image_link_url(link, format, page=1):
    service_url = ops_service_url
    url_tpl = '{service_url}{link}.{format}?Range={page}'
    url = url_tpl.format(**locals())
    return url


@cache_region('static')
def get_ops_image_pdf(document, page):
    payload = get_ops_image(document, page, 'FullDocument', 'pdf')
    return payload

def get_ops_image(document, page, kind, format):

    # http://ops.epo.org/3.1/rest-services/published-data/images/EP/1000000/PA/firstpage.png?Range=1
    # http://ops.epo.org/3.1/rest-services/published-data/images/US/20130311929/A1/thumbnail.tiff?Range=1

    kind_requested = kind
    if kind_requested == 'FullDocumentDrawing':
        kind = 'FullDocument'

    # 1. inquire images to compute url to image resource
    image_info = inquire_images(document)
    if image_info:
        drawing_node = image_info.get(kind)
        if drawing_node:
            link = drawing_node['@link']

            # compute offset to first drawing if special kind "FullDocumentDrawing" is requested
            if kind_requested == 'FullDocumentDrawing':
                start_page = image_info['META'].get('drawing-start-page')
                if start_page:
                    page = page + start_page - 1

            url = get_ops_image_link_url(link, format, page)
        else:
            msg = 'No image information for document={0}, kind={1}'.format(document, kind)
            log.warn(msg)
            # TODO: respond with proper json error
            raise HTTPNotFound(msg)
    else:
        msg = 'No image information for document={0}'.format(document)
        #log.warn(msg)
        # TODO: respond with proper json error
        raise HTTPNotFound(msg)

    client = get_ops_client()
    response = client.get(url)
    if response.status_code == 200:
        payload = response.content
        return payload

    else:
        msg = 'Could not load image for document={document}, kind={kind}, page={page}, format={format}'.format(**locals())
        log.warn('[{code}] {message}'.format(code=response.status_code, message=msg))
        error = HTTPError()
        error.explanation = msg
        error.status_code = response.status_code
        # TODO: respond with proper json error
        raise error


@cache_region('static')
def ops_description(document_number):

    # http://ops.epo.org/3.1/rest-services/published-data/publication/epodoc/EP0666666/description.json

    url_tpl = 'https://ops.epo.org/3.1/rest-services/published-data/publication/epodoc/{document_number}/description.json'
    url = url_tpl.format(document_number=document_number)

    client = get_ops_client()
    response = client.get(url, headers={'Accept': 'application/json'})

    if response.status_code == 200:
        if response.headers['content-type'] == 'application/json':
            return response.json()
        else:
            return
    else:
        response = handle_error(response, 'ops-description')
        raise response

@cache_region('static')
def ops_claims(document_number):

    # http://ops.epo.org/3.1/rest-services/published-data/publication/epodoc/EP0666666/claims.json

    url_tpl = 'https://ops.epo.org/3.1/rest-services/published-data/publication/epodoc/{document_number}/claims.json'
    url = url_tpl.format(document_number=document_number)

    client = get_ops_client()
    response = client.get(url, headers={'Accept': 'application/json'})

    if response.status_code == 200:
        if response.headers['content-type'] == 'application/json':
            return response.json()
        else:
            return
    else:
        response = handle_error(response, 'ops-claims')
        raise response


def handle_error(response, name):
    request = get_current_request()
    response_dict = object_attributes_to_dict(response, ['url', 'status_code', 'reason', 'headers', 'content'])
    response_dict['url'] = response_dict['url'].replace(ops_service_url, '/')
    request.errors.add(name, 'http-response', response_dict)

    response_json = json_error(request.errors)
    response_json.status = response.status_code

    #print "response:", response
    log.warn(request.errors)
    return response_json


@cache_region('static')
def pdf_document_build(patent):

    # 1. collect all single pdf pages
    image_info = inquire_images(patent)
    if not image_info:
        msg = 'No image information for document={0}'.format(patent)
        # TODO: respond with proper json error
        raise HTTPNotFound(msg)

    page_count = int(image_info['FullDocument']['@number-of-pages'])
    log.info('pdf_document_build collecting {0} pages for document {1}'.format(page_count, patent))
    pdf_pages = []
    for page_number in range(1, page_count + 1):
        page = get_ops_image_pdf(patent, page_number)
        pdf_pages.append(page)

    # 2. join single pdf pages
    pdf_document = pdf_join(pages=pdf_pages)

    # 3. add pdf metadata
    page_sections = None
    if image_info['FullDocument'].has_key('ops:document-section'):
        page_sections = image_info['FullDocument']['ops:document-section']
        #pprint(page_sections)

    metadata = pdf_make_metadata(patent, 'digi42, elmyra ip suite', page_count, page_sections)
    pdf_document = pdf_set_metadata(pdf_document, metadata)

    # TODO: 4. add attachments (e.g. xml)

    return pdf_document


def _summarize_metrics(payload, kind):

    metrics = payload['environments'][0]['dimensions'][0]['metrics']
    total_response_size_entries = filter(lambda item: item['name'] == kind, metrics)[0]['values']
    #print total_response_size_entries

    total_response_sizes = map(lambda item: float(item['value']), total_response_size_entries)
    #print total_response_sizes

    total = sum(total_response_sizes)
    return total

def ops_service_usage():
    client = get_ops_client()

    # one day
    #response = client.get('https://ops.epo.org/3.1/developers/me/stats/usage?timeRange=24/02/2014~24/02/2014')

    # misc
    #response = client.get('https://ops.epo.org/3.1/developers/me/stats/usage?timeRange=01/01/2014~24/02/2014')
    #response = client.get('https://ops.epo.org/3.1/developers/me/stats/usage?timeRange=23/02/2014~04/03/2014')

    # all
    response = client.get('https://ops.epo.org/3.1/developers/me/stats/usage?timeRange=26/11/2013~04/03/2014')

    #print response
    #print response.headers
    #print response.content

    payload = response.json()

    total_response_size = _summarize_metrics(payload, 'total_response_size')
    print 'Total response size: {0}G'.format(total_response_size / float(10**9))

    message_count = _summarize_metrics(payload, 'message_count')
    print 'Total message count: {0}'.format(message_count)

if __name__ == '__main__':
    ops_service_usage()
