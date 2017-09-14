# -*- coding: utf-8 -*-
# (c) 2015-2016 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
# patzilla.access.ificlaims.cli: Adapter to search provider "IFI Claims Direct"
import sys
import json
import logging
from pprint import pprint
from patzilla.access.ificlaims.clientpool import IFIClaimsClientFactory

if __name__ == '__main__':
    """
    Synopsis::

        python patzilla/access/ificlaims/commands.py | jq .
        python patzilla/access/ificlaims/commands.py | xmllint --format -

    Todo:
        - Pass output type (json/xml) via parameter

    """

    logging.basicConfig(level='INFO')

    # configure cache manager
    from beaker.cache import CacheManager
    from beaker.util import parse_cache_config_options
    cache_opts = {
        'cache.type': 'memory',
        'cache.regions': 'static,search',
        }
    cache = CacheManager(**parse_cache_config_options(cache_opts))

    api_uri  = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]

    client = IFIClaimsClientFactory(api_uri, credentials={'username': username, 'password': password}).client_create()
    client.login()

    #results = client.search('*:*')
    #pprint(results)

    #results = client.search('pa:siemens', 0, 10)
    #results = client.search('pa:siemens OR pa:bosch', 0, 10)
    #results = client.search('pa:(siemens OR bosch)', 0, 10)
    #results = client.search('text:"solar energy"', 0, 10)
    #results = client.search('text:solar energy', 0, 10)
    #results = client.search(u'text:抑血管生成素的药物用途', 0, 10)
    #results = client.search(u'text:放射線を照射する放射線源と', 0, 10)
    #pprint(results)

    #results = client.text_fetch('US-20100077592-A1')
    #results = client.text_fetch('CN-1055497-A')
    #results = client.text_fetch('PL-2543232-T3')
    #results = client.text_fetch('CA-2895851-A1')
    #results = client.text_fetch('CA-167637-S')
    #results = json.loads(client.text_fetch('CA-2886702-A1', 'json'))
    #results = json.loads(client.text_fetch('CA-2895852-A1', 'json'))
    results = json.loads(client.text_fetch('CA-108104-S', 'json'))

    print json.dumps(results)

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

    #blob = client.pdf_fetch('SE-9400081-D0')
    #blob = client.pdf_fetch('SE-9400081-A')
    #blob = client.pdf_fetch('SE-9400081-L')

    #blob = client.pdf_fetch('EP-0666666-A2')
    #blob = client.tif_fetch('EP-0666666-A2')
    #print blob
