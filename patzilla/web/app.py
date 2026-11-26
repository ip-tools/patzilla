# -*- coding: utf-8 -*-
# (c) 2013-2026 Andreas Motl <andreas.motl@ip-tools.org>
import contextlib
import importlib
import logging.config
import typing as t

import anyio.to_thread
from fastapi import FastAPI
from starlette.concurrency import run_in_threadpool
from starlette.staticfiles import StaticFiles
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from patzilla.version import __version__
from patzilla.web.auth import SessionAuthMiddleware
from patzilla.web.errors import install_exception_handlers
from patzilla.web.settings import WebSettings
from patzilla.web.state import build_state, static_directory

logger = logging.getLogger(__name__)

# Routers in matching order. Pages first, then API services.
ROUTERS = [
    "patzilla.navigator.views:router",
    "patzilla.navigator.views:root_router",
    "patzilla.access.office:router",
    "patzilla.access.epo.espacenet.service:router",
    "patzilla.access.sip.service:router",
    "patzilla.navigator.opaquelinks:router",
    "patzilla.navigator.services.admin:router",
    "patzilla.navigator.services.analytics:router",
    "patzilla.navigator.services.composite:router",
    "patzilla.navigator.services.depatech:router",
    "patzilla.navigator.services.dpma:router",
    "patzilla.navigator.services.espacenet:router",
    "patzilla.navigator.services.google:router",
    "patzilla.navigator.services.ificlaims:router",
    "patzilla.navigator.services.ops:router",
    "patzilla.navigator.services.publicationserver:router",
    "patzilla.navigator.services.util:router",
    "patzilla.util.web.identity.service:router",
]


class NoCacheStaticFiles(StaticFiles):
    def file_response(self, *args, **kwargs):
        response = super().file_response(*args, **kwargs)
        response.headers["Cache-Control"] = "max-age=0, must-revalidate, no-cache, no-store"
        return response


class NoSniffMiddleware:
    """Prevent content type sniffing, as Cornice did for all responses."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                if not any(key.lower() == b"x-content-type-options" for key, _ in headers):
                    headers.append((b"x-content-type-options", b"nosniff"))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper if scope["type"] == "http" else send)


def create_app(settings: WebSettings) -> FastAPI:

    @contextlib.asynccontextmanager
    async def lifespan(app: FastAPI) -> t.AsyncIterator[None]:
        if settings.server.threads:
            anyio.to_thread.current_default_thread_limiter().total_tokens = settings.server.threads
        app.state.patzilla = await run_in_threadpool(build_state, settings)
        logger.info("Application is ready to serve requests. Enjoy your research.")
        yield

    # The OpenAPI documentation is opt-in, because some endpoints are only protected by the reverse proxy.
    app = FastAPI(
        title="PatZilla",
        version=__version__,
        lifespan=lifespan,
        root_path=settings.proxy.root_path if settings.proxy else "",
        openapi_url="/api/openapi.json" if settings.api_docs else None,
        docs_url="/api/docs" if settings.api_docs else None,
        redoc_url=None,
    )
    install_exception_handlers(app)

    for index, reference in enumerate(ROUTERS):
        module, _, name = reference.partition(":")
        app.include_router(getattr(importlib.import_module(module), name))
        if index == 0:
            app.mount("/static", NoCacheStaticFiles(directory=static_directory()), name="static")

    app.add_middleware(NoSniffMiddleware)
    app.add_middleware(SessionAuthMiddleware)
    if settings.proxy:
        app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=settings.proxy.trusted_hosts)
    return app


def app_factory() -> FastAPI:
    """
    ASGI application factory, reading the configuration file from `PATZILLA_CONFIG`::

        PATZILLA_CONFIG=patzilla.ini uvicorn --factory patzilla.web.app:app_factory
    """
    settings = WebSettings.from_environment()
    if settings.has_logging:
        logging.config.fileConfig(settings.configfile, disable_existing_loggers=False)
    return create_app(settings)
