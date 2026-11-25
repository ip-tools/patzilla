# -*- coding: utf-8 -*-
# (c) 2026 Andreas Motl <andreas.motl@ip-tools.org>
"""
Bridge between FastAPI routes and PatZilla's synchronous request handlers.

- ``build_endpoint`` creates an ASGI endpoint which reads the request body,
  builds a ``patzilla.web.request.Request``, and runs the handler in Starlette's
  worker thread pool, with the request designated as current request.
- ``RouteTable`` declares web pages: route name, path pattern, handler,
  renderer, and predicates. It replaces Pyramid's URL dispatch (``add_route``,
  ``view_config``) and retains the order of route matching.
- ``convert_path`` translates Pyramid route patterns, including regular
  expressions like ``{name:\\/?}``, into Starlette path syntax.
"""
import hashlib
import logging
import re
import typing as t

from fastapi.routing import APIRoute
from starlette.concurrency import run_in_threadpool
from starlette.convertors import CONVERTOR_TYPES, Convertor, register_url_convertor
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response as StarletteResponse
from starlette.routing import Match
from starlette.types import Scope

from patzilla.web.context import request_context
from patzilla.web.exceptions import HTTPException, HTTPNotFound
from patzilla.web.render import render
from patzilla.web.request import MultiDict, Request
from patzilla.web.response import ResponseMixin, StarletteResponseAdapter

logger = logging.getLogger(__name__)

Handler = t.Callable[[Request], t.Any]
Dispatcher = t.Callable[[Request], t.Any]

ALL_METHODS = ["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]

_PATTERN_PARAM = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)(?::((?:[^{}]|\{[^{}]*\})*))?\}")


class _RegexConvertor(Convertor):
    regex = ""

    def convert(self, value: str) -> str:
        return value

    def to_string(self, value: t.Any) -> str:
        return str(value)


def _regex_convertor(regex: str) -> str:
    """
    Register a Starlette path convertor for a regular expression, return its name.
    """
    name = "re_" + hashlib.sha1(regex.encode("utf-8")).hexdigest()[:12]
    if name not in CONVERTOR_TYPES:
        convertor_class = type(f"RegexConvertor_{name}", (_RegexConvertor,), {"regex": regex})
        register_url_convertor(name, convertor_class())
    return name


def convert_path(pattern: str) -> str:
    """
    Translate a Pyramid route pattern into a Starlette path.

    >>> convert_path("/api/ops/{patent}/claims")
    '/api/ops/{patent}/claims'
    """
    if not pattern.startswith("/"):
        pattern = "/" + pattern

    def replace(match: t.Match[str]) -> str:
        name, regex = match.group(1), match.group(2)
        if regex is None:
            return "{%s}" % name
        return "{%s:%s}" % (name, _regex_convertor(regex))

    return _PATTERN_PARAM.sub(replace, pattern)


def path_parameters(pattern: str) -> t.List[str]:
    return [match.group(1) for match in _PATTERN_PARAM.finditer(pattern)]


async def read_form(request: StarletteRequest) -> MultiDict:
    form = await request.form()
    return MultiDict(form.multi_items())


def process_request(request: Request, dispatcher: Dispatcher) -> StarletteResponse:
    """
    Run request subscribers and the dispatcher, then convert the result into a Starlette response.
    This is invoked within a worker thread.
    """
    with request_context(request):
        try:
            if request.registry is not None:
                request.registry.notify_request(request)
            response = dispatcher(request)
        except HTTPException as ex:
            response = ex

        target = response if isinstance(response, ResponseMixin) else StarletteResponseAdapter(response)
        for callback in request.response_callbacks:
            callback(request, target)

        if isinstance(response, ResponseMixin):
            return response.to_starlette(accept=request.headers.get("Accept"), base_url=request.url)
        return response


def build_endpoint(dispatcher: Dispatcher) -> t.Callable[[StarletteRequest], t.Awaitable[StarletteResponse]]:
    """
    Create an ASGI endpoint for a synchronous dispatcher.
    """

    async def endpoint(request: StarletteRequest) -> StarletteResponse:
        body = await request.body()
        form = None
        if request.headers.get("content-type", "").lower().startswith("multipart/form-data"):
            form = await read_form(request)
        patzilla_request = Request.from_starlette(
            request, body=body, registry=request.app.state.registry, form=form,
        )
        try:
            return await run_in_threadpool(process_request, patzilla_request, dispatcher)
        finally:
            if form is not None:
                await request.close()

    return endpoint


