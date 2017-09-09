# -*- coding: utf-8 -*-
# (c) 2014 Andreas Motl, Elmyra UG
import logging
import uuid
import datetime
import arrow
from pbkdf2 import crypt
from pymongo.mongo_client import MongoClient
from pymongo.uri_parser import parse_uri
from mongoengine import connect as mongoengine_connect, signals, IntField
from mongoengine.document import Document
from mongoengine.fields import StringField, ListField, DateTimeField, DictField
from mongoengine.errors import NotUniqueError
from pyramid.threadlocal import get_current_request
from zope.interface.declarations import implements
from zope.interface.interface import Interface

log = logging.getLogger(__name__)


# ------------------------------------------
#   bootstrapping
# ------------------------------------------
def includeme(config):
    #config.add_subscriber(setup_pymongo, "pyramid.events.NewRequest")
    config.add_subscriber(setup_mongoengine, "pyramid.events.ApplicationCreated")
    config.add_subscriber(provision_users, "pyramid.events.ApplicationCreated")
    config.registry.registerUtility(UserMetricsManager())


# ------------------------------------------
#   database connection
# ------------------------------------------
def setup_mongoengine(event):
    registry = event.app.registry
    mongodb_uri = registry.settings.get('mongodb.ipsuite.uri')
    mongodb_database = parse_uri(mongodb_uri)['database']
    try:
        mongoengine_connect(mongodb_database, host=mongodb_uri)
    except Exception as ex:
        log.critical('Failed to connect to MongoDB database at %s. Reason: %s', mongodb_uri, ex)

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
    modules = ListField(StringField(max_length=30))
    upstream_credentials = DictField()

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
    userid = StringField()
    timestamp = DateTimeField(default=datetime.datetime.now)
    action = StringField()


class UserMetrics(Document):
    userid = StringField()
    date = DateTimeField()
    transfer = DictField()


# ------------------------------------------
#   utilities
# ------------------------------------------
class IUserMetricsManager(Interface):
    pass

class UserMetricsManager(object):

    implements(IUserMetricsManager)

    def measure_upstream(self, upstream, volume):

        # measure per-user
        request = get_current_request()
        if not hasattr(request, 'user'):
            return

        userid = request.user and request.user.userid or None

        log.debug('Measure transfer: userid={0}, upstream={1}, volume={2}'.format(userid, upstream, volume))
        date = arrow.utcnow().format('YYYY-MM-DD')
        metrics, created = UserMetrics.objects.get_or_create(userid=userid, date=date)
        metrics.transfer.setdefault(upstream, {'total_response_size': 0, 'message_count': 0})
        metrics.transfer[upstream]['total_response_size'] += volume
        metrics.transfer[upstream]['message_count'] += 1
        metrics.save()


# ------------------------------------------
#   provisioning
# ------------------------------------------
def provision_users(event):

    # Disabled as of 2017-08-09.
    # Enable temporarily again to create "admin" user on daemon start. YMMV.
    return

    users = [

        User(
            fullname = 'Administrator',
            username = 'admin',
            password = 'admin',
            tags     = ['staff'],
            modules  = ['keywords-user', 'family-citations', 'analytics', 'ifi', 'depatech']),

        """
        User(
            username = 'test@example.com',
            password = 'test',
            fullname = 'Markus Tester',
            tags = ['']
        ),
        """
    ]
    for user in users:
        try:
            if type(user) is User:
                user.save()
        except NotUniqueError as ex:
            pass
