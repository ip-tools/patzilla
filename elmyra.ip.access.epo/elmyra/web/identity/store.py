# -*- coding: utf-8 -*-
# (c) 2014 Andreas Motl, Elmyra UG
import logging
import uuid
import datetime
from pbkdf2 import crypt
from pymongo.mongo_client import MongoClient
from pymongo.uri_parser import parse_uri
from mongoengine import connect as mongoengine_connect, signals
from mongoengine.document import Document
from mongoengine.fields import StringField, ListField, DateTimeField
from mongoengine.errors import NotUniqueError

log = logging.getLogger(__name__)


# ------------------------------------------
#   bootstrapping
# ------------------------------------------
def includeme(config):
    #config.add_subscriber(setup_pymongo, "pyramid.events.NewRequest")
    config.add_subscriber(setup_mongoengine, "pyramid.events.ApplicationCreated")
    config.add_subscriber(provision_users, "pyramid.events.ApplicationCreated")


# ------------------------------------------
#   database connection
# ------------------------------------------
def setup_mongoengine(event):
    registry = event.app.registry
    mongodb_uri = registry.settings.get('mongodb.ipsuite.uri')
    mongodb_database = parse_uri(mongodb_uri)['database']
    mongoengine_connect(mongodb_database, host=mongodb_uri)

# provide lowlevel access to the pymongo connection via ``request.db``
def setup_pymongo(event):
    registry = event.request.registry
    mongodb_uri = registry.settings.get('mongodb.ipsuite.uri')
    mongodb_database = parse_uri(mongodb_uri)['database']
    mongodb_connection = MongoClient(mongodb_uri)
    event.request.db = mongodb_connection[mongodb_database]


# ------------------------------------------
#   data model
# ------------------------------------------
class User(Document):
    userid = StringField(unique=True)
    username = StringField(unique=True)
    password = StringField()
    fullname = StringField()
    created = DateTimeField()
    modified = DateTimeField(default=datetime.datetime.now)
    tags = ListField(StringField(max_length=30))

    @classmethod
    def assign_userid(cls, sender, document, **kwargs):
        if sender is User and not document.userid:
            document.userid = str(uuid.uuid4())

    """
    reg. password hashing
    https://github.com/passy/flask-bcrypt/blob/master/flaskext/bcrypt.py
    https://github.com/maxcountryman/flask-bcrypt/blob/master/flask_bcrypt.py
    https://exyr.org/2011/hashing-passwords/
    https://github.com/SimonSapin/snippets/blob/master/hashing_passwords.py
    https://github.com/mitsuhiko/python-pbkdf2/blob/master/pbkdf2.py
    """

    @classmethod
    def assign_created(cls, sender, document, **kwargs):
        if sender is User and not document.created:
            document.created = datetime.datetime.now()

    @staticmethod
    def crypt500(password):
        return crypt(password, iterations=500)

    @classmethod
    def hash_password(cls, sender, document, **kwargs):
        if sender is User and not document.password.startswith('$p5k2$'):
            document.password = cls.crypt500(document.password)

    def check_password(self, password):
        pwhash = self.password
        return pwhash == crypt(password, pwhash)

signals.post_init.connect(User.assign_userid)
signals.post_init.connect(User.assign_created)
signals.pre_save.connect(User.hash_password)


class UserHistory(Document):
    userid = StringField(unique=True)
    timestamp = DateTimeField(default=datetime.datetime.now)
    action = StringField()


# ------------------------------------------
#   utilities
# ------------------------------------------
def provision_users(event):
    users = [
        User(username = '***REMOVED***', password = '***REMOVED***', fullname = '***REMOVED***', tags = ['elmyra-staff']),
        User(username = '***REMOVED***', password = '***REMOVED***', fullname = 'Andreas Motl', tags = ['elmyra-staff']),
    ]
    for user in users:
        try:
            user.save()
        except NotUniqueError as ex:
            pass
