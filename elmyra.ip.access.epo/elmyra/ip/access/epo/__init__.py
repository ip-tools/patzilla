from elmyra.ip.access.epo.util import PngRenderer
from pyramid.config import Configurator

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)

    # Addons
    config.include('pyramid_mako')
    config.include('pyramid_fanstatic')
    config.include('cornice')

    # Configure subscribers: URL generator, renderer globals.
    config.include(".subscribers")
    config.include(".views")
    #config.include("akhet.static")

    config.add_renderer('png', PngRenderer)

    # Views and routes
    #config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_static_view('static', 'static', cache_max_age=0)
    config.add_route('home', '/')

    config.scan()

    return config.make_wsgi_app()
