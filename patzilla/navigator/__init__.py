# -*- coding: utf-8 -*-
# (c) 2013-2017 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
def includeme(config):

    # Register application components: URL generator, renderer globals
    config.include("patzilla.navigator.opaquelinks")
    config.include("patzilla.navigator.subscribers")
    config.include("patzilla.navigator.views", route_prefix='/navigator')

    # Views and routes
    config.add_static_view('static', 'static', cache_max_age=3600)
    #config.add_static_view('static', 'static', cache_max_age=0)
    config.add_route('home', '/')

    config.scan()
