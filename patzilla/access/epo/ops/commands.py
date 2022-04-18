# -*- coding: utf-8 -*-
# (c) 2014-2022 Andreas Motl <andreas.motl@ip-tools.org>
"""
About
=====
Run requests to search provider "EPO OPS" from the command line.

Synopsis
========
Direct mode, without configuration file::

    export OPS_API_CONSUMER_KEY=y3A0G86cmcij0OQU69VYGTJ4JGxUN8EVG
    export OPS_API_CONSUMER_SECRET=rrXdr5WA7x9tudmP
    python -m patzilla.access.epo.ops.commands

Use configuration file::

    python -m patzilla.access.epo.ops.commands patzilla/config/development-local.ini
    python -m patzilla.access.epo.ops.commands patzilla/config/development-local.ini | jq .
    python -m patzilla.access.epo.ops.commands patzilla/config/development-local.ini | xmllint --format -

"""
import json
import logging

from requests import HTTPError

from patzilla.access.epo.ops.api import OPS_API_URI, get_ops_client
from patzilla.boot.config import BootConfiguration
from patzilla.boot.framework import setup_pyramid
from patzilla.util.config import get_configfile_from_commandline

logger = logging.getLogger(__name__)


def mangle_range_parameter(parameters):

    range = parameters.get("Range", "1-10")
    try:
        del parameters["Range"]
    except KeyError:
        pass

    return range


def json_request(client, url, parameters=None, use_get=False):

    parameters = parameters or {}

    # Decode `range` parameter.
    range = mangle_range_parameter(parameters)

    # Submit request to OPS.
    response = client._make_request(
        url, data=parameters, extra_headers={"X-OPS-Range": range}, use_get=use_get,
    )

    logger.info('Response information')
    logger.info('status: %s', response.status_code)
    logger.info('method: %s', response.request.method)
    logger.info('url:    %s', response.request.url)
    logger.info('headers:\n%s', json.dumps(dict(response.headers), indent=2))
    if response.status_code == 200:
        if response.headers["content-type"].startswith("application/json"):
            logger.info('body:   ')
            print(json.dumps(response.json(), indent=2))
            return
    elif response.status_code == 404:
        logger.error('Resource "{}" not found. Parameters={}'.format(url, parameters))
        return

    logger.error("Request did not return JSON. Response was:\n{}".format(response.content))


def image_request(client, url, parameters):

    # Decode `range` parameter.
    range = mangle_range_parameter(parameters)

    # Submit request to OPS.
    response = client._make_request(
        #url, data=parameters, extra_headers={"X-OPS-Range": range}
        url, data=parameters, extra_headers={"Accept": "application/pdf", "X-OPS-Range": range}, use_get=True,
    )

    print response.content


def generic_request(client, url):
    try:
        response = client._make_request(
            url, data={}, extra_headers={"Accept": "*"}, use_get=True,
        )
        return response
    except HTTPError as ex:
        logger.error("EPO OPS request failed: {}".format(ex))


if __name__ == '__main__':  # pragma: nocover
    """
    Demo program for accessing different EPO OPS services in a low-level manner.
    """

    # Create a Pyramid runtime environment.
    env = setup_pyramid(
        configfile=get_configfile_from_commandline(),
        bootconfiguration=BootConfiguration(datasources=["ops"]),
    )

    # Get hold of data source client utility.
    client = get_ops_client()

    # 0. Access API base URL.
    """
    response = generic_request(client, "https://ops.epo.org/3.2")
    if response:
        # print(response.content)
        assert "<title>EPO - Open Patent Services (OPS)</title>" in response.content
        print("Ready.")
    """

    # 2.3.4. Data usage API
    # url = '{baseuri}/me/stats/usage?timeRange={date_begin}~{date_end}'.format(baseuri=OPS_DEVELOPERS_URI, **locals())
    # url = '{baseuri}/me/stats/usage?timeRange=16/04/2022'.format(baseuri=OPS_DEVELOPERS_URI, **locals())
    # json_request(client, url, {}, use_get=True)

    # 3.1. Published-data services
    url = '{baseuri}/published-data/search/biblio'.format(baseuri=OPS_API_URI)
    # json_request(client, url, {'q': 'pn=EP666666', 'Range': '1-10'})
    # json_request(client, url, {'q': 'pn=DE142829T1', 'Range': '1-10'})
    # json_request(client, url, {'q': 'pn=EP666666', 'Range': '1-10'}, provoke_failure=True)
    json_request(client, url, {'q': 'pn=KR20000069056A', 'Range': '1-10'})

    # 3.1.3. Images inquiry and retrieval
    # image_request(client, '{baseuri}/published-data/images/TW/201721043/A/fullimage.pdf'.format(baseuri=OPS_API_URI), {'Range': '19'})
    # image_request(client, '{baseuri}/published-data/images/EP/0666666/B1/fullimage'.format(baseuri=OPS_API_URI), {'Range': '5'})
    # image_request(client, '{baseuri}/published-data/images/EP/1000000/PA/fullimage'.format(baseuri=OPS_API_URI), {'Range': '3'})
