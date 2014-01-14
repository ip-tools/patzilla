# -*- coding: utf-8 -*-
# (c) 2013 Andreas Motl, Elmyra UG
from elmyra.ip.access.epo.patentutil import split_patent_number
import requests
import logging
from pyramid.threadlocal import get_current_request
from cornice import Service
from cornice.util import json_error
from simplejson.scanner import JSONDecodeError
from elmyra.ip.access.epo.util import object_attributes_to_dict
from elmyra.ip.access.epo.imageutil import tiff_to_png
from elmyra.ip.access.epo.client import oauth_client_create

log = logging.getLogger(__name__)

ops_client = None
def get_ops_client():
    global ops_client
    if not ops_client:
        ops_client = oauth_client_create()
    return ops_client

# ------------------------------------------
#   services
# ------------------------------------------
ops_published_data_search_service = Service(
    name='ops-published-data-search',
    path='/api/ops/published-data/search',
    description="OPS search interface")

ops_firstdrawing_service = Service(
    name='ops-firstdrawing',
    path='/api/ops/{patent}/image/firstdrawing',
    description="OPS firstdrawing interface")

ops_family_publication_service = Service(
    name='ops-family-publication',
    path='/api/ops/{patent}/family/publication',
    description="OPS family publication interface")


# ------------------------------------------
#   handlers
# ------------------------------------------
@ops_published_data_search_service.get(accept="application/json")
def ops_published_data_search_handler(request):
    """Search for published-data at OPS"""

    # constituents: abstract, biblio and/or full-cycle
    constituents = request.params.get('constituents', 'biblio')

    # CQL query string
    query = request.params.get('query', '')

    # range: x-y, maximum delta is 100
    range = request.params.get('range', '1-25')

    return ops_published_data_search(constituents, query, range)


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


@ops_firstdrawing_service.get(renderer='png')
def ops_firstdrawing_handler(request):

    service_url = 'https://ops.epo.org/3.1/rest-services/'

    client = get_ops_client()

    # 1. inquire images
    url_image_inquriy_tpl = 'https://ops.epo.org/3.1/rest-services/published-data/publication/epodoc/{patent}/images'
    patent = request.matchdict['patent']
    url_image_inquriy = url_image_inquriy_tpl.format(patent=patent)
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

    drawing_node = None
    for node in result['ops:document-instance']:
        if node['@desc'] == u'Drawing':
            drawing_node = node
            break

    if drawing_node:
        link = drawing_node['@link']
        url = service_url + link + '.tiff?Range=1'
    else:
        return


    # 2. request first drawing, convert from tiff to png
    # works:
    # http://ops.epo.org/3.1/rest-services/published-data/images/EP/1000000/PA/firstpage.png?Range=1
    # http://ops.epo.org/3.1/rest-services/published-data/images/US/20130311929/A1/thumbnail.tiff?Range=1
    #print "image url:", url
    response = client.get(url)
    if response.status_code != 200:
        print response
        print response.headers
        print response.content
        return

    tiff = response.content
    png = tiff_to_png(tiff)
    return png



@ops_family_publication_service.get(renderer='xml')
def ops_family_publication_handler(request):
    """
    Download requested family publication information from OPS
    e.g. http://ops.epo.org/3.1/rest-services/family/publication/docdb/EP.1491501.A1/biblio,legal
    """

    url_tpl = 'https://ops.epo.org/3.1/rest-services/family/publication/docdb/{patent}/{constituents}'

    # split patent number
    patent = split_patent_number(request.matchdict.get('patent'))
    patent_dotted = '.'.join([patent['country'], patent['number'], patent['kind']])

    # constituents: biblio, legal, xxx?
    constituents = request.params.get('constituents', 'biblio')

    url = url_tpl.format(patent=patent_dotted, constituents=constituents)
    client = get_ops_client()
    #response = client.get(url, headers={'Accept': 'application/json'})
    response = client.get(url, headers={'Accept': 'text/xml'})
    #print "response:", response.content

    return response.content
