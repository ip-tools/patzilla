# -*- coding: utf-8 -*-
# (c) 2013,2014 Andreas Motl, Elmyra UG
import logging
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
        print "response:", response
        raise response


def inquire_images(patent):

    url_image_inquriy_tpl = 'https://ops.epo.org/3.1/rest-services/published-data/publication/epodoc/{patent}/images'
    url_image_inquriy = url_image_inquriy_tpl.format(patent=patent)

    client = get_ops_client()
    response = client.get(url_image_inquriy, headers={'Accept': 'application/json'})
    #print response
    #print dir(response)
    #print response.content
    print patent, url_image_inquriy, response
    if response.status_code != 200:
        print response
        print response.content
        return

    try:
        data = response.json()
    except JSONDecodeError:
        return
    result = data['ops:world-patent-data']['ops:document-inquiry']['ops:inquiry-result']
    #pprint(result)

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

    # 1. inquire images to compute url to image resource
    image_info = inquire_images(document)
    if image_info:
        drawing_node = image_info.get(kind)
        if drawing_node:
            link = drawing_node['@link']
            url = get_ops_image_link_url(link, format, page)
        else:
            print "WARN: No full image for document '{0}'".format(document)
            return
    else:
        print "WARN: No image information for document '{0}'".format(document)
        return

    response = ops_safe_request(url)
    payload = response.content
    return payload