def to_response(request: Request, result: t.Any, renderer: t.Optional[str]) -> t.Any:
    """
    Pass through responses returned by handlers, otherwise render the result.
    """
    if isinstance(result, (ResponseMixin, StarletteResponse)):
        return result
    if renderer is None and isinstance(result, str):
        # Handlers without a renderer must return a response, but be graceful.
        request.response.content_type = "text/plain"
    return render(request, result, renderer)


class PatzillaRoute(APIRoute):
    """
    A FastAPI route which can be constrained by a regular expression
    on the request path, like Pyramid's ``path_info`` route predicate.
    """

    def __init__(self, *args: t.Any, path_info: t.Optional[str] = None, **kwargs: t.Any):
        super().__init__(*args, **kwargs)
        self.path_info_regex = re.compile(path_info) if path_info else None

    def matches(self, scope: Scope) -> t.Tuple[Match, Scope]:
        match, child_scope = super().matches(scope)
        if match != Match.NONE and self.path_info_regex is not None:
            path, root_path = scope.get("path", ""), scope.get("root_path", "")
            if root_path and path.startswith(root_path):
                path = path[len(root_path):]
            if not self.path_info_regex.match(path):
                return Match.NONE, {}
        return match, child_scope


class View:
    """
    A handler for a route, optionally constrained by predicates.
    """

    def __init__(
        self,
        handler: Handler,
        renderer: t.Optional[str] = None,
        request_method: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        request_param: t.Optional[str] = None,
    ):
        self.handler = handler
        self.renderer = renderer
        if isinstance(request_method, str):
            request_method = [request_method]
        self.request_methods = [method.upper() for method in request_method] if request_method else None
        if self.request_methods and "GET" in self.request_methods and "HEAD" not in self.request_methods:
            self.request_methods.append("HEAD")
        self.request_param = request_param

    @property
    def predicate_count(self) -> int:
        return int(self.request_methods is not None) + int(self.request_param is not None)

    def matches(self, request: Request) -> bool:
        if self.request_methods is not None and request.method not in self.request_methods:
            return False
        if self.request_param is not None:
            key, has_value, value = self.request_param.partition("=")
            if key not in request.params:
                return False
            if has_value and request.params.get(key) != value:
                return False
        return True


class RouteDefinition:
    def __init__(self, name: str, pattern: str, path_info: t.Optional[str] = None):
        self.name = name
        self.pattern = pattern
        self.path_info = path_info
        self.views: t.List[View] = []

    def dispatch(self, request: Request) -> t.Any:
        # Like Pyramid, try more specific views first.
        for view in sorted(self.views, key=lambda item: -item.predicate_count):
            if view.matches(request):
                return to_response(request, view.handler(request), view.renderer)
        raise HTTPNotFound()


class RouteTable:
    """
    An ordered table of web page routes. Routes are matched in the order they have been added.
    """

    def __init__(self, prefix: str = ""):
        self.prefix = prefix.rstrip("/")
        self.routes: t.Dict[str, RouteDefinition] = {}

    def add(
        self,
        name: str,
        pattern: str,
        handler: t.Optional[Handler] = None,
        renderer: t.Optional[str] = None,
        request_method: t.Optional[t.Union[str, t.Sequence[str]]] = None,
        request_param: t.Optional[str] = None,
        path_info: t.Optional[str] = None,
    ) -> "RouteTable":
        """
        Add a route, or another view to an existing route of the same name.
        Routes without views respond with "404 Not Found".
        """
        if name not in self.routes:
            if not pattern.startswith("/"):
                pattern = "/" + pattern
            self.routes[name] = RouteDefinition(name, self.prefix + pattern, path_info=path_info)
        if handler is not None:
            self.routes[name].views.append(
                View(handler, renderer=renderer, request_method=request_method, request_param=request_param)
            )
        return self

    def api_routes(self) -> t.List[APIRoute]:
        routes = []
        for definition in self.routes.values():
            if not definition.views:
                continue
            routes.append(
                PatzillaRoute(
                    convert_path(definition.pattern),
                    build_endpoint(definition.dispatch),
                    methods=ALL_METHODS,
                    name=definition.name,
                    include_in_schema=False,
                    path_info=definition.path_info,
                )
            )
        return routes
