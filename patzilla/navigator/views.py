# -*- coding: utf-8 -*-
# (c) 2013-2017 Andreas Motl, Elmyra UG
import re
import os
import json
import logging
from pkg_resources import resource_filename
from mongoengine.errors import NotUniqueError
from pyramid.encode import urlencode
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.response import FileResponse
from pyramid.settings import asbool
from pyramid.view import view_config
from patzilla.util.date import today_iso, parse_weekrange, date_iso, week_iso, month_iso, year
from patzilla.util.render.phantomjs import render_pdf
from patzilla.util.text.format import slugify
from patzilla.util.web.identity.store import User

log = logging.getLogger(__name__)

def includeme(config):

    # serve favicon.ico
    # http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/assets.html#registering-a-view-callable-to-serve-a-static-asset
    config.add_route('favicon', '/favicon.ico')
    config.add_view('patzilla.navigator.views.favicon_view', route_name='favicon')

    # serve admin page
    config.add_route('admin-user-create', '/admin/user/create')

    # serve login page
    config.add_route('login', '/login')

    # serve help pages
    config.add_route('help', '/help')

    # serve application
    config.add_route('patentsearch', '/')

    # serve web components
    config.add_route('embedded-item', '/embed/item')
    config.add_route('embedded-list', '/embed/list')

    # public
    config.add_route('patentview',          '/view/{field}/{value}')

    # vanity-/shortcut urls
    config.add_route('patentsearch-vanity', '/{label}')
    config.add_route('patentsearch-quick',  '/{field}/{value}')
    config.add_route('patentsearch-quick2', '/{field}/{value}/{value2}', path_info='^(?!.*\.map).*$')

    # Remark:
    # At route "patentsearch-quick2", exclude access to javascript .map files. Otherwise, these would match.
    #
    # Example::
    #
    #   $ curl --silent -i http://localhost:6543/static/jquery/jquery.min.map | grep Location
    #   Location: http://localhost:6543?query=static%3Djquery
    #
    # Negative lookahead to the rescue:
    # http://stackoverflow.com/questions/1240275/how-to-negate-specific-word-in-regex/1240365#1240365

@view_config(route_name='patentsearch', renderer='patzilla.navigator:templates/standalone.html')
def navigator_standalone(request):
    return {}

@view_config(route_name='embedded-item', renderer='patzilla.navigator:templates/embedded.html')
@view_config(route_name='embedded-list', renderer='patzilla.navigator:templates/embedded.html')
def navigator_embedded(request):
    return {}

@view_config(route_name='patentview', renderer='patzilla.navigator:templates/embedded.html')
def patentview(request):

    matchdict = request.matchdict.copy()
    params = request.params.copy()

    params['mode'] = 'liveview'
    params['context'] = 'viewer'

    payload = {
        'embed_options': json.dumps({
            'matchdict': dict(matchdict),
            'params': dict(params),
        }),
    }
    return payload

@view_config(route_name='patentsearch', request_param="pdf=true", renderer='pdf')
def opspdf(request):
    name = 'ip-navigator-' + (request.params.get('query') or 'default')
    filename = slugify(name, strip_equals=False, lowercase=False)
    suffix = '.pdf'
    request.response.headers['Content-Disposition'] = 'inline; filename={filename}{suffix}'.format(**locals())
    print_url = request.url.replace('pdf=true', 'mode=print')
    if request.headers.get('Host') == 'patentsearch.elmyra.de':
        print_url = print_url.replace('ops/browser', '')
    return render_pdf(print_url)

@view_config(route_name='patentsearch-vanity')
def navigator_vanity(request):
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

    query = compute_expression(field, value)
    log.info('vanity url: "{0}" => "{1}"'.format(label, query))

    return get_redirect_query(request, query)

@view_config(route_name='patentsearch-quick')
@view_config(route_name='patentsearch-quick2')
def navigator_quick(request):
    field = request.matchdict.get('field')
    value = request.matchdict.get('value')
    value2 = request.matchdict.get('value2')

    # Compute query expression
    expression = compute_expression(field, value, value2, parameters=request.params)
    print 'quick expression:', expression

    #return get_redirect_query(request, expression, query_args=query_args)
    return get_redirect_query(request, expression)

