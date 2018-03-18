# -*- coding: utf-8 -*-
# (c) 2013-2017 Andreas Motl, Elmyra UG
import logging
from pyramid.threadlocal import get_current_request
from pyramid.url import route_url
from akhet.urlgenerator import URLGenerator as ApplicationURLGenerator
from patzilla.navigator.settings import GlobalSettings, RuntimeSettings
from patzilla.navigator import helpers

log = logging.getLogger(__name__)


def includeme(config):
    """Configure all application-specific subscribers."""
    #config.add_subscriber(global_config, "pyramid.events.ApplicationCreated")
    config.add_subscriber(runtime_config, "pyramid.events.ContextFound")
    config.add_subscriber(create_url_generators, "pyramid.events.ContextFound")
    #config.add_subscriber(create_tools, "pyramid.events.ContextFound")
    config.add_subscriber(add_renderer_globals, "pyramid.events.BeforeRender")

def global_config(event):
    """
    A subscriber for ``pyramid.events.ApplicationCreated`` events.
    """
    registry = event.app.registry

def runtime_config(event):
    """
    A subscriber for ``pyramid.events.ContextFound`` events.
    I create the runtime configuration object and attach it to the request.
    """
    event.request.runtime_settings = RuntimeSettings()

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


def create_tools(event):
    """A subscriber for ``pyramid.events.ContextFound`` events. I create various
    tools and attach them to the request.

    - ``request.geolocator``: Queries geolocation service for geographic position
    """
    request = event.request
    #request.geolocator = GeoLocator(request)


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
