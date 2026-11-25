# -*- coding: utf-8 -*-
# (c) 2013-2026 Andreas Motl <andreas.motl@ip-tools.org>
"""
Renderers convert data returned by request handlers into responses.

Available renderers:

- ``json``:       JSON, the default for API services. Like Cornice, the content
                  type is negotiated between ``application/json`` and ``text/plain``.
- ``prettyjson``: Indented JSON with sorted keys.
- ``xml``, ``png``, ``pdf``: Pass the payload through, setting the content type.
- ``null``:       Pass the payload through, retaining ``request.response.content_type``.
- Mako templates, referenced by asset specification, e.g.
  ``patzilla.navigator:templates/standalone.html``.
"""
import importlib.util
import json
import os
import typing as t

import simplejson
from mako.lookup import TemplateLookup

from patzilla.web.response import Response

if t.TYPE_CHECKING:  # pragma: no cover
    from patzilla.web.request import Request


PASSTHROUGH_CONTENT_TYPES = {
    "xml": "text/xml",
    "png": "image/png",
    "pdf": "application/pdf",
}


def is_template(renderer: t.Optional[str]) -> bool:
    return renderer is not None and renderer.endswith((".html", ".mako"))


def json_default(request: "Request") -> t.Callable[[t.Any], t.Any]:
    def default(obj: t.Any) -> t.Any:
        if hasattr(obj, "__json__"):
            return obj.__json__(request)
        raise TypeError(f"{obj!r} is not JSON serializable")

    return default


def assign_body(response: Response, value: t.Any) -> None:
    """
    Assign the result of a request handler to the response body, like Pyramid does.
    """
    if value is None:
        return
    if isinstance(value, str):
        response.text = value
    elif isinstance(value, (bytes, bytearray, memoryview)):
        response.body = bytes(value)
    elif hasattr(value, "read"):
        response.body = value.read()
    elif isinstance(value, t.Mapping):
        raise TypeError("Unable to use a mapping as response body, the handler needs a renderer")
    elif hasattr(value, "__iter__"):
        response.body = b"".join(chunk.encode(response.charset or "UTF-8") if isinstance(chunk, str) else chunk
                                 for chunk in value)
    else:
        raise TypeError(f"Unable to use value of type {type(value).__name__} as response body")


def render(request: "Request", value: t.Any, renderer: t.Optional[str]) -> Response:
    """
    Render a value returned by a request handler into ``request.response``.
    """
    response = request.response

    if renderer == "json":
        if response.status_code == 204:
            response.content_type = None
            return response
        offers = request.accept.acceptable_offers(["application/json", "text/plain"])
        response.content_type = offers[0][0] if offers else "application/json"
        if response.content_type == "application/json" and not response._charset_explicit:
            response._charset = None
        response.text = json.dumps(value, default=json_default(request))

    elif renderer == "prettyjson":
        response.content_type = "application/json"
        response.text = simplejson.dumps(value, use_decimal=True, sort_keys=True, indent=4)

    elif renderer in PASSTHROUGH_CONTENT_TYPES:
        response.content_type = PASSTHROUGH_CONTENT_TYPES[renderer]
        assign_body(response, value)

    elif renderer == "null" or renderer is None:
        assign_body(response, value)

    elif is_template(renderer):
        templates: TemplateRenderer = request.registry.template_renderer  # type: ignore[union-attr]
        response.text = templates.render(renderer, request, value)

    else:
        raise ValueError(f"Unknown renderer: {renderer}")

    return response


class TemplateRenderer:
    """
    Render Mako templates referenced by asset specification (``package:path``).

    The settings correspond to the defaults of ``pyramid_mako``: Expressions are
    HTML-escaped by default, use ``${value | n}`` to emit raw markup.
    """

    def __init__(self, reload: bool = False):
        self.reload = reload
        self.lookups: t.Dict[str, TemplateLookup] = {}

    def lookup(self, package: str) -> TemplateLookup:
        if package not in self.lookups:
            spec = importlib.util.find_spec(package)
            if spec is None or not spec.submodule_search_locations:
                raise ValueError(f"Unable to locate package for templates: {package}")
            directory = list(spec.submodule_search_locations)[0]
            self.lookups[package] = TemplateLookup(
                directories=[directory],
                input_encoding="utf-8",
                default_filters=["h"],
                filesystem_checks=self.reload,
            )
        return self.lookups[package]

    def get_template(self, asset_spec: str) -> t.Any:
        package, _, path = asset_spec.partition(":")
        if not path:
            raise ValueError(f"Template references must be asset specifications (package:path): {asset_spec}")
        return self.lookup(package).get_template("/" + path.replace(os.sep, "/"))

    def render(self, asset_spec: str, request: "Request", value: t.Optional[t.Mapping[str, t.Any]]) -> str:
        system: t.Dict[str, t.Any] = {
            "request": request,
            "req": request,
            "_context": None,
            "view": None,
            "renderer_name": asset_spec,
        }
        namespace = dict(request.registry.notify_render(system, value)) if request.registry else system  # type: ignore[union-attr]
        if value:
            namespace.update(value)
        return self.get_template(asset_spec).render_unicode(**namespace)
