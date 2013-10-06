from pyramid.response import Response
from pyramid.view import view_config

@view_config(route_name='ops-chooser', renderer='elmyra.ip.access.epo:templates/ops-chooser.mako')
def screening(request):
    return {'project': 'elmyra.ip.access.epo'}
