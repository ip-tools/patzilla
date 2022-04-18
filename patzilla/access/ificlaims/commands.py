# -*- coding: utf-8 -*-
# (c) 2015-2022 Andreas Motl <andreas.motl@ip-tools.org>
"""
About
=====
Run requests to search provider "IFI CLAIMS Direct" from the command line.

Synopsis
========
Direct mode, without configuration file::

    export IFICLAIMS_API_URI=https://cdws21.ificlaims.com
    export IFICLAIMS_API_USERNAME=acme
    export IFICLAIMS_API_PASSWORD=10f8GmWTz
    python -m patzilla.access.ificlaims.commands

Use configuration file::

    python -m patzilla.access.ificlaims.commands patzilla/config/development-local.ini
    python -m patzilla.access.ificlaims.commands patzilla/config/development-local.ini | jq .
    python -m patzilla.access.ificlaims.commands patzilla/config/development-local.ini | xmllint --format -

Todo
====
- Pass output type (JSON/XML) via parameter

"""
import json

from patzilla.access.ificlaims import get_ificlaims_client
from patzilla.boot.cache import configure_cache_backend
from patzilla.boot.config import BootConfiguration
from patzilla.util.config import get_configfile_from_commandline
from patzilla.util.data.container import SmartBunch
from patzilla.boot.framework import setup_pyramid


def make_request(client):

    #results = client.search('*:*')
    #pprint(results)

    #results = client.search('pa:siemens', 0, 10)
    #results = client.search('pa:siemens OR pa:bosch', 0, 10)
    #results = client.search('pa:(siemens OR bosch)', 0, 10)
    #results = client.search('text:"solar energy"', 0, 10)
    results = client.search(SmartBunch({'expression': 'text:solar energy'}), SmartBunch({'offset': 0, 'limit': 10}))
    #results = client.search(SmartBunch({'expression': '{!complexphrase inOrder=true}"siemen* *haus"'}), SmartBunch({'offset': 0, 'limit': 10}))
    #results = client.search(u'text:抑血管生成素的药物用途', 0, 10)
    #results = client.search(u'text:放射線を照射する放射線源と', 0, 10)
    #results = client.search(SmartBunch({'expression': 'pnctry:(de OR ep OR wo OR cn OR jp OR tw) AND pa:"taiwan paiho" AND pd:[20170101 TO 20170731]'}), SmartBunch({'offset': 0, 'limit': 50}))

    #results = client.text_fetch('US-20100077592-A1')
    #results = client.text_fetch('CN-1055497-A')
    #results = client.text_fetch('PL-2543232-T3')
    #results = client.text_fetch('CA-2895851-A1')
    #results = client.text_fetch('CA-167637-S')
    #results = json.loads(client.text_fetch('CA-2886702-A1', 'json'))
    #results = json.loads(client.text_fetch('CA-2895852-A1', 'json'))
    #results = json.loads(client.text_fetch('CA-108104-S', 'json'))

    #results = json.loads(client.text_fetch('KR-20160114950-A', 'json'))
    #print json.dumps(results)

    #results = client.text_fetch('KR-20160114950-A', 'xml')
    #print results

    #results = client.attachment_list('CN-1055497-A')
    #pprint(results)

    #blob = client.pdf_fetch('US-20100077592-A1')
    #blob = client.pdf_fetch('CN-1055497-A')
    #blob = client.pdf_fetch('CN-1055498-A')
    #blob = client.pdf_fetch('CN-1059488-A')
    #print blob

    # 2015-09-07
    #results = client.text_fetch('SE-9400081-D0')
    #results = client.text_fetch('SE-9400081-A')
    #results = client.text_fetch('SE-9400081-L')
    #print results

    #results = client.text_fetch('SE-9400081-L', format='json')
    #pprint(json.loads(results))

    # 2017-10-12
    #results = client.text_fetch('JP-2017173854-A')
    #results = client.text_fetch('KR-20170103976-A', 'json')
    #results = client.text_fetch('JP-2017128728-A', 'json')
    #print json.dumps(json.loads(results))

    #blob = client.pdf_fetch('SE-9400081-D0')
    #blob = client.pdf_fetch('SE-9400081-A')
    #blob = client.pdf_fetch('SE-9400081-L')

    #blob = client.pdf_fetch('EP-0666666-A2')
    #blob = client.tif_fetch('EP-0666666-A2')
    #print blob

    return results


if __name__ == '__main__':
    """
    Demo program for accessing different IFI CLAIMS services in a high-level manner.
    """

    # Create a Pyramid runtime environment.
    env = setup_pyramid(
        configfile=get_configfile_from_commandline(),
        bootconfiguration=BootConfiguration(datasources=["ificlaims"]),
    )

    # The IFI CLAIMS data source relies heavily on caching.
    configure_cache_backend("filesystem")

    # Get hold of data source client utility.
    client = get_ificlaims_client()

    results = make_request(client)
    print(json.dumps(results, indent=2))
