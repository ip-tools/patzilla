# -*- coding: utf-8 -*-
# (c) 2013,2014 Andreas Motl, Elmyra UG
import logging
from patzilla.util.config import read_config, read_list, asbool
from patzilla.util.data.container import SmartBunch
from pyramid.threadlocal import get_current_request
from pyramid.url import route_url
from akhet.urlgenerator import URLGenerator as ApplicationURLGenerator

from . import helpers

site_version = '0.0.0'

log = logging.getLogger(__name__)


def includeme(config):
    """Configure all application-specific subscribers."""
    config.add_subscriber(global_config, "pyramid.events.ApplicationCreated")
    config.add_subscriber(create_url_generators, "pyramid.events.ContextFound")
    config.add_subscriber(create_tools, "pyramid.events.ContextFound")
    config.add_subscriber(add_renderer_globals, "pyramid.events.BeforeRender")

def global_config(event):
    registry = event.app.registry
    pyramid_settings = registry.settings

    # Read configuration file to get global settings
    # TODO: Optimize: Only read once, not on each request!
    application_settings = read_config(pyramid_settings['CONFIG_FILE'], kind=SmartBunch)

    # Provide Paste configuration via registry object
    registry.application_settings = application_settings


    # Compute datasource settings
    datasource_settings = SmartBunch({
        'datasources': [],
        'datasource': SmartBunch(),
        'total': SmartBunch.bunchify({'fulltext_countries': [], 'details_countries': []}),
        })

    # Read system settings from configuration
    datasource_settings.datasources = read_list(application_settings.get('ip_navigator', {}).get('datasources'))
    datasource_settings.protected_fields = read_list(application_settings.get('ip_navigator', {}).get('datasources_protected_fields'))
    for datasource in datasource_settings.datasources:
        application_settings_key = 'datasource_{name}'.format(name=datasource)
        datasource_info = application_settings.get(application_settings_key, {})
        datasource_info['fulltext_enabled'] = asbool(datasource_info.get('fulltext_enabled', False))
        datasource_info['fulltext_countries'] = read_list(datasource_info.get('fulltext_countries', ''))
        datasource_info['details_enabled'] = asbool(datasource_info.get('details_enabled', False))
        datasource_info['details_countries'] = read_list(datasource_info.get('details_countries', ''))
        datasource_settings.datasource[datasource] = SmartBunch.bunchify(datasource_info)

        # Aggregate data for all countries
        datasource_settings.total.fulltext_countries += datasource_info['fulltext_countries']

    registry.datasource_settings = datasource_settings

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

    # Page title
    renderer_globals['theme'] = helpers.Bootstrapper().theme_parameters()
    renderer_globals['page_title'] = None
