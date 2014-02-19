from elmyra.ip.access.dpma.dpmaregister import DpmaRegisterAccess
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.response import Response
from pyramid.url import route_path
from pyramid.view import view_config

def includeme(config):
    config.add_route('ops-browser', '/ops/browser')
    config.add_route('jump-dpmaregister', '/jump/dpma/register')
    config.add_route('angry-cats', '/angry-cats')


@view_config(route_name='ops-browser', renderer='elmyra.ip.access.epo:templates/ops-chooser.mako')
def opsbrowser(request):
    return {'project': 'elmyra.ip.access.epo'}

@view_config(route_name='jump-dpmaregister')
def jump_dpmaregister(request):
    publication_number = request.params.get('pn')
    if publication_number:
        dra = DpmaRegisterAccess()
        url = dra.get_document_url(publication_number)
        if url:
            return HTTPFound(location=url)

    return HTTPNotFound('Could not find publication number "{0}" in DPMAregister'.format(publication_number))


@view_config(name='ops-chooser', renderer='elmyra.ip.access.epo:templates/ops-chooser.mako')
def ops_chooser(request):
    url = route_path('ops-browser', request, _query=request.params)
    return HTTPFound(location=url)

@view_config(name='portfolio-demo', renderer='elmyra.ip.access.epo:templates/portfolio-demo.mako')
def portfolio(request):
    return {'project': 'elmyra.ip.access.epo'}

@view_config(name='angry-cats', renderer='elmyra.ip.access.epo:templates/angry-cats.mako')
def angry_cats(request):
    return {}
