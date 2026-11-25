# -*- coding: utf-8 -*-
# (c) 2026 Andreas Motl <andreas.motl@ip-tools.org>
"""
PatZilla's web application layer, based on FastAPI / Starlette.

Overview of how the concepts of the previous Pyramid/Cornice
implementation map onto this package:

- ``Configurator``, ``config.include``    -> ``patzilla.web.registry.Registry``, ``registry.include``
- ZCA utilities (``registerUtility``)     -> plain attributes on the ``Registry``
- ``ContextFound`` subscribers            -> ``registry.add_request_subscriber``
- ``BeforeRender`` subscribers            -> ``registry.add_renderer_globals``
- ``ApplicationCreated`` subscribers      -> ``registry.add_startup_hook``, run within the ASGI lifespan
- ``config.add_request_method(reify=True)`` -> ``registry.add_request_method``
- ``pyramid.threadlocal``                 -> ``patzilla.web.context`` (``contextvars``)
- ``pyramid.httpexceptions``              -> ``patzilla.web.exceptions``
- Cornice ``Service`` and error handling  -> ``patzilla.web.service``, ``patzilla.web.errors``
- URL dispatch, views and renderers       -> ``patzilla.web.routing``, ``patzilla.web.render``
- ``pyramid_mako``                        -> ``patzilla.web.render`` (Mako ``TemplateLookup``)
- ``pyramid_beaker``                      -> ``patzilla.boot.cache.configure_cache_regions``
- PasteDeploy, ``pserve``, waitress       -> ``patzilla.web.config``, ``patzilla.web.server`` (uvicorn)
- ``pyramid.paster.bootstrap``            -> ``patzilla.web.app.app_context``
- ``pyramid.testing.DummyRequest``        -> ``patzilla.web.testing.DummyRequest``
"""
