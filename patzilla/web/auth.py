# -*- coding: utf-8 -*-
# (c) 2026 Andreas Motl <andreas.motl@ip-tools.org>
import logging

from starlette.concurrency import run_in_threadpool
from starlette.datastructures import Headers
from starlette.requests import HTTPConnection
from starlette.responses import Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from patzilla.util.web.identity.config import AuthSettings
from patzilla.util.web.identity.session import authenticate_session, clear_session_cookie, set_session_cookie
from patzilla.util.web.identity.store import User

log = logging.getLogger(__name__)


class SessionAuthMiddleware:
    """
    Resolve the requesting user into `scope["user"]` (`request.user`), in this order:

    1. HttpOnly session cookie, validated against `UserSession`, with sliding renewal.
    2. Reverse-proxy `X-User-Id` header, e.g. from `nginx-auth`.
    3. Anonymous `User()`.

    Renewed session cookies are sent with the response, invalid ones are cleared.
    """

    def __init__(self, app: ASGIApp, skip_prefixes=("/static/",)):
        self.app = app
        self.skip_prefixes = skip_prefixes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["path"].startswith(self.skip_prefixes):
            await self.app(scope, receive, send)
            return

        conn = HTTPConnection(scope)
        settings = AuthSettings.from_registry(scope["app"].state.patzilla)
        user, cookie_headers = await run_in_threadpool(resolve_user, conn, settings)
        scope["user"] = user

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start" and cookie_headers:
                message["headers"] = list(message.get("headers", [])) + cookie_headers
            await send(message)

        await self.app(scope, receive, send_wrapper)


def resolve_user(conn: HTTPConnection, settings: AuthSettings):
    """Return `(user, set_cookie_headers)`."""
    raw_token = conn.cookies.get(settings.session_cookie_name)
    if raw_token:
        try:
            user, session, renewed = authenticate_session(raw_token, settings)
        except Exception:
            log.exception("Failed to authenticate session cookie")
            user, session, renewed = None, None, False

        cookies = Response()
        if user is not None and session is not None:
            if renewed:
                set_session_cookie(cookies, raw_token, settings, request=conn)
            return user, _set_cookie_headers(cookies.headers)
        clear_session_cookie(cookies, settings, request=conn)
        cookie_headers = _set_cookie_headers(cookies.headers)
    else:
        cookie_headers = []

    userid = conn.headers.get("X-User-Id")
    user = (User.objects(userid=userid).first() if userid else None) or User()  # ty: ignore[unresolved-attribute]
    return user, cookie_headers


def _set_cookie_headers(headers: Headers):
    return [(key, value) for key, value in headers.raw if key == b"set-cookie"]
