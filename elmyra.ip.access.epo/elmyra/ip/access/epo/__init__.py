from pyramid.config import Configurator

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)

    # Addons
    config.include('pyramid_mako')
    config.include('pyramid_fanstatic')

    # Configure subscribers: URL generator, renderer globals.
    config.include(".subscribers")
    #config.include("akhet.static")

    # Views and routes
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('ops-chooser', '/ops-chooser')

    config.scan()

    return config.make_wsgi_app()
