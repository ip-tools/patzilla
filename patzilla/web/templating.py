# -*- coding: utf-8 -*-
# (c) 2026 Andreas Motl <andreas.motl@ip-tools.org>
"""
Mako templates, referenced by asset specification, e.g. `patzilla.navigator:templates/login.html`.
Like `pyramid_mako`, expressions are HTML-escaped by default; use `${value | n}` for raw markup.
"""
import importlib.util
import types
import typing as t
from typing import Annotated

from fastapi import Depends, Request
from fastapi.responses import HTMLResponse
from mako.lookup import TemplateLookup

from patzilla.web.dependencies import Runtime, State


class MakoTemplates:

    def __init__(self, reload: bool = False):
        self.reload = reload
        self.lookups: t.Dict[str, TemplateLookup] = {}

    def get_template(self, asset_spec: str):
        package, _, path = asset_spec.partition(":")
        if package not in self.lookups:
            spec = importlib.util.find_spec(package)
            if spec is None or not spec.submodule_search_locations:
                raise ValueError(f"Unable to locate package for templates: {package}")
            self.lookups[package] = TemplateLookup(
                directories=list(spec.submodule_search_locations)[:1],
                input_encoding="utf-8",
                default_filters=["h"],
                filesystem_checks=self.reload,
            )
        return self.lookups[package].get_template("/" + path)

    def render(self, asset_spec: str, **namespace) -> str:
        return self.get_template(asset_spec).render_unicode(**namespace)


class Page:
    """
    Render navigator pages, providing the template globals `request`/`r`, `h`, `url`, `theme`, and `page_title`.
    """

    def __init__(self, request: Request, state: State, runtime: Runtime):
        self.request = request
        self.templates = state.templates
        self.runtime = runtime

    def render(self, template: str, context: t.Optional[t.Mapping] = None, status_code: int = 200) -> HTMLResponse:
        from patzilla.navigator.helpers import TemplateHelpers

        namespace = {
            "request": self.request,
            "r": self.request,
            "h": TemplateHelpers(self.runtime),
            "url": types.SimpleNamespace(app=self.request.scope.get("root_path", "")),
            "theme": getattr(self.runtime, "theme", None),
            "page_title": None,
        }
        namespace.update(context or {})
        return HTMLResponse(self.templates.render(template, **namespace), status_code=status_code)


PageRenderer = Annotated[Page, Depends(Page)]
