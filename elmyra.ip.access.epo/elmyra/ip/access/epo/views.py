from elmyra.ip.access.dpma.dpmaregister import DpmaRegisterAccess
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.response import Response
from pyramid.url import route_path
from pyramid.view import view_config

def includeme(config):
    config.add_route('ops-browser', '/ops/browser')
    config.add_route('jump-dpmaregister', '/office/dpma/register/application/{document_number}')
    config.add_route('angry-cats', '/angry-cats')


@view_config(route_name='ops-browser', renderer='elmyra.ip.access.epo:templates/ops-chooser.mako')
def opsbrowser(request):
    return {'project': 'elmyra.ip.access.epo'}

@view_config(route_name='jump-dpmaregister')
def jump_dpmaregister(request):
    document_number = request.matchdict.get('document_number')
    redirect = request.params.get('redirect')
    if document_number:
        dra = DpmaRegisterAccess()
        url = dra.get_document_url(document_number)
        if url and redirect:
            return HTTPFound(location=url)

    return HTTPNotFound('Could not find application number "{0}" in DPMAregister'.format(document_number))


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
