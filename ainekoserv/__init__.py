from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from .models import (
    DBSession,
    Base,
    )


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    config = Configurator(settings=settings)
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.scan()
    config.add_route('index', '/')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('forcelogin', '/forcelogin')
    config.add_route('register', '/register')
    config.add_route('client', '/client')

    config.add_route('socket_io', 'socket.io/*remaining')

    #ainekoserv:templates/empty.pt
    config.add_view('ainekoserv.views.socketio_service',
            route_name='socket_io',
            renderer="json"
    )
    config.add_view('ainekoserv.login.login',
            route_name='login',
            renderer='ainekoserv:templates/login.pt',
        )
    config.add_view('ainekoserv.login.logout', route_name='logout')
    config.add_view('ainekoserv.login.forcelogin', route_name='forcelogin')
    config.add_view('ainekoserv.login.register',
            route_name='register',
            renderer="templates/register.pt",
        )
    return config.make_wsgi_app()
