# -*- coding: utf-8 -*-
# (c) 2026 Andreas Motl <andreas.motl@ip-tools.org>
"""
ASGI middleware for running behind a reverse proxy.

``ProxyPrefixMiddleware`` is the equivalent of ``egg:PasteDeploy#prefix``,
which has been used before. It evaluates the ``X-Forwarded-*`` headers set by
the reverse proxy, and optionally serves the application below a path prefix.
Only enable it when the application is reachable through the proxy exclusively,
because clients could spoof those headers otherwise.
"""
import typing as t

from starlette.types import ASGIApp, Receive, Scope, Send

from patzilla.web.config import ProxyOptions


class ProxyPrefixMiddleware:

    def __init__(self, app: ASGIApp, options: t.Optional[ProxyOptions] = None):
        self.app = app
        self.options = options or ProxyOptions()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        scope = dict(scope)
        options = self.options
        headers: t.Dict[bytes, bytes] = {}
        others: t.List[t.Tuple[bytes, bytes]] = []
        consumed = {b"x-forwarded-for", b"x-forwarded-scheme", b"x-forwarded-proto"}
        if options.translate_forwarded_server:
            consumed |= {b"x-forwarded-server", b"x-forwarded-host"}
        for key, value in scope["headers"]:
            if key in consumed:
                headers.setdefault(key, value)
            else:
                others.append((key, value))

        host = None
        if options.translate_forwarded_server:
            for name in (b"x-forwarded-server", b"x-forwarded-host"):
                if name in headers:
                    host = headers[name].split(b",")[0].strip()

        if b"x-forwarded-for" in headers:
            client = headers[b"x-forwarded-for"].split(b",")[0].strip().decode("latin-1")
            scope["client"] = (client, 0)

        scheme = headers.get(b"x-forwarded-scheme") or headers.get(b"x-forwarded-proto")
        if scheme:
            scope["scheme"] = scheme.split(b",")[0].strip().decode("latin-1")
        if options.scheme:
            scope["scheme"] = options.scheme

        if options.force_port is not None:
            # An empty value strips the port, like PasteDeploy does.
            current = host or dict(others).get(b"host", b"")
            hostname = current.split(b":")[0]
            host = hostname + b":" + options.force_port.encode("latin-1") if options.force_port else hostname

        if host is not None:
            others = [(key, value) for key, value in others if key != b"host"]
            others.append((b"host", host))
            scope["server"] = (host.split(b":")[0].decode("latin-1"), scope.get("server", (None, None))[1])

        scope["headers"] = others

        prefix = options.prefix
        if prefix:
            path = scope.get("path", "")
            if path == prefix or path.startswith(prefix + "/"):
                scope["root_path"] = scope.get("root_path", "") + prefix

        await self.app(scope, receive, send)


class DefaultHeadersMiddleware:
    """
    Add headers to all HTTP responses, unless they are already present.
    """

    def __init__(self, app: ASGIApp, headers: t.Mapping[str, str]):
        self.app = app
        self.headers = [(key.lower().encode("latin-1"), value.encode("latin-1")) for key, value in headers.items()]

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message: t.MutableMapping[str, t.Any]) -> None:
            if message["type"] == "http.response.start":
                present = {key.lower() for key, _ in message.get("headers", [])}
                message["headers"] = list(message.get("headers", [])) + [
                    (key, value) for key, value in self.headers if key not in present
                ]
            await send(message)

        await self.app(scope, receive, send_wrapper)
