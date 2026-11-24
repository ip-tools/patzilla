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
from mongoengine.fields import BooleanField, DateTimeField, DictField, ListField, StringField
from mongoengine.errors import NotUniqueError
from pyramid.threadlocal import get_current_request
from zope.interface.interface import Interface
from zope.interface import implementer

log = logging.getLogger(__name__)


def utcnow() -> datetime.datetime:
    """
    Return the current UTC timestamp as a naive datetime compatible with
    MongoEngine / PyMongo while avoiding deprecated `datetime.utcnow()`.
    """
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


def ensure_utc_naive(dt: datetime.datetime) -> datetime.datetime:
    """
    Normalize a datetime to naive UTC for safe comparison with MongoDB values.
    """
    if dt.tzinfo is not None:
        return dt.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    return dt


# ------------------------------------------
#   bootstrapping
# ------------------------------------------
def includeme(config):
    #config.add_subscriber(setup_pymongo, "pyramid.events.NewRequest")
    config.add_subscriber(setup_mongoengine, "pyramid.events.ApplicationCreated")
    config.add_subscriber(provision_users, "pyramid.events.ApplicationCreated")
    # TODO: Is it really needed in "minimal" mode?
    config.registry.registerUtility(UserMetricsManager())


# ------------------------------------------
#   database connection
# ------------------------------------------
def setup_mongoengine(event):
    registry = event.app.registry
    mongodb_uri = registry.settings.get('mongodb.patzilla.uri')
    if mongodb_uri is None:
        log.warning("No user identity database enabled")
        return
    mongodb_database = parse_uri(mongodb_uri)['database']
    try:
        mongoengine_connect(mongodb_database, host=mongodb_uri)
    except Exception:
        log.exception('Failed to connect to MongoDB database at %s', mongodb_uri)

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
    email = StringField(required=False)
    email_verified = BooleanField(default=False)
    email_verified_at = DateTimeField(required=False)
    password = StringField()
    fullname = StringField()

    created = DateTimeField()
    modified = DateTimeField(default=utcnow)
    last_login_at = DateTimeField(required=False)
    status = StringField(default='active')

    phone = StringField(required=False)
    homepage = StringField(required=False)
    company = StringField(required=False)
    organization = StringField(required=False)

    tags = ListField(StringField(max_length=30))
    modules = ListField(StringField(max_length=30))
    upstream_credentials = DictField(required=False)
    billing = DictField(required=False)
    parent = StringField(required=False)

    @property
    def is_active(self) -> bool:
        """
        Return True when the user account is permitted to authenticate.
        Respects both the explicit `status` field and the legacy `login:disabled` tag.
        """
        if self.status and self.status != 'active':
            return False
        if self.tags and 'login:disabled' in self.tags:
            return False
        return True

    @property
    def is_authenticated(self) -> bool:
        """
        Return True for a persisted/identified user rather than an anonymous placeholder.
        """
        return bool(self.userid and (self.username or self.email))

    def to_public_dict(self) -> dict:
        """
        Return a safe dictionary representation suitable for API responses and frontend state.
        Excludes sensitive fields such as `password`, `upstream_credentials`, and `billing`.
        """
        return {
            'userid': self.userid,
            'username': self.username,
            'email': self.email or (self.username if self.username and '@' in self.username else None),
            'email_verified': bool(self.email_verified),
            'fullname': self.fullname or '',
            'status': self.status or 'active',
            'tags': list(self.tags or []),
            'modules': list(self.modules or []),
        }

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
            document.created = utcnow()

    @staticmethod
    def crypt500(password):
        return crypt(password, iterations=500)

    @classmethod
    def hash_password(cls, sender, document, **kwargs):
        if sender is User and document.password and not document.password.startswith('$p5k2$'):
            document.password = cls.crypt500(document.password)

    def check_password(self, password):
        pwhash = self.password
        if not pwhash:
            return False
        return pwhash == crypt(password, pwhash)

signals.post_init.connect(User.assign_userid)
signals.post_init.connect(User.assign_created)
signals.pre_save.connect(User.hash_password)


class MagicLinkToken(Document):
    """
    Single-use, short-lived authentication token sent via email.
    Only the SHA-256 hash of the raw token is persisted.
    """

    meta = {
        'collection': 'magic_link_token',
        'indexes': [
            {'fields': ['expires_at'], 'expireAfterSeconds': 0},
            {'fields': ['email', 'created_at']},
            {'fields': ['request_ip', 'created_at']},
        ],
    }

    token_hash = StringField(required=True, unique=True)
    email = StringField(required=True)
    purpose = StringField(default='login')
    came_from = StringField(required=False)
    created_at = DateTimeField(default=utcnow)
    expires_at = DateTimeField(required=True)
    consumed_at = DateTimeField(required=False)
    request_ip = StringField(required=False)
    user_agent = StringField(required=False)


class UserSession(Document):
    """
    Server-side user session backed by an HttpOnly session cookie.
    Only the SHA-256 hash of the raw session token is persisted so
    sessions can be audited and revoked server-side.
    """

    meta = {
        'collection': 'user_session',
        'indexes': [
            {'fields': ['expires_at'], 'expireAfterSeconds': 0},
            'userid',
        ],
    }

    session_hash = StringField(required=True, unique=True)
    userid = StringField(required=True)
    created_at = DateTimeField(default=utcnow)
    last_seen_at = DateTimeField(default=utcnow)
    expires_at = DateTimeField(required=True)
    revoked_at = DateTimeField(required=False)
    ip_address = StringField(required=False)
    user_agent = StringField(required=False)

    def is_valid(self, now: datetime.datetime | None = None) -> bool:
        """
        Return True if the session has not been revoked and has not expired.
        """
        current = ensure_utc_naive(now) if now is not None else utcnow()
        if self.revoked_at is not None:
            return False
        if self.expires_at is None:
            return False
        return ensure_utc_naive(self.expires_at) > current


class UserHistory(Document):
    userid = StringField()
    timestamp = DateTimeField(default=utcnow)
    action = StringField()


class UserMetrics(Document):
    userid = StringField()
    date = DateTimeField()
    transfer = DictField()


# ------------------------------------------
#   utilities
# ------------------------------------------
class IUserMetricsManager(Interface):  # ty: ignore[unsupported-base]
    pass

@implementer(IUserMetricsManager)
class UserMetricsManager:

# py27    implements(IUserMetricsManager)

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
            metrics = UserMetrics.objects.get(userid=userid, date=date)  # ty: ignore[unresolved-attribute]
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
        for field in User._fields:  # ty: ignore[unresolved-attribute]
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
