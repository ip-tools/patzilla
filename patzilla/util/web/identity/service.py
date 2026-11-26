# -*- coding: utf-8 -*-
# (c) 2014-2026 Andreas Motl, Elmyra UG
import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Body, Depends, Request, Response

from patzilla.access.generic.exceptions import ServiceError
from patzilla.util.web.identity.config import AuthSettings
from patzilla.util.web.identity.magic_link import (
    InvalidEmailError,
    MagicLinkDisabledError,
    MagicLinkError,
    MagicLinkMail,
    RateLimitExceededError,
    get_client_ip,
    request_magic_link,
    resolve_base_url,
)
from patzilla.util.web.identity.session import clear_session_cookie, revoke_session
from patzilla.util.web.identity.store import User, UserHistory
from patzilla.web.dependencies import CurrentUser, State, Vendor

log = logging.getLogger(__name__)

router = APIRouter(tags=["identity"])


def get_auth_settings(state: State) -> AuthSettings:
    return AuthSettings.from_registry(state)


Auth = Annotated[AuthSettings, Depends(get_auth_settings)]


async def get_payload(request: Request) -> dict:
    """Read request parameters from JSON body or form data."""
    content_type = (request.headers.get("content-type") or "").lower()
    if "application/json" in content_type:
        try:
            body = await request.json()
        except ValueError:
            return {}
        return body if isinstance(body, dict) else {}
    if content_type.startswith(("application/x-www-form-urlencoded", "multipart/form-data")):
        return dict(await request.form())
    return dict(request.query_params)


@router.post("/api/identity/auth", name="identity-auth", summary="Identity service: perform authentication")
def identity_auth_handler(payload: Annotated[Optional[dict], Body()] = None):
    """Authenticate a user with username and password."""

    try:
        username = payload['username'].lower()
        password = payload['password']
        assert len(username) > 0
        assert len(password) > 0
    except (KeyError, AttributeError, AssertionError, TypeError, ValueError):
        raise ServiceError('identity subsystem', 'authentication-failed', 'Incomplete credentials')

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

    raise ServiceError('identity subsystem', 'authentication-failed', 'Authentication failed')


@router.get("/api/identity/pwhash/{password}", name="identity-pwhash", summary="Identity service: hash password")
def identity_pwhash_handler(password: str):
    """Hash a password."""
    return User.crypt500(password)


@router.post("/api/identity/magic-link", name="identity-magic-link",
             summary="Identity service: request an email magic-link for passwordless authentication")
def identity_magic_link_handler(request: Request, state: State, vendor: Vendor, auth_settings: Auth,
                                payload: Annotated[dict, Depends(get_payload)]):
    """
    Request a passwordless email magic link.
    Returns a neutral success message to avoid leaking account existence.
    """
    try:
        request_magic_link(
            email=payload.get("email"),
            settings=auth_settings,
            base_url=resolve_base_url(request, auth_settings),
            came_from=payload.get("came_from"),
            request_ip=get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            mail=MagicLinkMail.from_settings(state.application_settings, vendor),
        )
    except InvalidEmailError as ex:
        raise ServiceError("identity subsystem", ex.code, ex.message, status_code=400)
    except MagicLinkDisabledError as ex:
        raise ServiceError("identity subsystem", ex.code, ex.message, status_code=403)
    except RateLimitExceededError as ex:
        raise ServiceError("identity subsystem", ex.code, ex.message, status_code=429)
    except MagicLinkError as ex:
        raise ServiceError("identity subsystem", ex.code, ex.message, status_code=503)

    return {
        "status": "ok",
        "message": "If the email address is valid, a sign-in link has been sent.",
    }


@router.get("/api/identity/session", name="identity-session",
            summary="Identity service: inspect current authentication session")
def identity_session_handler(user: CurrentUser):
    """
    Return the current user's authentication status and non-sensitive profile data.
    Also used by `nginx-auth` to validate session cookies.
    """
    if user is not None and user.is_authenticated and user.is_active:
        return {
            "authenticated": True,
            "user": user.to_public_dict(),
        }
    return {
        "authenticated": False,
        "user": None,
    }


@router.post("/api/identity/logout", name="identity-logout",
             summary="Identity service: revoke current authentication session")
def identity_logout_handler(request: Request, response: Response, user: CurrentUser, auth_settings: Auth):
    """
    Revoke the current server-side session and clear the session cookie.
    """
    raw_token = request.cookies.get(auth_settings.session_cookie_name)

    if raw_token:
        revoke_session(raw_token)

    if user is not None and user.is_authenticated:
        UserHistory(userid=user.userid, action="logout").save()

    clear_session_cookie(response, auth_settings, request=request)
    return {"status": "ok"}
