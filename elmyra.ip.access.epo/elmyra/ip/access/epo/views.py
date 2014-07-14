# -*- coding: utf-8 -*-
# (c) 2013,2014 Andreas Motl, Elmyra UG
import os
import logging
from pkg_resources import resource_filename
from elmyra.ip.access.dpma.dpmaregister import DpmaRegisterAccess
from elmyra.ip.util.date import today_iso, parse_weekrange, date_iso, week_iso, month_iso, year
from elmyra.ip.util.render.phantomjs import render_pdf
from elmyra.ip.util.text.format import slugify
from pyramid.encode import urlencode
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.response import Response, FileResponse
from pyramid.settings import asbool
from pyramid.url import route_path
from pyramid.view import view_config

log = logging.getLogger(__name__)

def includeme(config):

    # serve favicon.ico
    # http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/assets.html#registering-a-view-callable-to-serve-a-static-asset
    config.add_route('favicon', '/ops/browser/favicon.ico')
    config.add_view('elmyra.ip.access.epo.views.favicon_view', route_name='favicon')

    # serve login page
    config.add_route('login', '/ops/browser/login')

    # serve help page
    config.add_route('help', '/ops/browser/help')

    # serve application
    config.add_route('patentsearch', '/ops/browser')

    # vanity-/shortcut urls
    config.add_route('patentsearch-vanity', '/ops/browser/{label}')
    config.add_route('patentsearch-quick',  '/ops/browser/{field}/{value}')
    config.add_route('patentsearch-quick2',  '/ops/browser/{field}/{value}/{value2}', path_info='^(?!.*\.map).*$')
    config.add_route('jump-dpmaregister', '/office/dpma/register/application/{document_number}')
    config.add_route('jump-dpmaregister2', '/ops/browser/office/dpma/register/application/{document_number}')

    # demo stuff
    #config.add_route('angry-cats', '/angry-cats')

    # at route "patentsearch-quick2", exclude access to javascript .map files, these would match, see::
    #   $ curl --silent -i http://localhost:6543/ops/browser/fanstatic/jquery/jquery.min.map | grep Location
    #   Location: http://localhost:6543/ops/browser?query=fanstatic%3Djquery
    #
    # negative lookahead to the rescue:
    # http://stackoverflow.com/questions/1240275/how-to-negate-specific-word-in-regex/1240365#1240365

@view_config(route_name='patentsearch', renderer='elmyra.ip.access.epo:templates/app.html')
def opsbrowser(request):
    payload = {
        'project': 'elmyra.ip.access.epo',
    }
    return payload


@view_config(route_name='patentsearch', request_param="pdf=true", renderer='pdf')
def opspdf(request):
    name = 'elmyra-patentsearch-' + request.params.get('query')
    filename = slugify(name, strip_equals=False, lowercase=False)
    suffix = '.pdf'
    request.response.headers['Content-Disposition'] = 'inline; filename={filename}{suffix}'.format(**locals())
    print_url = request.url.replace('pdf=true', 'mode=print')
    if request.headers.get('Host') == 'patentsearch.elmyra.de':
        print_url = print_url.replace('ops/browser', '')
    return render_pdf(print_url)

@view_config(route_name='patentsearch-vanity')
def opsbrowser_vanity(request):
    label = request.matchdict.get('label')

    field = None
    value = None

    if label == 'today':
        field = 'publicationdate'
        value = today_iso()

    elif label == 'week':
        field = 'publicationdate'
        value = week_iso()

    elif label == 'month':
        field = 'publicationdate'
        value = month_iso()

    elif label == 'year':
        field = 'publicationdate'
        value = year()

    else:
        return get_redirect_query(request)

    query = compute_query(field, value)
    log.info('vanity url: "{0}" => "{1}"'.format(label, query))

    return get_redirect_query(request, query)

@view_config(route_name='patentsearch-quick')
@view_config(route_name='patentsearch-quick2')
def opsbrowser_quick(request):
    field = request.matchdict.get('field')
    value = request.matchdict.get('value')
    value2 = request.matchdict.get('value2')

    query = compute_query(field, value, value2)
    print 'quick:', query
    return get_redirect_query(request, query)

def compute_query(field, value, value2=None):

    if field == 'country':
        field = 'pn'

    if field in ['cl', 'ipc', 'ic', 'cpc', 'cpci', 'cpca']:
        value = value.replace('-', '/')

    query = '{field}={value}'.format(**locals())

    if field in ['pd', 'publicationdate']:
        if 'W' in value:
            range = parse_weekrange(value)
            value = date_iso(range['begin'])
            value2 = date_iso(range['end'])

        if value2:
            query = '{field} within {value},{value2}'.format(**locals())

    return query

def get_redirect_query(request, query=None):

    # FIXME: does not work due reverse proxy anomalies, tune it to make it work!
    #query = '{field}={value}'.format(**locals())
    #return HTTPFound(location=request.route_url('patentsearch', _query={'query': query}))

    # FIXME: this is a hack
    path = '/'
    host = request.headers.get('Host')

    # TODO: at least look this up in development.ini
    if 'localhost:6543' in host:
        path = '/ops/browser'

    redirect_url = path
    if query:
        redirect_url += '?' + urlencode({'query': query})

    return HTTPFound(redirect_url)


@view_config(route_name='jump-dpmaregister')
@view_config(route_name='jump-dpmaregister2')
def jump_dpmaregister(request):
    document_number = request.matchdict.get('document_number')
    redirect = request.params.get('redirect')
    if document_number:
        dra = DpmaRegisterAccess()
        url = dra.get_document_url(document_number)
        if url and redirect:
            return HTTPFound(location=url)

    return HTTPNotFound('Could not find application number "{0}" in DPMAregister'.format(document_number))


@view_config(route_name='login', renderer='elmyra.ip.access.epo:templates/login.html')
def login_page(request):
    tplvars = {
        'username': request.params.get('username', ''),
        'error': asbool(request.params.get('error')),
    }
    return tplvars

@view_config(route_name='help', renderer='elmyra.ip.access.epo:templates/help.html')
def help_page(request):
    return {}

def favicon_view(request):
    # http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/assets.html#registering-a-view-callable-to-serve-a-static-asset
    icon = resource_filename('elmyra.ip.access.epo', 'static/favicon.ico')
    if os.path.isfile(icon):
        return FileResponse(icon, request=request)
    else:
        return HTTPNotFound()

@view_config(name='patentsearch-old', renderer='elmyra.ip.access.epo:templates/app.html')
def ops_chooser(request):
    url = route_path('patentsearch', request, _query=request.params)
    return HTTPFound(location=url)

@view_config(name='portfolio-demo', renderer='elmyra.ip.access.epo:templates/portfolio-demo.mako')
def portfolio(request):
    return {'project': 'elmyra.ip.access.epo'}

@view_config(name='angry-cats', renderer='elmyra.ip.access.epo:templates/angry-cats.mako')
def angry_cats(request):
    return {}
