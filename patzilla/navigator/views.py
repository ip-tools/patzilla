# -*- coding: utf-8 -*-
# (c) 2013-2017 Andreas Motl, Elmyra UG
import re
import os
import json
import logging
from pkg_resources import resource_filename
from mongoengine.errors import NotUniqueError
from urllib.parse import urlencode
from patzilla.web.exceptions import HTTPFound, HTTPNotFound
from starlette.responses import FileResponse
from patzilla.util.config import asbool
from patzilla.util.date import today_iso, parse_weekrange, date_iso, week_iso, month_iso, year
from patzilla.util.render.phantomjs import render_pdf
from patzilla.util.text.format import slugify
from patzilla.util.web.identity.config import AuthSettings
from patzilla.util.web.identity.magic_link import (
    MagicLinkError,
    consume_magic_link,
    get_client_ip,
    inspect_magic_link_token,
    sanitize_redirect_url,
)
from patzilla.util.web.identity.session import (
    clear_session_cookie,
    create_session,
    revoke_session,
    set_session_cookie,
)
from patzilla.util.web.identity.store import User, UserHistory
from patzilla.web.routing import RouteTable

log = logging.getLogger(__name__)

TEMPLATE_STANDALONE = 'patzilla.navigator:templates/standalone.html'
TEMPLATE_EMBEDDED = 'patzilla.navigator:templates/embedded.html'
TEMPLATE_HELP = 'patzilla.navigator:templates/help.html'
TEMPLATE_LOGIN = 'patzilla.navigator:templates/login.html'
TEMPLATE_MAGIC_LINK_VERIFY = 'patzilla.navigator:templates/magic-link-verify.html'
TEMPLATE_ADMIN_USER_CREATE = 'patzilla.navigator:templates/admin/user-create.html'
TEMPLATE_PORTFOLIO_DEMO = 'patzilla.navigator:templates/portfolio-demo.mako'


def navigator_routes(prefix=''):
    """
    The routes of the navigator web pages. They are matched in the order defined here.
    """

    routes = RouteTable(prefix=prefix)

    # serve favicon.ico
    routes.add('favicon', '/favicon.ico', favicon_view)

    # serve admin page
    routes.add('admin-user-create', '/admin/user/create', admin_user_create, renderer=TEMPLATE_ADMIN_USER_CREATE)

    # serve login and auth pages
    routes.add('login', '/login', login_page, renderer=TEMPLATE_LOGIN)
    routes.add('auth-magic-verify', '/auth/magic/verify', auth_magic_verify, renderer=TEMPLATE_MAGIC_LINK_VERIFY)
    routes.add('logout', '/logout', logout_view)

    # serve help pages
    routes.add('help-hotkeys', '/help/hotkeys', help, renderer=TEMPLATE_HELP)
    routes.add('help-ificlaims', '/help/ificlaims', help, renderer=TEMPLATE_HELP)

    # serve application
    routes.add('patentsearch', '/', navigator_standalone, renderer=TEMPLATE_STANDALONE)
    routes.add('patentsearch', '/', opspdf, renderer='pdf', request_param='pdf=true')

    # serve web components
    routes.add('embedded-item', '/embed/item', navigator_embedded, renderer=TEMPLATE_EMBEDDED)
    routes.add('embedded-list', '/embed/list', navigator_embedded, renderer=TEMPLATE_EMBEDDED)

    # public
    routes.add('patentview', '/view/{field}/{value}', patentview, renderer=TEMPLATE_EMBEDDED)

    # vanity-/shortcut urls
    routes.add('patentsearch-vanity', '/{label}', navigator_vanity)
    routes.add('patentsearch-quick', '/{field}/{value}', navigator_quick)
    routes.add('patentsearch-quick2', '/{field}/{value}/{value2}', navigator_quick, path_info=r'^(?!.*\.map).*$')

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

    return routes

def navigator_standalone(request):
    return {}

def navigator_embedded(request):
    return {}

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

def opspdf(request):
    name = 'ip-navigator-' + (request.params.get('query') or 'default')
    filename = slugify(name, strip_equals=False, lowercase=False)
    suffix = '.pdf'
    request.response.headers['Content-Disposition'] = 'inline; filename={filename}{suffix}'.format(**locals())
    print_url = request.url.replace('pdf=true', 'mode=print')
    if request.headers.get('Host') == 'patentsearch.elmyra.de':
        print_url = print_url.replace('ops/browser', '')
    return render_pdf(print_url)

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

def navigator_quick(request):
    field = request.matchdict.get('field')
    value = request.matchdict.get('value')
    value2 = request.matchdict.get('value2')

    # Compute query expression
    expression = compute_expression(field, value, value2, parameters=request.params)
    print('quick expression:', expression)

    #return get_redirect_query(request, expression, query_args=query_args)
    return get_redirect_query(request, expression)

