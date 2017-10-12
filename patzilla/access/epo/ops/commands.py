# -*- coding: utf-8 -*-
# (c) 2014-2017 Andreas Motl, Elmyra UG
import sys
import json
import logging
from patzilla.access.epo.ops.api import OPS_API_URI
from patzilla.access.epo.ops.client import IOpsClientPool
from patzilla.util.web.pyramid.commandline import setup_commandline_pyramid

"""
About
=====
Run requests to search provider "EPO OPS" from the command line.

Synopsis
========
::

    python patzilla/access/epo/ops/commands.py patzilla/config/development-local.ini
    python patzilla/access/epo/ops/commands.py patzilla/config/development-local.ini | jq .
    python patzilla/access/epo/ops/commands.py patzilla/config/development-local.ini | xmllint --format -

"""

def json_request(client, url, parameters, **kwargs):

    response = client.get(url, headers={'Accept': 'application/json'}, params=parameters, **kwargs)

    logger.info('Response information')
    logger.info('status: %s', response.status_code)
    logger.info('method: %s', response.request.method)
    logger.info('url:    %s', response.request.url)
    #if response.status_code == 200:
    logger.info('headers:\n%s', json.dumps(dict(response.headers), indent=4))
    #print 'response:'; print response.content
    logger.info('response body:')
    print json.dumps(response.json(), indent=4)

def tiff_request(client, url, parameters, **kwargs):
    response = client.get(url, params=parameters, **kwargs)
    #print response
    print response.content

if __name__ == '__main__':

    configfile = sys.argv[1]

    env = setup_commandline_pyramid(configfile)
    logger = logging.getLogger(__name__)

    # Get hold of data source client utility
    registry = env['registry']
    pool = registry.getUtility(IOpsClientPool)
    client = pool.get('system')

    url = '{baseuri}/published-data/search/biblio'.format(baseuri=OPS_API_URI)

    #json_request(ops_session, url, {'q': 'pn=EP666666', 'Range': '1-10'})
    #json_request(ops_session, url, {'q': 'pn=EP666666', 'Range': '1-10'}, provoke_failure=True)

    #json_request(client, url, {'q': 'pn=DE142829T1', 'Range': '1-10'})
    json_request(client, url, {'q': 'pn=KR20000069056A', 'Range': '1-10'})

    #tiff_request(client, '{baseuri}/published-data/images/TW/201721043/A/fullimage.pdf'.format(baseuri=OPS_API_URI), {'Range': '19'})
