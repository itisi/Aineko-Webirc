from twisted.internet.protocol import ClientFactory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
from .models import DBSession, Channel
import thread
import json
import transaction

started = False
users = {}
protocol = None
nicks = {}
channels = {}

class webirc(LineReceiver):
    def __init__(self):
        pass

    def connectionMade(self):
        pass

    def connectionLost(self, reason):
        pass
    
    def sendMessage(self, message):
        pass

    def lineReceived(self, line):
        print "Received"
        try:
            line = json.loads(line)
        except ValueError:
            return
        if 'command' in line:
            if hasattr(self, 'on_' + line['command']):
                getattr(self,'on_' + line['command'])(line)
    def on_privmsg(self, line):
        channel = Channel.by_name(line['channel'])
        if not channel:
            channel = Channel()
            channel.name = channelname
            DBSession.add(channel)
            DBSession.flush()
        senduser(1, 'privmsg', channel.id, line['nick'], line['message'])
        transaction.commit()
        transaction.begin()
    def on_initvars(self, line):
        global channels, nicks
        channels = line['channels']
        nicks = line['nicks']
        remchannels = [name for name in channels]
        dbchannels = DBSession.query(Channel).filter(Channel.name.in_(remchannels))
        for channel in dbchannels:
            channel.topic = channels[channel.name]['topic']
            DBSession.add(channel)
            remchannels.remove(channel.name)
        for channelname in remchannels:
            channel = Channel()
            channel.topic = channels[channelname]['topic']
            channel.name = channelname
            DBSession.add(channel)
        transaction.commit()
        transaction.begin()

class webircFactory(ClientFactory):
    def __init__(self):
        pass

    def buildProtocol(self, addr):
        global protocol
        protocol = webirc()
        return protocol

def adduser(user):
    global users
    if (user.id in users):
        users[user.id].append(user)
    else:
        users[user.id] = [user]

def senduser(userid, *args):
    print 'sent', args
    if userid in users:
        for user in users[userid]:
            user.emit(*args)

def sendmessage(message):
    reactor.callFromThread(protocol.sendLine, json.dumps(message))

reactor.connectTCP('localhost', 9001, webircFactory())
thread.start_new_thread(reactor.run, (), {'installSignalHandlers': 0})