def compute_expression(field, value, value2=None, **kwargs):

    # TODO: Refactor to "util" namespace

    if field == 'country':
        field = 'pn'

    if field in ['cl', 'ipc', 'ic', 'cpc', 'cpci', 'cpca']:
        value = value.replace('-', '/')

    quotable = True
    if field in ['pa', 'applicant']:
        if kwargs.get('parameters', {}).get('smart'):
            quotable = False

            # apply blacklist
            blacklist = [
                'GmbH & Co. KG',
                'GmbH',
                ' KG',
                ' AG',
                '& Co.',
            ]
            replacements = {
                ' and ': ' ',
                ' or ':  ' ',
                ' not ': ' ',
            }
            for black in blacklist:
                pattern = re.compile(re.escape(black), re.IGNORECASE)
                value = pattern.sub('', value).strip()
            for replacement_key, replacement_value in replacements.items():
                #value = value.replace(replacement_key, replacement_value)
                pattern = re.compile(replacement_key, re.IGNORECASE)
                value = pattern.sub(replacement_value, value).strip()

            # make query expression
            parts_raw = re.split('[ -]*', value)
            umlaut_map = {
                'ä': 'ae',
                'ö': 'oe',
                'ü': 'ue',
                'Ä': 'Ae',
                'Ö': 'Oe',
                'Ü': 'Ue',
                'ß': 'ss',
            }
            def replace_parts(thing):
                for umlaut, replacement in umlaut_map.items():
                    thing = thing.replace(umlaut, replacement)
                return thing

            parts = []
            for part in parts_raw:

                # "Alfred H. Schütte" => Alfred Schütte
                if re.match(r'^(\w\.)+$', part):
                    continue

                part_normalized = replace_parts(part)
                if part != part_normalized:
                    part = '({} or {})'.format(part, part_normalized)
                parts.append(part)

            value = ' and '.join(parts)
            #value = u'({})'.format(value)


    if quotable and ' ' in value:
        value = '"{0}"'.format(value)

    query = '{field}={value}'.format(**locals())

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

def login_page(request):
    auth_settings = AuthSettings.from_registry(request.registry)
    tplvars = {
        'username': request.params.get('username', ''),
        'came_from': sanitize_redirect_url(request.params.get('came_from', ''), default=''),
        'error': asbool(request.params.get('error')),
        'reason': request.params.get('reason', ''),
        'magic_link_enabled': auth_settings.magic_link_enabled,
    }
    return tplvars


def auth_magic_verify(request):
    """
    Two-step magic-link verification endpoint protecting against email link scanners:
    - GET: validates token read-only and renders a confirmation form.
    - POST: atomically consumes the token, provisions/updates the user, creates a
      server-side session, sets the HttpOnly cookie, and redirects.
    """
    auth_settings = AuthSettings.from_registry(request.registry)

    if request.method == 'POST':
        raw_token = request.POST.get('token', '').strip()
        try:
            user, redirect_url = consume_magic_link(raw_token, auth_settings)
            raw_session_token, _ = create_session(
                user=user,
                settings=auth_settings,
                ip_address=get_client_ip(request),
                user_agent=request.headers.get('User-Agent'),
            )
            response = HTTPFound(location=redirect_url)
            set_session_cookie(response, raw_session_token, auth_settings, request=request)
            return response
        except MagicLinkError as ex:
            return {
                'token': '',
                'email': '',
                'valid': False,
                'error': True,
                'error_code': ex.code,
                'error_message': ex.message,
                'magic_link_enabled': auth_settings.magic_link_enabled,
            }

    # GET: read-only inspection (does not consume the token).
    raw_token = request.params.get('token', '').strip()
    if not auth_settings.magic_link_enabled:
        return {
            'token': '',
            'email': '',
            'valid': False,
            'error': True,
            'error_code': 'magic-link-disabled',
            'error_message': 'Magic-link authentication is currently disabled.',
            'magic_link_enabled': False,
        }

    try:
        token_doc = inspect_magic_link_token(raw_token)
        return {
            'token': raw_token,
            'email': token_doc.email,
            'valid': True,
            'error': False,
            'error_code': '',
            'error_message': '',
            'magic_link_enabled': True,
        }
    except MagicLinkError as ex:
        return {
            'token': '',
            'email': '',
            'valid': False,
            'error': True,
            'error_code': ex.code,
            'error_message': ex.message,
            'magic_link_enabled': True,
        }


def logout_view(request):
    """
    Revoke active session cookie and redirect to the login page.
    """
    auth_settings = AuthSettings.from_registry(request.registry)
    raw_token = request.cookies.get(auth_settings.session_cookie_name)
    user = getattr(request, 'user', None)

    if raw_token:
        revoke_session(raw_token)

    if user is not None and user.is_authenticated:
        UserHistory(userid=user.userid, action='logout').save()

    response = HTTPFound(location='/login')
    clear_session_cookie(response, auth_settings, request=request)
    return response

def help(request):
    return {}

def favicon_view(request):
    icon = resource_filename('patzilla.navigator', 'static/favicon.ico')
    if os.path.isfile(icon):
        return FileResponse(icon)
    else:
        return HTTPNotFound()

def portfolio(request):
    return {}

