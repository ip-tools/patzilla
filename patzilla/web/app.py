# -*- coding: utf-8 -*-
# (c) 2013-2026 Andreas Motl <andreas.motl@ip-tools.org>
"""
Application factory.

- ``configure()`` builds the application registry from the configuration file.
- ``create_app()`` builds the FastAPI application from the registry.
- ``app_factory()`` is the entry point for ASGI servers, reading the
  configuration file from the ``PATZILLA_CONFIG`` environment variable.
- ``bootstrap()`` provides an application environment without an HTTP server,
  for command line programs and software tests.
"""
import contextlib
import datetime
import logging
import logging.config
import os
import typing as t
from email.utils import format_datetime

import anyio.to_thread
from fastapi import FastAPI
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response as StarletteResponse
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles
from starlette.types import Scope

from patzilla.boot.cache import configure_cache_regions
from patzilla.navigator.settings import GlobalSettings
from patzilla.util.config import asbool
from patzilla.version import __version__
from patzilla.web.config import IniConfiguration, read_ini
from patzilla.web.context import set_defaults
from patzilla.web.exceptions import HTTPError, HTTPException, HTTPMethodNotAllowed, HTTPNotFound
from patzilla.web.middleware import DefaultHeadersMiddleware, ProxyPrefixMiddleware
from patzilla.web.registry import Registry, StaticView
from patzilla.web.render import TemplateRenderer
from patzilla.web.request import Request
from patzilla.web.response import status_reason
from patzilla.web.routing import ALL_METHODS, RouteTable
from patzilla.web.service import Service

logger = logging.getLogger(__name__)


# Modules defining API services. They are mounted in this order,
# their services ordered by attribute name, like Pyramid's scanner did.
SERVICE_MODULES = [
    "patzilla.access.epo.espacenet.service",
    "patzilla.access.sip.service",
    "patzilla.navigator.opaquelinks",
    "patzilla.navigator.services.admin",
    "patzilla.navigator.services.analytics",
    "patzilla.navigator.services.composite",
    "patzilla.navigator.services.depatech",
    "patzilla.navigator.services.dpma",
    "patzilla.navigator.services.espacenet",
    "patzilla.navigator.services.google",
    "patzilla.navigator.services.ificlaims",
    "patzilla.navigator.services.ops",
    "patzilla.navigator.services.publicationserver",
    "patzilla.navigator.services.util",
    "patzilla.util.web.identity.service",
]


def configure(configfile: str, settings: t.Optional[t.Dict[str, t.Any]] = None, flavor: str = "web") -> Registry:
    """
    Build the application registry.

    The ``minimal`` flavor is a lightweight runtime environment for command line
    programs and software tests. The ``web`` flavor is the full web application.
    """
    settings = dict(settings or {})
    registry = Registry(settings=settings)
    registry.app_flavor = flavor

    # Propagate global settings to application registry.
    global_settings = GlobalSettings(configfile)
    registry.global_settings = global_settings
    registry.application_settings = global_settings.application_settings
    registry.datasource_settings = global_settings.datasource_settings
    registry.vendor_settings = global_settings.vendor_settings

    if flavor == "minimal":
        registry.include("patzilla.navigator.opaquelinks")
        # TODO: Refactor user context bootstrapping to `patzilla.boot.user`, maybe.
        registry.include("patzilla.util.web.identity.service")
        registry.include("patzilla.boot.settings")
        registry.include("patzilla.access")

    elif flavor == "web":
        reload_templates = settings.get("reload_templates", settings.get("pyramid.reload_templates"))
        registry.template_renderer = TemplateRenderer(reload=asbool(reload_templates))
        configure_cache_regions(settings)

        registry.include("patzilla.util.database.beaker_mongodb_gridfs")
        registry.include("patzilla.util.web.identity")
        registry.include("patzilla.navigator")
        registry.include("patzilla.boot.settings")
        registry.include("patzilla.access")

        for module in SERVICE_MODULES:
            registry.add_services_from(module)

    else:
        raise ValueError(f"Unknown application flavor: {flavor}")

    return registry


class CachingStaticFiles(StaticFiles):
    """
    Serve static files, optionally emitting caching headers.
    """

    def __init__(self, *args: t.Any, cache_max_age: t.Optional[int] = None, **kwargs: t.Any):
        super().__init__(*args, **kwargs)
        self.cache_max_age = cache_max_age

    def file_response(self, full_path, stat_result, scope: Scope, status_code: int = 200):  # type: ignore[override]
        response = super().file_response(full_path, stat_result, scope, status_code=status_code)
        if self.cache_max_age is not None:
            expires = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=self.cache_max_age)
            response.headers["Expires"] = format_datetime(expires, usegmt=True)
            if self.cache_max_age == 0:
                # Like Pyramid/WebOb, forcefully prevent caching.
                response.headers["Cache-Control"] = "max-age=0, must-revalidate, no-cache, no-store"
                response.headers["Pragma"] = "no-cache"
            else:
                response.headers["Cache-Control"] = f"max-age={self.cache_max_age}"
        return response


