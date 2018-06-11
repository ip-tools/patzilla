# -*- coding: utf-8 -*-
# (c) 2014-2018 Andreas Motl <andreas.motl@ip-tools.org>
import uuid
import arrow
import logging
import datetime
from pbkdf2 import crypt
from pymongo.mongo_client import MongoClient
from pymongo.uri_parser import parse_uri
from mongoengine import connect as mongoengine_connect, signals, IntField, DoesNotExist
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
    mongodb_uri = registry.settings.get('mongodb.patzilla.uri')
    mongodb_database = parse_uri(mongodb_uri)['database']
    try:
        mongoengine_connect(mongodb_database, host=mongodb_uri)
    except Exception as ex:
        log.critical('Failed to connect to MongoDB database at %s. Reason: %s', mongodb_uri, ex)

# provide lowlevel access to the pymongo connection via ``request.db``
def setup_pymongo(event):
    registry = event.request.registry
    mongodb_uri = registry.settings.get('mongodb.patzilla.uri')
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

    phone = StringField(required=False)
    homepage = StringField(required=False)
    company = StringField(required=False)
    organization = StringField(required=False)

    tags = ListField(StringField(max_length=30))
    modules = ListField(StringField(max_length=30))
    upstream_credentials = DictField(required=False)
    billing = DictField(required=False)
    parent = StringField(required=False)

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
        if sender is User and document.password and not document.password.startswith('$p5k2$'):
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

        # mongoengine 0.8.7
        # metrics, created = UserMetrics.objects.get_or_create(userid=userid, date=date)

        # mongoengine 0.13.0
        # http://docs.mongoengine.org/guide/querying.html?highlight=get_or_create#retrieving-unique-results
        try:
            metrics = UserMetrics.objects.get(userid=userid, date=date)
        except DoesNotExist:
            metrics = UserMetrics(userid=userid, date=date)
            metrics.save()

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
            modules  = ['keywords-user', 'family-citations', 'analytics', 'ificlaims', 'depatech', 'sip']),

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


class UserManager:

    @classmethod
    def add_user(cls, **kwargs):
        """
        MongoDB blueprint:
        {
            _id: ObjectId("545b6c81a42dde3b4f2c8524"),
            userid: "9cff5461-1104-43e7-b23d-9261dabf5ced",
            username: "test@example.org",
            password: "$p5k2$1f4$8ViZsq5E$XF9C2/0Qoalds2PytzhCWC1wbw.V5x1c",
            fullname: "Max Mustermann",
            organization: "Example Inc.",
            homepage: "https://example.org/",
            created: ISODate("2014-11-06T13:41:37.934Z"),
            modified: ISODate("2014-11-06T13:41:37.933Z"),
            tags: [
                "trial"
            ],
            modules: [
                "keywords-user",
                "family-citations",
                "analytics"
            ]
        }
        """


        # Build dictionary of proper object attributes from kwargs
        data = {}
        for field in User._fields:
            if field == 'id': continue
            if field in kwargs and kwargs[field] is not None:
                data[field] = kwargs[field]

        # Sanity checks
        required_fields = ['username', 'password', 'fullname']
        for required_field in required_fields:
            if required_field not in data:
                log.error('Option "--{}" required.'.format(required_field))
                return

        # Create user object and store into database
        user = User(**data)
        try:
            user.save()
            return user
        except NotUniqueError:
            log.error('User with username "{}" already exists.'.format(data['username']))
