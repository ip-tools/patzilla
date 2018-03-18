# -*- coding: utf-8 -*-
# (c) 2015-2018 Andreas Motl, Elmyra UG
from __future__ import absolute_import
import logging
from cornice.service import Service
from pyramid.httpexceptions import HTTPBadRequest, HTTPNotFound
from patzilla.access.epo.espacenet.client import espacenet_claims, espacenet_description

logger = logging.getLogger(__name__)

status_upstream_espacenet = Service(
    name='status_espacenet',
    path='/api/status/upstream/epo/espacenet',
    description="Checks EPO espacenet upstream for valid response")

@status_upstream_espacenet.get()
def status_upstream_espacenet_handler(request):
    data = espacenet_claims_handler('EP666666')
    assert data, 'Empty response from Espacenet'
    return "OK"


def espacenet_claims_handler(patent):
    try:
        claims = espacenet_claims(patent)

    except KeyError as ex:
        logger.error('No details at Espacenet: %s %s', type(ex), ex)
        raise HTTPNotFound(ex)

    except ValueError as ex:
        logger.error('Fetching details from Espacenet failed: %s %s', type(ex), ex)
        raise HTTPBadRequest(ex)

    return claims

def espacenet_description_handler(patent):
    try:
        description = espacenet_description(patent)

    except KeyError as ex:
        logger.error('No details at Espacenet: %s %s', type(ex), ex)
        raise HTTPNotFound(ex)

    except ValueError as ex:
        logger.error('Fetching details from Espacenet failed: %s %s', type(ex), ex)
        raise HTTPBadRequest(ex)

    return description

