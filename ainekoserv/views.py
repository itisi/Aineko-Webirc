from pyramid.response import Response
from pyramid.view import view_config
from pyramid.renderers import get_renderer

from sqlalchemy.exc import DBAPIError

from socketio import socketio_manage

from aineko import ChatNamespace

from .models import (
    DBSession,
    )

def site_layout():
    renderer = get_renderer("templates/global_layout.pt")
    layout = renderer.implementation().macros['layout']
    return layout

@view_config(route_name='index', renderer='templates/index.pt')
def index_view(request):
    return {
            'layout': site_layout(),
            'page_title': 'Home',
            'logged_in': False
        }

@view_config(route_name='client', renderer='templates/client.pt')
def client(request):
    return {
            'layout': site_layout(),
            'page_title': 'Client',
        }

@view_config(route_name='error', renderer='templates/index.pt')
def error(request):
    1/0

def socketio_service(request):
    retval = socketio_manage(request.environ,
        {  
            '/aineko_serv': ChatNamespace,
        }, request=request
    )
    if 'socketio' in request.environ:
        return retval
    else:
        return {}
