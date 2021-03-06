from hashlib import sha512
from sqlalchemy import (
    Column,
    Integer,
    Text,
    func,
    Table,
    ForeignKey,
    Boolean
    )

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relationship,
    )
from pyramid.security import Allow, Everyone
from sqlalchemy.ext.hybrid import Comparator, hybrid_property
from zope.sqlalchemy import ZopeTransactionExtension
import string
import random

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

class AinekoBase():
    @classmethod
    def by_id(cls, rowid, joined = None):
        if joined is not None:
            options = []
            for join in joined:
                options.append(joinedload(join))
            return DBSession.query(cls).options(*options).filter(cls.id == rowid).first()
        else:
            return DBSession.query(cls).filter(cls.id == rowid).first()

    @classmethod
    def by_name(cls, name, joined = None):
        if joined is not None:
            options = []
            for join in joined:
                options.append(joinedload(join))
            return DBSession.query(cls).options(*options).filter(cls.name == name).first()
        else:
            return DBSession.query(cls).filter(cls.name == name).first()



class RootFactory(object):
    __acl__ = [ (Allow, Everyone, 'view'),
                (Allow, 'active', 'active') ]
    storage = dict()
    def __init__(self, request):
        pass

class CaseInsensitiveComparator(Comparator):
    def __eq__(self, other):
        return func.lower(self.__clause_element__()) == func.lower(other)

users_channels_table = Table('users_channels', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('channel_id', Integer, ForeignKey('channels.id')),
)

class User(Base, AinekoBase):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(Text)
    email = Column(Text)
    password = Column(Text)
    channels = relationship(
            'Channel',
            secondary=users_channels_table,
            backref='users')


    @hybrid_property
    def name_insensitive(self):
        return self.user.lower()

    @name_insensitive.comparator
    def name_insensitive(self):
        return CaseInsensitiveComparator(self.name)

    def setpass(self, password):
        salt = "".join([random.choice(string.letters) for x in range(10)])
        self.password = sha512(password + salt).hexdigest() + salt

    def checkpass(self, password):
        phash = self.password[:-10]
        salt = self.password[-10:]
        return sha512(password + salt).hexdigest() == phash

    @classmethod
    def by_username(cls, username):
        return DBSession.query(User).filter(User.name == username).first()

class Channel(Base, AinekoBase):
    __tablename__ = 'channels'
    id = Column(Integer, primary_key=True)
    registered = Column(Boolean)
    name = Column(Text)
    password = Column(Text)
    topic = Column(Text)
    invite_only = Column(Boolean)
    owner_id = Column(Integer, ForeignKey('users.id'))
    owner = relationship(User, backref='owned_channels')

    def simple(self):
        return {
                'id': self.id,
                'name': self.name,
                'topic': self.topic,
                'users': [user.name for user in self.users],
            }
