# -*- coding: utf-8 -*-
# (c) 2013,2014 Andreas Motl, Elmyra UG
import logging
from pyramid.httpexceptions import HTTPNotFound, HTTPError
from pyramid.threadlocal import get_current_request
from cornice.util import json_error
from simplejson.scanner import JSONDecodeError
from elmyra.ip.access.epo.util import object_attributes_to_dict
from elmyra.ip.access.epo.client import oauth_client_create

log = logging.getLogger(__name__)


ops_client = None
def get_ops_client():
    global ops_client
    if not ops_client:
        ops_client = oauth_client_create()
    return ops_client


def ops_published_data_search(constituents, query, range):

    # query EPO OPS REST service
    url_tpl = "https://ops.epo.org/3.1/rest-services/published-data/search/{constituents}"
    url = url_tpl.format(constituents=constituents)

    # v1: anonymous
    #client = requests

    # v2: with oauth
    client = get_ops_client()

    response = client.get(url, headers={'Accept': 'application/json'}, params={'q': query, 'Range': range})
    #print "response:", response

    #print "url:", url
    #print "status-code:", response.status_code

    if response.status_code == 200:
        #print "content-type:", response.headers['content-type']
        if response.headers['content-type'] == 'application/json':
            return response.json()
        else:
            return {}
    else:
        request = get_current_request()
        response_dict = object_attributes_to_dict(response, ['url', 'status_code', 'reason', 'headers', 'content'])
        request.errors.add('ops-published-data-search', 'http-response', response_dict)
        response = json_error(request.errors)
        response.status = 500
        #print "response:", response
        raise response


def inquire_images(patent):

    url_image_inquriy_tpl = 'https://ops.epo.org/3.1/rest-services/published-data/publication/epodoc/{patent}/images'
    url_image_inquriy = url_image_inquriy_tpl.format(patent=patent)

    error_msg_access = 'No image information for document "{0}"'.format(patent)
    error_msg_process = 'Error while processing image information for document "{0}"'.format(patent)

    client = get_ops_client()
    response = client.get(url_image_inquriy, headers={'Accept': 'application/json'})
    if response.status_code != 200:
        log.warn(error_msg_access + '\n' + str(response) + '\n' + str(response.content))
        if response.status_code in [404]:
            error = HTTPNotFound(error_msg_access)
        else:
            error = HTTPError(error_msg_access)
            error.status_code = response.status_code
        raise error

    try:
        data = response.json()
    except JSONDecodeError as ex:
        error_msg_process += ': {0}'.format(str(ex))
        log.error(error_msg_process)
        error = HTTPError(error_msg_process)
        error.status_code = 500
        raise error

    result = data['ops:world-patent-data']['ops:document-inquiry']['ops:inquiry-result']

    info = {}
    for node in result['ops:document-instance']:
        key = node['@desc']
        info[key] = node

    return info


def ops_safe_request(url):
    client = get_ops_client()
    response = client.get(url)
    if response.status_code != 200:
        print response
        print response.headers
        print response.content
    return response


def get_ops_image_link_url(link, format, page=1):
    service_url = 'https://ops.epo.org/3.1/rest-services/'
    url_tpl = '{service_url}{link}.{format}?Range={page}'
    url = url_tpl.format(**locals())
    return url


def get_ops_image(document, page, kind, format):

    kind_requested = kind
    if kind_requested == 'FullDocumentDrawing':
        kind = 'FullDocument'

    # 1. inquire images to compute url to image resource
    image_info = inquire_images(document)
    drawing_node = image_info.get(kind)
    if drawing_node:
        link = drawing_node['@link']
        if kind_requested == 'FullDocumentDrawing':
            sections = drawing_node['ops:document-section']
            for section in sections:
                if section['@name'] == 'DRAWINGS':
                    start_page = int(section['@start-page'])
                    page = start_page + page - 1
        url = get_ops_image_link_url(link, format, page)
    else:
        msg = 'No image information for document "{0}" for kind "{1}"'.format(document, kind)
        log.warn(msg)
        raise HTTPNotFound(msg)

    response = ops_safe_request(url)
    payload = response.content
    return payload
