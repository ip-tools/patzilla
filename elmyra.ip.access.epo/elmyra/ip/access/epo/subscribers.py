# -*- encoding: utf-8 -*-
import logging
import itertools
import pyramid.threadlocal as threadlocal
from pyramid.url import route_url
from akhet.urlgenerator import URLGenerator as ApplicationURLGenerator

import fanstatic

from . import helpers

site_version = '0.0.0'

log = logging.getLogger(__name__)


def includeme(config):
    """Configure all application-specific subscribers."""
    config.add_subscriber(create_url_generators, "pyramid.events.ContextFound")
    config.add_subscriber(create_tools, "pyramid.events.ContextFound")
    config.add_subscriber(add_renderer_globals, "pyramid.events.BeforeRender")
    config.add_subscriber(add_html_foundation, "pyramid.events.BeforeRender")


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

    # initialize fanstatic
    #needed = fanstatic.init_needed(base_url='http://localhost:6543')
    #renderer_globals["needed"] = needed

    renderer_globals["h"] = helpers
    request = event.get("request") or threadlocal.get_current_request()
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

    # Site title
    """
    those three variables belong together. the browsertitle is:
    - ``page_title + site_title`` or
    - ``site_title + site_claim``

    the title on the page is only rendered if ``page_title is not None``
    """
    renderer_globals['page_title'] = None
    renderer_globals['site_title'] = u"elmyra.ip.access.epo"
    renderer_globals['site_claim'] = u"EPO OPS access"

    renderer_globals['site_version'] = site_version


def add_html_foundation(event):

    # include all javascript/css frameworks

    # backbone.marionette
    from js.marionette import marionette
    marionette.need()

    # bootstrap
    from js.bootstrap import bootstrap
    #from js.bootstrap import bootstrap_theme
    bootstrap.need()
    #bootstrap_theme.need()

    # jquery
    from js.jquery import jquery
    jquery.need()

    # jqueryui
    #from js.jqueryui import jqueryui, base as jqueryui_base, smoothness as jqueryui_smoothness
    #from js.jqueryui_bootstrap import jqueryui_bootstrap
    #jqueryui.need()
    #jqueryui_base.need()
    #jqueryui_smoothness.need()
    #jqueryui_bootstrap.need()

    #from css.fontawesome import fontawesome
    #fontawesome.need()
