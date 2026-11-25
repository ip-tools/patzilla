# -*- coding: utf-8 -*-
# (c) 2014-2026 Andreas Motl, Elmyra UG
import logging
from patzilla.web.service import Service
from patzilla.util.web.identity.config import AuthSettings
from patzilla.util.web.identity.magic_link import (
    InvalidEmailError,
    MagicLinkDisabledError,
    MagicLinkError,
    RateLimitExceededError,
    get_client_ip,
    request_magic_link,
    resolve_base_url,
)
from patzilla.util.web.identity.session import (
    authenticate_session,
    clear_session_cookie,
    revoke_session,
    set_session_cookie,
)
from patzilla.util.web.identity.store import User, UserHistory

log = logging.getLogger(__name__)


def setup(registry):
    registry.add_request_subscriber(attach_user)


# ------------------------------------------
#   user injection
# ------------------------------------------
def attach_user(event):
    """
    Attach `request.user` and `request.auth_session` to incoming requests.

    Resolution order:
    1. Native HttpOnly session cookie (`patzilla_session`), validated
       against MongoDB `UserSession` with automatic sliding renewal.
    2. Reverse-proxy `X-User-Id` header (e.g. from `nginx-auth`).
    3. Anonymous placeholder `User()`.
    """
    request = event.request
    request.auth_session = None

    auth_settings = AuthSettings.from_registry(request.registry)
    raw_session_token = request.cookies.get(auth_settings.session_cookie_name)

    if raw_session_token:
        try:
            user, session, renewed = authenticate_session(raw_session_token, auth_settings)
        except Exception:
            log.exception("Failed to authenticate session cookie")
            user, session, renewed = None, None, False

        if user is not None and session is not None:
            request.user = user
            request.auth_session = session
            if renewed:
                def _renew_cookie(req, response):
                    set_session_cookie(response, raw_session_token, auth_settings, request=req)

                request.add_response_callback(_renew_cookie)
            return

        # Clear invalid / expired / revoked session cookie.
        def _clear_cookie(req, response):
            clear_session_cookie(response, auth_settings, request=req)

        request.add_response_callback(_clear_cookie)

    userid = request.headers.get('X-User-Id')
    if userid:
        request.user = User.objects(userid=userid).first() or User()  # ty: ignore[unresolved-attribute]
    else:
        request.user = User()


# ------------------------------------------
#   services
# ------------------------------------------
identity_auth = Service(
    name='identity-auth',
    path='/api/identity/auth',
    description='Identity service: perform authentication')

identity_pwhash = Service(
    name='identity-pwhash',
    path='/api/identity/pwhash/{password}',
    description='Identity service: hash password')

identity_magic_link = Service(
    name='identity-magic-link',
    path='/api/identity/magic-link',
    description='Identity service: request an email magic-link for passwordless authentication')

identity_session = Service(
    name='identity-session',
    path='/api/identity/session',
    description='Identity service: inspect current authentication session')

identity_logout = Service(
    name='identity-logout',
    path='/api/identity/logout',
    description='Identity service: revoke current authentication session')

# TODO: set user password
"""
identity_user_password = Service(
    name='identity-user-password',
    path='/api/identity/user/{username}/{password}',
    description='Identity service: set user password')
"""


# ------------------------------------------
#   handlers
# ------------------------------------------
@identity_auth.decorator("post", accept="application/json")
def identity_auth_handler(request):
    """Authenticate a user with username and password."""

    try:
        payload = request.json
        username = payload['username'].lower()
        password = payload['password']
        assert len(username) > 0
        assert len(password) > 0
    except (KeyError, AttributeError, AssertionError, ValueError):
        request.errors.add('identity subsystem', 'authentication-failed', 'Incomplete credentials')
        return

    # mitigate timing attacks
    # see also:
    # http://codahale.com/a-lesson-in-timing-attacks/
    # http://emerose.com/timing-attacks-explained
    # http://carlos.bueno.org/2011/10/timing.html
    # https://code.djangoproject.com/ticket/20760
    User.crypt500(password)

    # find user
    user = User.objects(username__iexact=username).first()  # ty: ignore[unresolved-attribute]
    if user is not None:

        # check password
        if user.check_password(password):
            UserHistory(userid=user.userid, action='login').save()
            response = {
                'userid': user.userid,
                'username': user.username,
                'fullname': user.fullname,
                'tags': user.tags,
                'modules': user.modules,
            }
            return response

    request.errors.add('identity subsystem', 'authentication-failed', 'Authentication failed')


@identity_pwhash.decorator("get", accept="application/json")
def identity_pwhash_handler(request):
    """Hash a password."""

    password = request.matchdict.get('password')
    return User.crypt500(password)


def _extract_request_payload(request) -> dict:
    """Read request parameters from JSON body or form data."""
    content_type = (request.content_type or "").lower()
    if "application/json" in content_type:
        try:
            body = getattr(request, "json_body", None)
            if body is None:
                body = request.json
            if isinstance(body, dict):
                return body
        except (ValueError, AttributeError):
            return {}
    return dict(request.params)


@identity_magic_link.decorator("post")
def identity_magic_link_handler(request):
    """
    Request a passwordless email magic link.
    Returns a neutral success message to avoid leaking account existence.
    """
    auth_settings = AuthSettings.from_registry(request.registry)
    payload = _extract_request_payload(request)
    email = payload.get("email")
    came_from = payload.get("came_from")

    try:
        request_magic_link(
            email=email,
            settings=auth_settings,
            base_url=resolve_base_url(request, auth_settings),
            came_from=came_from,
            request_ip=get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            request=request,
        )
    except InvalidEmailError as ex:
        request.errors.status = 400
        request.errors.add("identity subsystem", ex.code, ex.message)
        return
    except MagicLinkDisabledError as ex:
        request.errors.status = 403
        request.errors.add("identity subsystem", ex.code, ex.message)
        return
    except RateLimitExceededError as ex:
        request.errors.status = 429
        request.errors.add("identity subsystem", ex.code, ex.message)
        return
    except MagicLinkError as ex:
        request.errors.status = 503
        request.errors.add("identity subsystem", ex.code, ex.message)
        return

    return {
        "status": "ok",
        "message": "If the email address is valid, a sign-in link has been sent.",
    }


@identity_session.decorator("get")
def identity_session_handler(request):
    """
    Return the current user's authentication status and non-sensitive profile data.
    Also used by `nginx-auth` to validate native session cookies.
    """
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated and user.is_active:
        return {
            "authenticated": True,
            "user": user.to_public_dict(),
        }
    return {
        "authenticated": False,
        "user": None,
    }


@identity_logout.decorator("post")
def identity_logout_handler(request):
    """
    Revoke the current server-side session and clear the session cookie.
    """
    auth_settings = AuthSettings.from_registry(request.registry)
    raw_token = request.cookies.get(auth_settings.session_cookie_name)
    user = getattr(request, "user", None)

    if raw_token:
        revoke_session(raw_token)

    if user is not None and user.is_authenticated:
        UserHistory(userid=user.userid, action="logout").save()

    clear_session_cookie(request.response, auth_settings, request=request)
    return {"status": "ok"}
