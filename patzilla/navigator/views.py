# -*- coding: utf-8 -*-
# (c) 2013-2026 Andreas Motl, Elmyra UG
import re
import os
import json
import logging
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import FileResponse, RedirectResponse
from mongoengine.errors import NotUniqueError

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
from patzilla.web.dependencies import CurrentUser, LenientBool, Params, State
from patzilla.web.templating import PageRenderer

log = logging.getLogger(__name__)

TEMPLATE_STANDALONE = 'patzilla.navigator:templates/standalone.html'
TEMPLATE_EMBEDDED = 'patzilla.navigator:templates/embedded.html'
TEMPLATE_HELP = 'patzilla.navigator:templates/help.html'
TEMPLATE_LOGIN = 'patzilla.navigator:templates/login.html'
TEMPLATE_MAGIC_LINK_VERIFY = 'patzilla.navigator:templates/magic-link-verify.html'
TEMPLATE_ADMIN_USER_CREATE = 'patzilla.navigator:templates/admin/user-create.html'
TEMPLATE_PORTFOLIO_DEMO = 'patzilla.navigator:templates/portfolio-demo.mako'


def navigator_standalone(request: Request, page: PageRenderer, pdf: str = ''):
    if pdf == 'true':
        return opspdf(request)
    return page.render(TEMPLATE_STANDALONE)


def navigator_embedded(page: PageRenderer):
    return page.render(TEMPLATE_EMBEDDED)


def patentview(request: Request, page: PageRenderer, field: str, value: str):

    params = dict(request.query_params)
    params['mode'] = 'liveview'
    params['context'] = 'viewer'

    payload = {
        'embed_options': json.dumps({
            'matchdict': {'field': field, 'value': value},
            'params': params,
        }),
    }
    return page.render(TEMPLATE_EMBEDDED, payload)


def opspdf(request: Request):
    name = 'ip-navigator-' + (request.query_params.get('query') or 'default')
    filename = slugify(name, strip_equals=False, lowercase=False)
    print_url = str(request.url).replace('pdf=true', 'mode=print')
    if request.headers.get('Host') == 'patentsearch.elmyra.de':
        print_url = print_url.replace('ops/browser', '')
    return Response(render_pdf(print_url), media_type='application/pdf',
                    headers={'Content-Disposition': 'inline; filename={0}.pdf'.format(filename)})


def navigator_vanity(request: Request, label: str):

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


def navigator_quick(request: Request, field: str, value: str, value2: str = None):

    # Exclude access to JavaScript .map files, which would match otherwise.
    if value2 is not None and '.map' in request.url.path:
        raise HTTPException(404)

    # Compute query expression
    expression = compute_expression(field, value, value2, parameters=request.query_params)
    log.info('quick expression: {}'.format(expression))

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

    # FIXME: this is a hack
    path = '/'
    host = request.headers.get('Host', '')

    # TODO: at least look this up in development.ini
    if 'localhost:6543' in host:
        path = ''

    redirect_url = path
    if expression:
        query_args.update({'query': expression})

    if query_args:
        redirect_url += '?' + urlencode(query_args)

    return RedirectResponse(redirect_url, status_code=302)


def admin_user_create(request: Request, page: PageRenderer, params: Params):

    success = False
    success_message = ''
    error = False
    error_messages = []
    fullname = ''
    username = ''

    if request.method == 'POST':
        fullname = params.get('fullname', '').strip()
        username = params.get('username', '').strip().lower()
        password = params.get('password')

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

    tplvars = dict(params)
    tplvars.update({
        'username': username,
        'fullname': fullname,
        'success': asbool(success),
        'success_message': success_message,
        'error': asbool(error),
        'error_message': '<ul><li>' + '</li><li>'.join(error_messages) + '</li></ul>',
    })
    return page.render(TEMPLATE_ADMIN_USER_CREATE, tplvars)


def login_page(page: PageRenderer, state: State, username: str = '', came_from: str = '',
               error: LenientBool = False, reason: str = ''):
    auth_settings = AuthSettings.from_registry(state)
    tplvars = {
        'username': username,
        'came_from': sanitize_redirect_url(came_from, default=''),
        'error': error,
        'reason': reason,
        'magic_link_enabled': auth_settings.magic_link_enabled,
    }
    return page.render(TEMPLATE_LOGIN, tplvars)