def create_app(
    registry: Registry,
    proxy: t.Any = None,
    threads: t.Optional[int] = None,
) -> FastAPI:
    """
    Build the FastAPI application.

    The OpenAPI schema and interactive documentation are only published when
    enabled using the ``api.docs = true`` setting, because some endpoints are
    only protected by the reverse proxy.
    """

    @contextlib.asynccontextmanager
    async def lifespan(app: FastAPI) -> t.AsyncIterator[None]:
        if threads:
            anyio.to_thread.current_default_thread_limiter().total_tokens = threads
        await run_in_threadpool(registry.notify_startup, app)
        logger.info("Application is ready to serve requests. Enjoy your research.")
        yield

    docs_enabled = asbool(registry.settings.get("api.docs", False))
    app = FastAPI(
        title="PatZilla",
        version=__version__,
        lifespan=lifespan,
        redirect_slashes=False,
        openapi_url="/api/openapi.json" if docs_enabled else None,
        docs_url="/api/docs" if docs_enabled else None,
        redoc_url=None,
    )
    app.state.registry = registry

    for entry in registry.routing:
        if isinstance(entry, RouteTable):
            app.router.routes.extend(entry.api_routes())
        elif isinstance(entry, StaticView):
            app.router.routes.append(Mount(
                entry.url_path,
                app=CachingStaticFiles(directory=entry.directory, cache_max_age=entry.cache_max_age),
                name=entry.url_path.strip("/"),
            ))
        elif isinstance(entry, Service):
            route = entry.api_route()
            if route is not None:
                app.router.routes.append(route)

    app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]

    # Prevent content type sniffing, a protection Cornice applied to all responses.
    app.add_middleware(DefaultHeadersMiddleware, headers={"X-Content-Type-Options": "nosniff"})

    if proxy is not None:
        app.add_middleware(ProxyPrefixMiddleware, options=proxy)

    return app


async def http_exception_handler(request: StarletteRequest, exc: StarletteHTTPException) -> StarletteResponse:
    """
    Render errors raised by the routing layer, e.g. "404 Not Found" or "405 Method Not Allowed",
    like all other HTTP errors, see ``patzilla.web.exceptions``.
    """
    error: HTTPException
    if exc.status_code == 404:
        path, root_path = request.url.path, request.scope.get("root_path", "")
        if root_path and path.startswith(root_path):
            path = path[len(root_path):]
        error = HTTPNotFound(path)
    elif exc.status_code == 405:
        error = HTTPMethodNotAllowed(request_method=request.method)
    else:
        error = HTTPError(detail=exc.detail)
        error.status = exc.status_code
        error.title = status_reason(exc.status_code)
    for key, value in (exc.headers or {}).items():
        if key.lower() == "allow":
            value = ", ".join(sorted(
                (method.strip() for method in value.split(",")),
                key=lambda method: ALL_METHODS.index(method) if method in ALL_METHODS else len(ALL_METHODS),
            ))
        error.headers[key] = value
    return error.to_starlette(accept=request.headers.get("Accept"), base_url=str(request.url))


def configure_logging(configfile: str) -> None:
    logging.config.fileConfig(configfile, disable_existing_loggers=False)


def app_from_config(configfile: str, ini: t.Optional[IniConfiguration] = None) -> FastAPI:
    ini = ini or read_ini(configfile)
    registry = configure(ini.path, settings=ini.settings, flavor=ini.flavor)
    return create_app(registry, proxy=ini.proxy, threads=ini.server.threads)


def app_factory() -> FastAPI:
    """
    ASGI application factory, reading the configuration file from ``PATZILLA_CONFIG``.

    Example::

        PATZILLA_CONFIG=patzilla.ini uvicorn --factory patzilla.web.app:app_factory
    """
    configfile = os.environ.get("PATZILLA_CONFIG")
    if not configfile:
        raise ValueError("Configuration file missing, please set the PATZILLA_CONFIG environment variable")
    ini = read_ini(configfile)
    if ini.has_logging:
        configure_logging(ini.path)
    return app_from_config(ini.path, ini=ini)


def bootstrap(configfile: str) -> t.Dict[str, t.Any]:
    """
    Provide the application environment without running an HTTP server.

    The request object returned is designated as the default request, so that
    code accessing the current request works within command line programs.
    This is the counterpart to ``pyramid.paster.bootstrap``.
    """
    ini = read_ini(configfile)
    registry = configure(ini.path, settings=ini.settings, flavor=ini.flavor)
    app = create_app(registry, proxy=ini.proxy, threads=ini.server.threads)
    registry.notify_startup(app)
    request = Request(registry=registry, host="localhost:80")
    set_defaults(request=request, registry=registry)
    return {"app": app, "registry": registry, "request": request, "closer": lambda: set_defaults(None, None)}