def compute_expression(field, value, value2=None, **kwargs):

    # TODO: Refactor to "util" namespace

    if field == 'country':
        field = 'pn'

    if field in ['cl', 'ipc', 'ic', 'cpc', 'cpci', 'cpca']:
        value = value.replace(u'-', u'/')

    quotable = True
    if field in ['pa', 'applicant']:
        if kwargs.get('parameters', {}).get('smart'):
            quotable = False

            # apply blacklist
            blacklist = [
                u'GmbH & Co. KG',
                u'GmbH',
                u' KG',
                u' AG',
                u'& Co.',
            ]
            replacements = {
                u' and ': u' ',
                u' or ':  u' ',
                u' not ': u' ',
            }
            for black in blacklist:
                pattern = re.compile(re.escape(black), re.IGNORECASE)
                value = pattern.sub(u'', value).strip()
            for replacement_key, replacement_value in replacements.iteritems():
                #value = value.replace(replacement_key, replacement_value)
                pattern = re.compile(replacement_key, re.IGNORECASE)
                value = pattern.sub(replacement_value, value).strip()

            # make query expression
            parts_raw = re.split(u'[ -]*', value)
            umlaut_map = {
                u'ä': u'ae',
                u'ö': u'oe',
                u'ü': u'ue',
                u'Ä': u'Ae',
                u'Ö': u'Oe',
                u'Ü': u'Ue',
                u'ß': u'ss',
            }
            def replace_parts(thing):
                for umlaut, replacement in umlaut_map.iteritems():
                    thing = thing.replace(umlaut, replacement)
                return thing

            parts = []
            for part in parts_raw:

                # "Alfred H. Schütte" => Alfred Schütte
                if re.match(u'^(\w\.)+$', part):
                    continue

                part_normalized = replace_parts(part)
                if part != part_normalized:
                    part = u'({} or {})'.format(part, part_normalized)
                parts.append(part)

            value = u' and '.join(parts)
            #value = u'({})'.format(value)


    if quotable and u' ' in value:
        value = u'"{0}"'.format(value)

    query = u'{field}={value}'.format(**locals())

    if field in ['pd', 'publicationdate']:
        if 'W' in value:
            range = parse_weekrange(value)
            value = date_iso(range['begin'])
            value2 = date_iso(range['end'])

        if value2:
            query = '{field} within {value},{value2}'.format(**locals())

    return query

def get_redirect_query(request, expression=None, query_args=None):

    query_args = query_args or {}

    # FIXME: does not work due reverse proxy anomalies, tune it to make it work!
    #query = '{field}={value}'.format(**locals())
    #return HTTPFound(location=request.route_url('patentsearch', _query={'query': query}))

    # FIXME: this is a hack
    path = '/'
    host = request.headers.get('Host')

    # TODO: at least look this up in development.ini
    if 'localhost:6543' in host:
        path = ''

    redirect_url = path
    if expression:
        query_args.update({'query': expression})

    if query_args:
        redirect_url += '?' + urlencode(query_args)

    return HTTPFound(redirect_url)


@view_config(route_name='admin-user-create', renderer='patzilla.navigator:templates/admin/user-create.html')
def admin_user_create(request):

    success = False
    success_message = ''
    error = False
    error_messages = []

    if request.method == 'POST':
        fullname = request.params.get('fullname').strip()
        username = request.params.get('username').strip().lower()
        password = request.params.get('password')

        if not fullname:
            error = True
            error_messages.append('Full name must not be empty.')

        if not username:
            error = True
            error_messages.append('Email address / Username must not be empty.')

        if not password:
            error = True
            error_messages.append('Password must not be empty.')

        if not error:
            user = User(username = username, password = password, fullname = fullname, tags = ['trial'])
            try:
                user.save()
                success = True
                success_message = 'User "%s" created.' % username

                fullname = ''
                username = ''

            except NotUniqueError as ex:
                error = True
                error_messages.append('User already exists: %s' % ex)

    tplvars = {
        'username': '',
        'fullname': '',
        'success': success,
        'success_message': success_message,
        'error': error,
        'error_message': '<ul><li>' + '</li><li>'.join(error_messages) + '</li></ul>',
    }

    tplvars.update(dict(request.params))
    tplvars.update(**locals())

    tplvars['success'] = asbool(tplvars['success'])
    tplvars['error'] = asbool(tplvars['error'])
    return tplvars

@view_config(route_name='login', renderer='patzilla.navigator:templates/login.html')
def login_page(request):
    tplvars = {
        'username': request.params.get('username', ''),
        'came_from': request.params.get('came_from', ''),
        'error': asbool(request.params.get('error')),
        'reason': request.params.get('reason', ''),
    }
    return tplvars

@view_config(route_name='help', renderer='patzilla.navigator:templates/help.html')
def help(request):
    return {}

def favicon_view(request):
    # http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/assets.html#registering-a-view-callable-to-serve-a-static-asset
    icon = resource_filename('patzilla.navigator', 'static/favicon.ico')
    if os.path.isfile(icon):
        return FileResponse(icon, request=request)
    else:
        return HTTPNotFound()

@view_config(name='portfolio-demo', renderer='patzilla.navigator:templates/portfolio-demo.mako')
def portfolio(request):
    return {}

