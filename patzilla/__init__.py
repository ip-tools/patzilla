# -*- coding: utf-8 -*-
# (c) 2013-2022 Andreas Motl <andreas.motl@ip-tools.org>
import logging

from pyramid.config import Configurator

from patzilla.boot.logging import suppress_warnings
from patzilla.navigator.settings import GlobalSettings
from patzilla.util.web.pyramid.renderer import PngRenderer, XmlRenderer, PdfRenderer, NullRenderer


logger = logging.getLogger(__name__)


def before_start():
    """
    All things which should be done before anything other. Probably monkey
    patches and similar topics.
    """

    # This module carries a monkeypatch, make sure it is invoked before any other imports.
    import patzilla.util.web.pyramid.cornice


def configure(global_config, **settings):
    """
    Bootstrap Pyramid application configuration.
    """

    # Create Pyramid and application configuration objects.
    config = Configurator(settings=settings)
    global_settings = GlobalSettings(global_config.get('__file__'))

    # Propagate global settings to application registry.
    registry = config.registry
    registry.global_settings = global_settings

    # Propagate specific configuration topics to application registry.
    registry.application_settings = global_settings.application_settings
    registry.datasource_settings = global_settings.datasource_settings
    registry.vendor_settings = global_settings.vendor_settings

    return config


def minimal(global_config, **settings):
    """
    Pyramid WSGI application factory with minimal footprint,
    suitable for CLI usage and software tests.
    """

    # Prepare runtime environment.
    before_start()

    # Baseline configuration.
    config = configure(global_config, **settings)

    # Mark environment flavor.
    config.registry.app_flavor = "minimal"

    # Register community addons.
    config.include('cornice')

    # Register application addons.
    config.include("patzilla.navigator.opaquelinks")

    # Register application components.
    # TODO: Refactor user context bootstrapping to `patzilla.boot.user`, maybe.
    config.include("patzilla.util.web.identity.service")
    config.include("patzilla.boot.settings")

    # Register subsystem components.
    config.include("patzilla.access")

    logger.info("Application is ready to serve requests. Enjoy your research.")
    return config.make_wsgi_app()


def web(global_config, **settings):
    """
    Pyramid WSGI application factory for a full server application.
    """

    # Prepare runtime environment.
    before_start()

    # Baseline configuration.
    config = configure(global_config, **settings)

    # Mark environment flavor.
    config.registry.app_flavor = "web"

    # Add renderers.
    config.include('pyramid_mako')
    config.add_mako_renderer('.html')
    config.add_renderer('xml', XmlRenderer)
    config.add_renderer('png', PngRenderer)
    config.add_renderer('pdf', PdfRenderer)
    config.add_renderer('null', NullRenderer)

    # Register community addons.
    config.include('pyramid_beaker')
    config.include('cornice')
    #config.include("akhet.static")

    # Register application addons.
    config.include("patzilla.util.web.pyramid")
    config.include("patzilla.util.database.beaker_mongodb_gridfs")

    # Register application components.
    config.include("patzilla.util.web.identity")

    # Register subsystem components.
    config.include("patzilla.navigator")

    # Boot application.
    config.include("patzilla.boot.settings")
    config.include("patzilla.access")

    # Register all routes/handlers defined by function decorators.
    config.scan(ignore="patzilla.util.web.uwsgi.uwsgidecorators")

    logger.info("Application is ready to serve requests. Enjoy your research.")
    return config.make_wsgi_app()


# Suppress some "Python 2 is EOL" deprecation warnings.
suppress_warnings()