def auth_magic_verify(request: Request, page: PageRenderer, state: State, params: Params):
    """
    Two-step magic-link verification endpoint protecting against email link scanners:
    - GET: validates token read-only and renders a confirmation form.
    - POST: atomically consumes the token, provisions/updates the user, creates a
      server-side session, sets the HttpOnly cookie, and redirects.
    """
    auth_settings = AuthSettings.from_registry(state)

    if request.method == 'POST':
        raw_token = params.get('token', '').strip()
        try:
            user, redirect_url = consume_magic_link(raw_token, auth_settings)
            raw_session_token, _ = create_session(
                user=user,
                settings=auth_settings,
                ip_address=get_client_ip(request),
                user_agent=request.headers.get('User-Agent'),
            )
            response = RedirectResponse(redirect_url, status_code=302)
            set_session_cookie(response, raw_session_token, auth_settings, request=request)
            return response
        except MagicLinkError as ex:
            return page.render(TEMPLATE_MAGIC_LINK_VERIFY, {
                'token': '',
                'email': '',
                'valid': False,
                'error': True,
                'error_code': ex.code,
                'error_message': ex.message,
                'magic_link_enabled': auth_settings.magic_link_enabled,
            })

    # GET: read-only inspection (does not consume the token).
    raw_token = params.get('token', '').strip()
    if not auth_settings.magic_link_enabled:
        return page.render(TEMPLATE_MAGIC_LINK_VERIFY, {
            'token': '',
            'email': '',
            'valid': False,
            'error': True,
            'error_code': 'magic-link-disabled',
            'error_message': 'Magic-link authentication is currently disabled.',
            'magic_link_enabled': False,
        })

    try:
        token_doc = inspect_magic_link_token(raw_token)
        return page.render(TEMPLATE_MAGIC_LINK_VERIFY, {
            'token': raw_token,
            'email': token_doc.email,
            'valid': True,
            'error': False,
            'error_code': '',
            'error_message': '',
            'magic_link_enabled': True,
        })
    except MagicLinkError as ex:
        return page.render(TEMPLATE_MAGIC_LINK_VERIFY, {
            'token': '',
            'email': '',
            'valid': False,
            'error': True,
            'error_code': ex.code,
            'error_message': ex.message,
            'magic_link_enabled': True,
        })


def logout_view(request: Request, state: State, user: CurrentUser):
    """
    Revoke active session cookie and redirect to the login page.
    """
    auth_settings = AuthSettings.from_registry(state)
    raw_token = request.cookies.get(auth_settings.session_cookie_name)

    if raw_token:
        revoke_session(raw_token)

    if user is not None and user.is_authenticated:
        UserHistory(userid=user.userid, action='logout').save()

    response = RedirectResponse('/login', status_code=302)
    clear_session_cookie(response, auth_settings, request=request)
    return response


def help(page: PageRenderer):
    return page.render(TEMPLATE_HELP)


def favicon_view():
    icon = os.path.join(os.path.dirname(__file__), 'static', 'favicon.ico')
    if os.path.isfile(icon):
        return FileResponse(icon)
    raise HTTPException(404)


def portfolio(page: PageRenderer):
    return page.render(TEMPLATE_PORTFOLIO_DEMO)


# Routes of the navigator pages, in matching order.
router = APIRouter(prefix='/navigator', include_in_schema=False)
router.add_api_route('/favicon.ico', favicon_view, name='favicon')
router.add_api_route('/admin/user/create', admin_user_create, methods=['GET', 'POST'], name='admin-user-create')
router.add_api_route('/login', login_page, name='login')
router.add_api_route('/auth/magic/verify', auth_magic_verify, methods=['GET', 'POST'], name='auth-magic-verify')
router.add_api_route('/logout', logout_view, name='logout')
router.add_api_route('/help/hotkeys', help, name='help-hotkeys')
router.add_api_route('/help/ificlaims', help, name='help-ificlaims')
router.add_api_route('/', navigator_standalone, name='patentsearch')
router.add_api_route('/embed/item', navigator_embedded, name='embedded-item')
router.add_api_route('/embed/list', navigator_embedded, name='embedded-list')
router.add_api_route('/view/{field}/{value}', patentview, name='patentview')
router.add_api_route('/{label}', navigator_vanity, name='patentsearch-vanity')
router.add_api_route('/{field}/{value}', navigator_quick, name='patentsearch-quick')
router.add_api_route('/{field}/{value}/{value2}', navigator_quick, name='patentsearch-quick2')

root_router = APIRouter(include_in_schema=False)
root_router.add_api_route('/auth/magic/verify', auth_magic_verify, methods=['GET', 'POST'], name='auth-magic-verify-root')
root_router.add_api_route('/logout', logout_view, name='logout-root')
root_router.add_api_route('/portfolio-demo', portfolio, name='portfolio-demo')
