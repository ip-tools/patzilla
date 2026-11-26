import logging

from fastapi import APIRouter, HTTPException

from patzilla.access.epo.espacenet.api import espacenet_abstract, espacenet_claims, espacenet_description

log = logging.getLogger(__name__)

router = APIRouter(tags=["espacenet"])


@router.get("/api/espacenet/{patent}/abstract", name="espacenet-abstract", summary="Espacenet abstract interface")
def espacenet_abstract_handler(patent: str):
    #language = request.params.get('language')
    try:
        return espacenet_abstract(patent)

    except KeyError as ex:
        log.error('Problem fetching abstract from Espacenet: %s %s', type(ex), ex)
        raise HTTPException(404, str(ex))

    except ValueError as ex:
        log.error('Problem fetching abstract from Espacenet: %s %s', type(ex), ex)
        raise HTTPException(400, str(ex))


@router.get("/api/espacenet/{patent}/claims", name="espacenet-claims", summary="Espacenet claims interface")
def espacenet_claims_handler(patent: str):
    # TODO: use jsonified error responses
    try:
        return espacenet_claims(patent)

    except KeyError as ex:
        log.error('Problem fetching claims from Espacenet: %s %s', type(ex), ex)
        raise HTTPException(404, str(ex))

    except ValueError as ex:
        log.error('Problem fetching claims from Espacenet: %s %s', type(ex), ex)
        raise HTTPException(400, str(ex))


@router.get("/api/espacenet/{patent}/description", name="espacenet-description",
            summary="Espacenet description interface")
def espacenet_description_handler(patent: str):
    # TODO: use jsonified error responses
    try:
        return espacenet_description(patent)

    except KeyError as ex:
        log.error('Problem fetching description from Espacenet: %s %s', type(ex), ex)
        raise HTTPException(404, str(ex))

    except ValueError as ex:
        log.error('Problem fetching description from Espacenet: %s %s', type(ex), ex)
        raise HTTPException(400, str(ex))
