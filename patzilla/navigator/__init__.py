# -*- coding: utf-8 -*-
# (c) 2013-2026 Andreas Motl <andreas.motl@ip-tools.org>
import os

from patzilla.web.routing import RouteTable


def setup(registry):

    # Register application components: URL generator, renderer globals
    registry.include("patzilla.navigator.opaquelinks")
    registry.include("patzilla.navigator.subscribers")

    # Views and routes
    from patzilla.navigator.views import (
        TEMPLATE_MAGIC_LINK_VERIFY, TEMPLATE_PORTFOLIO_DEMO,
        auth_magic_verify, logout_view, navigator_routes, portfolio,
    )
    registry.add_routes(navigator_routes(prefix='/navigator'))
    registry.add_static_view('static', os.path.join(os.path.dirname(__file__), 'static'), cache_max_age=0)

    routes = RouteTable()
    routes.add('home', '/')
    routes.add('auth-magic-verify-root', '/auth/magic/verify', auth_magic_verify, renderer=TEMPLATE_MAGIC_LINK_VERIFY)
    routes.add('logout-root', '/logout', logout_view)
    routes.add('portfolio-demo', '/portfolio-demo', portfolio, renderer=TEMPLATE_PORTFOLIO_DEMO)
    registry.add_routes(routes)
