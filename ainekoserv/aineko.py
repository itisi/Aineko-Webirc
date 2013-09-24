from .models import DBSession, User, Channel
from socketio.namespace import BaseNamespace
from socketio.mixins import BroadcastMixin
from pyramid.security import authenticated_userid
from sqlalchemy.orm import joinedload
import transaction
import traceback
import string
import communication

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
    
    def joinChannelsByName(self, names):
        if len(names) > 1:
            channels = DBSession.query(Channel).filter(Channel.name.in_(names)).all()
        elif len(names) == 1:
            channels = DBSession.query(Channel).filter(Channel.name == names[0]).all()
        else:
            channels = []
        channels = {channel.name: channel for channel in channels}
        flush = False
        for name in names:
            if name not in channels:
                flush = True
                channel = Channel()
                channel.name = name
                channels[name] = channel
        if flush:
            DBSession.flush()
        for channel in channels:
            channel = channels[channel]
            if not channel.id in self.storage['channel']:
                self.storage['channel'][channel.id] = set()
            self.storage['channel'][channel.id].add(self)
            self.emit('join', self.name, channel.simple())
            communication.sendmessage({'command': 'join', 'channel': channel.name, 'user': self.name})
        

    def recv_connect(self):
        print communication.nicks, communication.channels
        self.emit('servermessage', 'You are now connected.')
        userid = authenticated_userid(self.request)
        user = User.by_id(userid)
        if user:
            self.name = user.name
            self.id = user.id
            communication.adduser(self)
        else:
            self.emit('servermessage', 'You are not logged in.')
            return
        initvars = {
                    'meid': user.id,
                    'name': user.name,
                }
        self.emit('initvars', initvars)
        if (self.name in communication.nicks):
            if 'channels' in communication.nicks[self.name]:
                self.joinChannelsByName(communication.nicks[self.name]['channels'])
            else:
                communication.nicks[self.name]['channels'] = [];
        else:
            communication.nicks[self.name] = {'channels': []}
        self.storage['user'][userid] = self

    def on_join(self, channelname):
        if len(channelname) < 2 or channelname[0] != '#':
            return self.emit('errormessage', 'Invalid channel format. Channels must be at least 2 characters in length and begin with #.')
        pos = 0
        for char in channelname:
            if char not in string.letters + string.digits + '#' or (pos == 0 and char != '#') or (char == '#' and pos != 0):
                return self.emit('errormessage', 'Invalid channel name. Channels may only contain letters.')
            pos += 1
        self.joinChannelsByName([channelname])
        communication.sendmessage({'command': 'join', 'channel': channelname, 'user': self.name})

    def on_privmsg(self, channelid, message):
        channel = Channel.by_id(channelid)
        user = User.by_id(self.id)
        self.emitChannel(channelid, 'privmsg', channel.id, user.name, message)
        communication.sendmessage({'command': 'privmsg', 'channel': channel.name, 'user': user.name, 'message': message})
