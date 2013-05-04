from pyramid.config import Configurator
from sqlalchemy import engine_from_config
from pyramid_beaker import session_factory_from_settings
from pyramid.authentication import SessionAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy

from .models import (
    DBSession,
    Base,
    )

def groupfinder(userid, request):
    return []
    user = User.by_id(userid, ('groups',))
    if user:
        return [g.groupname for g in user.groups]
    else:
        return None

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine

    authn_policy = SessionAuthenticationPolicy(callback=groupfinder)
    authz_policy = ACLAuthorizationPolicy()

    config = Configurator(settings=settings,
            authentication_policy=authn_policy,
            authorization_policy=authz_policy,
            root_factory='ainekoserv.models.RootFactory',)
    config.include("pyramid_beaker")
    session_factory = session_factory_from_settings(settings)
    config.set_session_factory(session_factory)

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
