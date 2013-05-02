from hashlib import sha512
from sqlalchemy import (
    Column,
    Integer,
    Text,
    )

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    )

from zope.sqlalchemy import ZopeTransactionExtension
import string
import random

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(Text)
    email = Column(Text)
    password = Column(Text)

    def setpass(password):
        salt = "".join([random.choice(string.letters) for x in range(10)])
        self.password = sha512(password + salt).hexdigest() + salt

    def checkpass(password):
        phash = self.password[:-10]
        salt = self.password[-10:]
        return sha512(password + salt).hexdigest() == phash
