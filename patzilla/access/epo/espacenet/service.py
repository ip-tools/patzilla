# -*- coding: utf-8 -*-
# (c) 2015-2018 Andreas Motl, Elmyra UG

import logging

from fastapi import APIRouter, HTTPException

from patzilla.access.epo.espacenet.api import espacenet_claims, espacenet_description

logger = logging.getLogger(__name__)

router = APIRouter(tags=["espacenet"])


@router.get("/api/status/upstream/epo/espacenet", name="status_espacenet",
            summary="Checks EPO espacenet upstream for valid response")
def status_upstream_espacenet_handler():
    data = espacenet_claims_handler('EP666666')
    assert data, 'Empty response from Espacenet'
    return "OK"


def espacenet_claims_handler(patent):
    try:
        claims = espacenet_claims(patent)

    except KeyError as ex:
        logger.error('No details at Espacenet: %s %s', type(ex), ex)
        raise HTTPException(404, str(ex))

    except ValueError as ex:
        logger.error('Fetching details from Espacenet failed: %s %s', type(ex), ex)
        raise HTTPException(400, str(ex))

    return claims

def espacenet_description_handler(patent):
    try:
        description = espacenet_description(patent)

    except KeyError as ex:
        logger.error('No details at Espacenet: %s %s', type(ex), ex)
        raise HTTPException(404, str(ex))

    except ValueError as ex:
        logger.error('Fetching details from Espacenet failed: %s %s', type(ex), ex)
        raise HTTPException(400, str(ex))

    return description
