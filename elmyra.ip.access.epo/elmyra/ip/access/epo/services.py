# -*- coding: utf-8 -*-
# (c) 2013 Andreas Motl, Elmyra UG
import logging
import requests
from pyramid.threadlocal import get_current_request
from cornice import Service
from cornice.util import json_error
from elmyra.ip.access.epo.util import object_attributes_to_dict

log = logging.getLogger(__name__)


# ------------------------------------------
#   services
# ------------------------------------------
ops_published_data_search_service = Service(
    name='ops-published-data-search',
    path='/api/ops/published-data/search',
    description="OPS search interface")



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
    url_tpl = "http://ops.epo.org/3.1/rest-services/published-data/search/{constituents}"
    url = url_tpl.format(constituents=constituents)
    response = requests.get(url, headers={'Accept': 'application/json'}, params={'q': query, 'Range': range})

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
