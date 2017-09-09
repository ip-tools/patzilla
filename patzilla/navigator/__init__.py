# -*- coding: utf-8 -*-
# (c) 2013-2017 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
from ConfigParser import NoOptionError
from patzilla.util.config import read_config
from patzilla.util.data.container import SmartBunch
from patzilla.version import __VERSION__
from patzilla.navigator.util import PngRenderer, XmlRenderer, PdfRenderer, NullRenderer
from pyramid.config import Configurator

def main(global_config, **settings):
    """This function returns a Pyramid WSGI application."""

    settings.setdefault('CONFIG_FILE', global_config.get('__file__'))
    settings.setdefault('SOFTWARE_VERSION', __VERSION__)

    application_settings = read_config(settings['CONFIG_FILE'], kind=SmartBunch)
    try:
        datasources = application_settings.ip_navigator.datasources
    except:
        raise NoOptionError('datasources', 'ip_navigator')

    config = Configurator(settings=settings)
    config.registry.application_settings = application_settings

    # Addons
    config.include('pyramid_mako')
    config.include('pyramid_fanstatic')
    config.include('pyramid_beaker')
    config.include('cornice')

    # Register generic components: URL generator, renderer globals
    config.include(".subscribers")
    config.include(".views")
    #config.include("akhet.static")

    # Register subsystem components
    config.include("patzilla.util.web.identity")
    config.include("patzilla.util.database.beaker_mongodb_gridfs")
    config.include("patzilla.util.web.pyramid")
    config.include("patzilla.navigator.opaquelinks")

    if 'ops' in datasources:
        config.include("patzilla.access.epo.ops.client")

    if 'depatisconnect' in datasources:
        config.include("patzilla.access.dpma.depatisconnect")

    if 'ificlaims' in datasources:
        config.include("patzilla.access.ificlaims.clientpool")

    if 'depatech' in datasources:
        config.include("patzilla.access.depatech.clientpool")

    config.add_renderer('.html', 'pyramid.mako_templating.renderer_factory')
    config.add_renderer('xml', XmlRenderer)
    config.add_renderer('png', PngRenderer)
    config.add_renderer('pdf', PdfRenderer)
    config.add_renderer('null', NullRenderer)

    # Views and routes
    config.add_static_view('static', 'static', cache_max_age=3600)
    #config.add_static_view('static', 'static', cache_max_age=0)
    config.add_route('home', '/')

    config.scan()

    return config.make_wsgi_app()
