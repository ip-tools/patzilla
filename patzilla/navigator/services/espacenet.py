import logging

from cornice import Service
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest

from patzilla.access.epo.espacenet.api import espacenet_abstract, espacenet_claims, espacenet_description

log = logging.getLogger(__name__)


espacenet_abstract_service = Service(
    name='espacenet-abstract',
    path='/api/espacenet/{patent}/abstract',
    description="Espacenet abstract interface")
espacenet_claims_service = Service(
    name='espacenet-claims',
    path='/api/espacenet/{patent}/claims',
    description="Espacenet claims interface")
espacenet_description_service = Service(
    name='espacenet-description',
    path='/api/espacenet/{patent}/description',
    description="Espacenet description interface")


@espacenet_abstract_service.get()
def espacenet_abstract_handler(request):
    patent = request.matchdict['patent']
    #language = request.params.get('language')
    try:
        return espacenet_abstract(patent)

    except KeyError as ex:
        log.error('Problem fetching abstract from Espacenet: %s %s', type(ex), ex)
        raise HTTPNotFound(ex)

    except ValueError as ex:
        log.error('Problem fetching abstract from Espacenet: %s %s', type(ex), ex)
        raise HTTPBadRequest(ex)


@espacenet_claims_service.get()
def espacenet_claims_handler(request):
    # TODO: use jsonified error responses
    patent = request.matchdict['patent']
    try:
        return espacenet_claims(patent)

    except KeyError as ex:
        log.error('Problem fetching claims from Espacenet: %s %s', type(ex), ex)
        raise HTTPNotFound(ex)

    except ValueError as ex:
        log.error('Problem fetching claims from Espacenet: %s %s', type(ex), ex)
        raise HTTPBadRequest(ex)


@espacenet_description_service.get()
def espacenet_description_handler(request):
    # TODO: use jsonified error responses
    patent = request.matchdict['patent']
    try:
        return espacenet_description(patent)

    except KeyError as ex:
        log.error('Problem fetching description from Espacenet: %s %s', type(ex), ex)
        raise HTTPNotFound(ex)

    except ValueError as ex:
        log.error('Problem fetching description from Espacenet: %s %s', type(ex), ex)
        raise HTTPBadRequest(ex)
