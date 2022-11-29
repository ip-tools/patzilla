# -*- coding: utf-8 -*-
# (c) 2013-2022 Andreas Motl <andreas.motl@ip-tools.org>
import logging
from pyramid.threadlocal import get_current_request
from pyramid.url import route_url
from akhet.urlgenerator import URLGenerator as ApplicationURLGenerator
from patzilla.navigator import helpers

log = logging.getLogger(__name__)


def includeme(config):
    """Configure all application-specific subscribers."""
    config.add_subscriber(create_url_generators, "pyramid.events.ContextFound")
    config.add_subscriber(add_renderer_globals, "pyramid.events.BeforeRender")


def create_url_generators(event):
    """A subscriber for ``pyramid.events.ContextFound`` events. I create various
    URL generators and attach them to the request.
    Templates and views can then use them to generate application URLs.

    - ``request.url_generator``: Generates URLs to application routes
    - ``request.blob_url_generator``: Generates URLs to the ``BlobStore`
    """

    request = event.request
    context = request.context

    app_url_generator = ApplicationURLGenerator(context, request, qualified=False)
    request.url_generator = app_url_generator

    #blob_url_generator = BlobURLGenerator(context, request, qualified=False)
    #request.blob_url_generator = blob_url_generator


def add_renderer_globals(event):
    """A subscriber for ``pyramid.events.BeforeRender`` events.  I add
    some :term:`renderer globals` with values that are familiar to Pylons
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
    #renderer_globals["bloburl"] = request.blob_url_generator

    # Optional additions:
    #renderer_globals["settings"] = request.registry.settings
    #try:
    #    renderer_globals["session"] = request.session
    #except ConfigurationError:
    #    pass
    #renderer_globals["c"] = request.tmpl_context

    # Propagate theme settings
    renderer_globals['theme'] = request.runtime_settings.theme
    renderer_globals['page_title'] = None
