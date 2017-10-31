# -*- coding: utf-8 -*-
# (c) 2013-2017 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
from pyramid.config import Configurator
from patzilla.version import __version__
from patzilla.util.config import read_config
from patzilla.util.data.container import SmartBunch
from patzilla.util.web.pyramid.renderer import PngRenderer, XmlRenderer, PdfRenderer, NullRenderer

def main(global_config, **settings):
    """This function returns a Pyramid WSGI application."""

    settings.setdefault('CONFIG_FILE', global_config.get('__file__'))
    settings.setdefault('SOFTWARE_VERSION', __version__)

    config = Configurator(settings=settings)

    application_settings = read_config(settings['CONFIG_FILE'], kind=SmartBunch)
    config.registry.application_settings = application_settings

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

    # Register subsystem components
    config.include("patzilla.util.web.identity")
    config.include("patzilla.util.web.pyramid")
    config.include("patzilla.util.database.beaker_mongodb_gridfs")

    config.include("patzilla.access")
    config.include("patzilla.navigator")

    #config.scan()

    return config.make_wsgi_app()
