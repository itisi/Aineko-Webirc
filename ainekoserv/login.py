from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.security import remember
from pyramid.security import forget
from pyramid.renderers import get_renderer
from pyramid.security import authenticated_userid

from colander import MappingSchema, SequenceSchema, SchemaNode #schema
from colander import String, Boolean, Integer #types
from colander import Length, OneOf, Regex, Email, All, Function #validators

from deform import ValidationFailure
from deform import Form
from deform import widget

import re

from sqlalchemy.exc import DBAPIError

from .models import DBSession, User

def site_layout():
    renderer = get_renderer("templates/global_layout.pt")
    layout = renderer.implementation().macros['layout']
    return layout

def forcelogin(request):
    settings = request.registry.settings
    if not 'development_env' in settings or not settings['development_env']:
         return HTTPNotFound('Nope')
    try:
        user = request.GET['user']
    except:
        return HTTPFound('/board')
    headers = remember(request, int(user))
    return HTTPFound('/board', headers = headers)

def login(request):
    login_url = request.route_url('login')
    referrer = request.url
    if referrer == login_url:
        referrer = '/' # never use the login form itself as came_from
    came_from = request.params.get('came_from', referrer)
    message = ''
    login = ''
    password = ''
    if 'form.submitted' in request.params:
        login = request.params['login']
        password = request.params['password']
        user = DBSession.query(User).filter(User.name_insensitive==login).first()
        if user and checkpass(password, user.password):
            try:
                user.socket.username = user.name
            except:
                pass #the user isn't connected to a socket.
            headers = remember(request, user.id)
            return HTTPFound(location = came_from, headers = headers)
        message = 'Failed login'

    return dict(
        content_type='text/xhtml',
        page_title = "Login",
        layout = site_layout(),
        message = message,
        url = request.application_url + '/login',
        came_from = came_from,
        login = login,
        password = password,
        )
    
def logout(request):
    headers = forget(request)
    return HTTPFound(location = request.route_url('home'), headers = headers)

def usercreatable(user):
    if DBSession.query(User).filter(User.name_insensitive==user).first():
        return False
    else:
        return True

class RegisterForm(MappingSchema):
    a = re.compile(r"^[A-Za-z0-9_]*$")
    userv = All(Regex(a, "Usernames may only contain letters, numbers, and underscores."), Function(usercreatable, "That username is unavailable"))
    username = SchemaNode(String(), description = 'Username', validator = userv)
    email = SchemaNode(String(), widget = widget.TextInputWidget(size=40), validator = Email(), description = 'Email address')
    password = SchemaNode(String(), widget = widget.CheckedPasswordWidget(), validator = Length(min=5))

def register(request):
    schema = RegisterForm()
    myform = Form(schema, buttons=('submit',))
    userid = authenticated_userid(request)
    username = False
    if userid:
        user = User.by_id(userid)
        if user:
            username = user.name
    fields = {
            "layout": site_layout(),
            "page_title": "Register",
            "message": "",
            "url": request.application_url + '/register',
            "logged_in": username,
        }
    if username:
        fields['form'] = "You are already logged in.  Please log out and try again."
        return fields
    if 'submit' in request.POST:
        controls = request.POST.items()
        try:
            myform.validate(controls)
        except ValidationFailure, e:
            fields['form'] = e.render()
            return fields
        #passed validation
        user = User()
        settings = Settings()
        DBSession.add(settings)
        user.name = request.POST['username']
        user.email = request.POST['email']
        user.password = makepass(request.POST['password'])
        DBSession.add(user)
        fields['form'] = request.POST['username']
        
        return fields
    fields['form'] = myform.render()
    return fields
