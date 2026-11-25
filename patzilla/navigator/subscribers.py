# -*- coding: utf-8 -*-
# (c) 2013-2026 Andreas Motl <andreas.motl@ip-tools.org>
import logging
from patzilla.web.context import get_current_request
from patzilla.navigator import helpers

log = logging.getLogger(__name__)


def setup(registry):
    """Configure all application-specific subscribers."""
    registry.add_request_subscriber(create_url_generators)
    registry.add_renderer_globals(add_renderer_globals)


class ApplicationURLGenerator:
    """
    Generate application URLs within templates and views.

    - ``url.app``: The application prefix of the URL. Append a slash to get the home page URL.
    - ``url.route(name, **params)``: The URL of a named route.
    """

    def __init__(self, request, qualified=False):
        self.request = request
        self.qualified = qualified

    @property
    def app(self):
        if self.qualified:
            return self.request.application_url
        return self.request.script_name

    def route(self, route_name, *elements, **kw):
        return self.request.route_url(route_name, **kw)

    __call__ = route


def create_url_generators(event):
    """A request subscriber. I create various
    URL generators and attach them to the request.
    Templates and views can then use them to generate application URLs.

    - ``request.url_generator``: Generates URLs to application routes
    """

    request = event.request
    request.url_generator = ApplicationURLGenerator(request, qualified=False)


def add_renderer_globals(event):
    """A renderer globals subscriber. I add
    some renderer globals with values that are familiar to Pylons
    users.
    """

    # use event as renderer globals
    renderer_globals = event

    renderer_globals["h"] = helpers
    request = event.get("request") or get_current_request()
    if not request:     # pragma: no cover
        return
    renderer_globals["r"] = request
    renderer_globals["url"] = request.url_generator

    # Propagate theme settings
    renderer_globals['theme'] = request.runtime_settings.theme
    renderer_globals['page_title'] = None
