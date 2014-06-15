# -*- coding: utf-8 -*-
# (c) 2013,2014 Andreas Motl, Elmyra UG
from elmyra.ip.access.dpma.dpmaregister import DpmaRegisterAccess
from elmyra.ip.util.date import today_iso, parse_weekrange, date_iso, week_iso, month_iso, year
from elmyra.ip.util.render.phantomjs import render_pdf
from elmyra.ip.util.text.format import slugify
from pyramid.encode import urlencode
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.response import Response
from pyramid.settings import asbool
from pyramid.url import route_path
from pyramid.view import view_config

def includeme(config):
    config.add_route('patentsearch', '/ops/browser')
    config.add_route('patentsearch-vanity', '/ops/browser/{label}')
    config.add_route('patentsearch-quick',  '/ops/browser/{field}/{value}')
    config.add_route('patentsearch-quick2',  '/ops/browser/{field}/{value}/{value2}')
    config.add_route('jump-dpmaregister', '/office/dpma/register/application/{document_number}')
    config.add_route('jump-dpmaregister2', '/ops/browser/office/dpma/register/application/{document_number}')
    config.add_route('angry-cats', '/angry-cats')


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
    value2 = None

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

    query = compute_query(field, value, value2)
    return get_redirect_query(request, query)

@view_config(route_name='patentsearch-quick')
@view_config(route_name='patentsearch-quick2')
def opsbrowser_quick(request):
    field = request.matchdict.get('field')
    value = request.matchdict.get('value')
    value2 = request.matchdict.get('value2')

    query = compute_query(field, value, value2)
    return get_redirect_query(request, query)

def compute_query(field, value, value2):

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

def get_redirect_query(request, query):

    # FIXME: does not work due reverse proxy anomalies, tune it to make it work!
    #query = '{field}={value}'.format(**locals())
    #return HTTPFound(location=request.route_url('patentsearch', _query={'query': query}))

    # FIXME: this is a hack
    path = '/'
    if request.headers.get('Host') != 'patentsearch.elmyra.de':
        path = '/ops/browser'
    redirect_url = location=path + '?' + urlencode({'query': query})
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
