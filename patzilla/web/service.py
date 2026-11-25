# -*- coding: utf-8 -*-
# (c) 2026 Andreas Motl <andreas.motl@ip-tools.org>
"""
Declarative API services, the replacement for ``cornice.Service``.

A ``Service`` bundles one URL path with handlers per HTTP method, optionally
distinguished by the ``Accept`` header. It is mounted as a single FastAPI route,
documented in the OpenAPI schema.

Semantics retained from Cornice:

- Handlers receive the request and return data, which is rendered as JSON by default.
- Errors added to ``request.errors`` are reported using the JSON error envelope,
  see ``patzilla.web.errors``.
- Requests with an unsupported HTTP method yield "405 Method Not Allowed", and
  requests with an unacceptable ``Accept`` header yield "406 Not Acceptable".
- ``GET`` handlers also respond to ``HEAD`` requests.

Usage::

    ops_claims_service = Service(name="ops-claims", path="/api/ops/{patent}/claims", description="...")

    @ops_claims_service.get()
    def ops_claims_handler(request):
        return ops_claims(request.matchdict["patent"])
"""
import typing as t

from patzilla.web.errors import JSONError
from patzilla.web.exceptions import HTTPMethodNotAllowed, HTTPNotFound
from patzilla.web.routing import Handler, PatzillaRoute, build_endpoint, convert_path, path_parameters, to_response

if t.TYPE_CHECKING:  # pragma: no cover
    from patzilla.web.request import Request

# Pyramid's default order of preference when multiple handlers are
# distinguished by ``Accept``, and the client accepts all of them equally.
DEFAULT_ACCEPT_ORDER = [
    "text/html",
    "application/xhtml+xml",
    "application/xml",
    "text/xml",
    "text/plain",
    "application/json",
]


class Definition:
    def __init__(self, method: str, handler: Handler, accept: t.Optional[t.Sequence[str]], renderer: t.Optional[str]):
        self.method = method
        self.handler = handler
        self.accept = list(accept) if accept else []
        self.renderer = renderer or "json"


class Service:
    """
    An API service, see module docstring.
    """

    def __init__(self, name: str, path: str, description: t.Optional[str] = None, renderer: t.Optional[str] = None,
                 **kwargs: t.Any):
        self.name = name
        self.path = path
        self.description = description
        self.renderer = renderer
        self.definitions: t.List[Definition] = []

    def __repr__(self) -> str:
        return f"<Service {self.name} at {self.path}>"

    def add_view(self, method: str, handler: Handler, accept: t.Optional[t.Union[str, t.Sequence[str]]] = None,
                 renderer: t.Optional[str] = None) -> None:
        if isinstance(accept, str):
            accept = [accept]
        self.definitions.append(Definition(method.upper(), handler, accept, renderer or self.renderer))

    def decorator(self, method: str, accept: t.Optional[t.Union[str, t.Sequence[str]]] = None,
                  renderer: t.Optional[str] = None, **kwargs: t.Any) -> t.Callable[[Handler], Handler]:
        def wrapper(handler: Handler) -> Handler:
            self.add_view(method, handler, accept=accept, renderer=renderer)
            return handler

        return wrapper

    def get(self, **kwargs: t.Any) -> t.Callable[[Handler], Handler]:
        return self.decorator("GET", **kwargs)

    def post(self, **kwargs: t.Any) -> t.Callable[[Handler], Handler]:
        return self.decorator("POST", **kwargs)

    def put(self, **kwargs: t.Any) -> t.Callable[[Handler], Handler]:
        return self.decorator("PUT", **kwargs)

    def delete(self, **kwargs: t.Any) -> t.Callable[[Handler], Handler]:
        return self.decorator("DELETE", **kwargs)

    @property
    def defined_methods(self) -> t.List[str]:
        methods: t.List[str] = []
        for definition in self.definitions:
            if definition.method not in methods:
                methods.append(definition.method)
            if definition.method == "GET" and "HEAD" not in methods:
                methods.append("HEAD")
        return methods

    def select(self, request: "Request") -> Definition:
        """
        Select the handler definition for a request, by HTTP method and ``Accept`` header.
        """
        method = "GET" if request.method == "HEAD" else request.method
        candidates = [definition for definition in self.definitions if definition.method == method]
        if not candidates:
            raise HTTPMethodNotAllowed(request_method=request.method,
                                       headers={"Allow": ", ".join(self.defined_methods)})

        offers: t.List[t.Tuple[str, Definition]] = []
        for definition in candidates:
            for offer in definition.accept:
                offers.append((offer, definition))

        if offers:
            def order(item: t.Tuple[int, t.Tuple[str, Definition]]) -> t.Tuple[int, int]:
                index, (offer, _) = item
                try:
                    return DEFAULT_ACCEPT_ORDER.index(offer), index
                except ValueError:
                    return len(DEFAULT_ACCEPT_ORDER), index

            ordered = [offer for _, offer in sorted(enumerate(offers), key=order)]
            ordered_offers = [offer for offer, _ in ordered]
            for offer, _ in request.accept.acceptable_offers(ordered_offers):
                for candidate_offer, definition in ordered:
                    if candidate_offer == offer:
                        return definition

        plain = [definition for definition in candidates if not definition.accept]
        if plain:
            return plain[0]

        if offers:
            acceptable = sorted({offer for offer, _ in offers})
            request.errors.add("header", "Accept", "Accept header should be one of {0}".format(acceptable))
            request.errors.status = 406
            raise JSONError(errors=request.errors, status=406)

        raise HTTPNotFound()

    def dispatch(self, request: "Request") -> t.Any:
        definition = self.select(request)
        result = definition.handler(request)
        if len(request.errors) > 0:
            return JSONError(errors=request.errors, status=request.errors.status)
        return to_response(request, result, definition.renderer)

    def api_route(self) -> t.Optional[PatzillaRoute]:
        """
        Build a FastAPI route for this service. Services without handlers are not mounted.
        """
        if not self.definitions:
            return None
        parameters = [
            {"name": name, "in": "path", "required": True, "schema": {"type": "string"}}
            for name in path_parameters(self.path)
            if not name.startswith("dummy")
        ]
        tags = [segment for segment in self.path.split("/") if segment and segment != "api"][:1]
        return PatzillaRoute(
            convert_path(self.path),
            build_endpoint(self.dispatch),
            methods=self.defined_methods,
            name=self.name,
            summary=self.description,
            tags=tags or None,
            openapi_extra={"parameters": parameters} if parameters else None,
        )
