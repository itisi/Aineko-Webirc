from .models import DBSession, User
from socketio.namespace import BaseNamespace
from socketio.mixins import BroadcastMixin
from pyramid.security import authenticated_userid
from sqlalchemy.orm import joinedload
import transaction
import traceback


def acl(group):
    """Returns a tuple containing an allowed method set() and a denied method set()"""
    groups = {}
    activeallow = (
            'recv_connect',
            'recv_disconnect',
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
        self.only_me = False
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
        return ('recv_connect', 'recv_disconnect', 'on_test')

