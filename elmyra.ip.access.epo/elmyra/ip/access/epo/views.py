from pyramid.response import Response
from pyramid.view import view_config

@view_config(route_name='ops-chooser', renderer='elmyra.ip.access.epo:templates/ops-chooser.mako')
def screening(request):
def includeme(config):
    config.add_route('ops-browser', '/ops/browser')
    config.add_route('angry-cats', '/angry-cats')
    return {'project': 'elmyra.ip.access.epo'}

@view_config(name='angry-cats', renderer='elmyra.ip.access.epo:templates/angry-cats.mako')
def angry_cats(request):
    return {}
