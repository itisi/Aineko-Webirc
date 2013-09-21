from .models import DBSession, User, Channel
from socketio.namespace import BaseNamespace
from socketio.mixins import BroadcastMixin
from pyramid.security import authenticated_userid
from sqlalchemy.orm import joinedload
import transaction
import traceback
import string

def acl(group):
    """Returns a tuple containing an allowed method set() and a denied method set()"""
    groups = {}
    activeallow = (
            'recv_connect',
            'recv_disconnect',
            'on_join',
        )
    groups["active"] = (set(activeallow), set())
    if not group in groups:
        return (set(), set())
    else:
        return groups[group]

def useracl(userid):
    user = User.by_id(userid, ('groups',))
    if not user:
        return []
    else:
        allowed = set()
        denied = set()
        for group in user.groups:
            allow, deny = acl(group.groupname)
            allowed |= allow
            denied |= deny
        return allowed - denied

class ChatNamespace(BaseNamespace, BroadcastMixin):
    def __init__(self, *args, **kwargs):
        BaseNamespace.__init__(self, *args, **kwargs)
        BroadcastMixin.__init__(self)
        try:
            self.storage = self.request.root.storage
        except:
            self.request.root.storage = {}
            self.storage = self.request.root.storage
        for var in ['user', 'channel']:
            if not var in self.storage:
                self.storage[var] = {}

    def call_method(self, method_name, packet, *args):
        try:
            return super(ChatNamespace, self).call_method(method_name, packet, *args)
        except:
            transaction.abort()
            traceback.print_exc()
        finally:
            transaction.commit()

    def call_method_with_acl(self, method_name, packet, *args):
        if not self.is_method_allowed(method_name):
            self.error('method_access_denied', method_name)
            return
        return self.call_method(method_name, packet, *args)

    def get_initial_acl(self):
        #self.user = authenticated_userid(self.request)
        #if not self.user:
        #    return []
        #else:
        #    return useracl(self.user)
        return ('recv_connect', 'recv_disconnect', 'on_test', 'on_join', 'on_privmsg')

    def emitChannel(self, channel, *args, **kwargs):
        if channel in self.storage['channel']:
            for user in self.storage['channel'][channel]:
                user.emit(*args, **kwargs)

    def recv_connect(self):
        self.emit('servermessage', 'You are now connected.')
        userid = authenticated_userid(self.request)
        user = User.by_id(userid)
        if user:
            self.name = user.name
            self.id = user.id
        else:
            self.emit('servermessage', 'You are not logged in.')
            return
        initvars = {
                    'meid': user.id,
                    'name': user.name,
                }
        self.emit('initvars', initvars)
        self.storage['user'][userid] = self

    def on_join(self, channelname):
        if len(channelname) < 2 or channelname[0] != '#':
            return self.emit('errormessage', 'Invalid channel format. Channels must be at least 2 characters in length and begin with #.')
        pos = 0
        for char in channelname[1:]:
            if char not in string.letters and (pos != 0 and char != '#'):
                return self.emit('errormessage', 'Invalid channel name. Channels may only contain letters.')
            pos += 1
        user = User.by_id(self.id)
        channelname = channelname.lower()
        channel = Channel.by_name(channelname)
        if not channel:
            channel = Channel()
            channel.name = channelname
            DBSession.add(channel)
            DBSession.flush()
        if not user in channel.users:
            channel.users.append(user)
            DBSession.add(user)
        if not channel.id in self.storage['channel']:
            self.storage['channel'][channel.id] = set()
        self.storage['channel'][channel.id].add(self)
        self.emit('join', user.name, channel.simple())

    def on_privmsg(self, channelid, message):
        channel = Channel.by_id(channelid)
        user = User.by_id(self.id)
        self.emitChannel(channelid, 'privmsg', channel.id, user.name, message)
