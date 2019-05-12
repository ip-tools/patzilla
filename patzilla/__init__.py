# -*- coding: utf-8 -*-
# (c) 2013-2018 Andreas Motl <andreas.motl@ip-tools.org>
from pyramid.config import Configurator
from patzilla.navigator.settings import GlobalSettings
from patzilla.util.web.pyramid.renderer import PngRenderer, XmlRenderer, PdfRenderer, NullRenderer

def main(global_config, **settings):
    """This function returns a Pyramid WSGI application."""

    config = Configurator(settings=settings)
    registry = config.registry

    global_settings = GlobalSettings(global_config.get('__file__'))

    # Propagate global settings to application registry
    registry.global_settings      = global_settings

    # Propagate some configuration topics to application registry
    registry.application_settings = global_settings.application_settings
    registry.datasource_settings  = global_settings.datasource_settings
    registry.vendor_settings      = global_settings.vendor_settings


    # Add renderers
    config.include('pyramid_mako')
    config.add_mako_renderer('.html')
    config.add_renderer('xml', XmlRenderer)
    config.add_renderer('png', PngRenderer)
    config.add_renderer('pdf', PdfRenderer)
    config.add_renderer('null', NullRenderer)

    # Register addons
    config.include('pyramid_beaker')
    config.scan('patzilla.util.web.pyramid.cornice')
    config.include('cornice')
    #config.include("akhet.static")

    config.include("patzilla.util.web.pyramid")
    config.include("patzilla.util.database.beaker_mongodb_gridfs")

    # Register subsystem components
    config.include("patzilla.util.web.identity")
    config.include("patzilla.navigator")
    config.include("patzilla.access")

    #config.scan()

    return config.make_wsgi_app()
