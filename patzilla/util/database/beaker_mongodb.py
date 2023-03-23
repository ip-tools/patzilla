#
# * Beaker plugin for MongoDB support
#
# Brendan W. McAdams <bwmcadams@gmail.com>
# Ryan Bourgeois <bluedragonx@gmail.com>
#
# https://github.com/bwmcadams/mongodb_beaker
# https://pypi.python.org/pypi/mongodb_beaker
#
"""
==============
beaker_mongodb
==============
MongoDB_. backend for Beaker_.'s caching / session system.

Based upon Beaker_.'s ext:memcache code.

This is implemented in a dont-assume-its-there manner.
It uses the beaker namespace as the mongodb row's _id, with everything
in that namespace ( e.g. a session or cache namespace) stored as a full
document.  Each key/value is part of that compound document, using upserts
for performance.

I will probably add a toggleable option for using subcollections, as in
certain cases such as caching mako templates, this may be desirable /
preferred performance wise.

Right now, this is primarily optimized for usage with beaker sessions,
although I need to look at tweaking beaker session itself as having it
store in individual keys rather than everything in a 'session' key may
be desirable for pruning/management/querying.

I have not tackled expiration yet, so you may want to hold off using this
if you need it.  It will be in the next update, but limits usefulness
primarily to sessions right now. (I'll tack a cleanup script in later
as well).

Due to the use of upserts, no check-insert is required, but it will overwrite
previous values which should be expected behavior while caching.
Safe is NOT invoked, so failure will be quiet.
TODO - Safe as overridable config option?

Note that, unless you disable_. it, the beaker_mongodb container will
use pickle (tries loading cpickle first, falls back on pickle) to
serialize/deserialize data to MongoDB_.

.. _Beaker: http://beaker.groovie.org
.. _MongoDB: http://mongodb.org


Beaker should maintain thread safety on connections internally and so I am
relying upon that rather than setting up threadlocal, etc.  If this assumption
is wrong or you run into issues, please let me know.

Configuration
=============

To set this up in your own project so that beaker can find it, it must
define a setuptools entry point in your setup.py file.  If you install
from the egg distribution, beaker_mongodb's setup.py SHOULD create a
beaker.backend entry point.  If you need to tweak it/see how it's done
or it just doesn't work and you need to define your own,
mine looks like this::

    >>> entry_points=\"\"\"
    ... [beaker.backends]
    ... mongodb = beaker_mongodb:MongoDBNamespaceManager
    ... \"\"\",


With this defined, beaker should automatically find the entry point at startup
(Beaker 1.4 and higher support custom entry points) and load it as an optional
backend called 'mongodb'. There are several ways to configure Beaker, I only
cover ini file (such as with Pylons) here.  There are more configuration
options and details in the Beaker configuration docs [1]_.

.. [1] Beaker's configuration documentation -
        http://beaker.groovie.org/configuration.htm

I have a few cache regions in one of my applications, some of which are memcache and some are on mongodb.  The region config looks like this::

    >>> # new style cache settings
    ... beaker.cache.regions = comic_archives, navigation
    ... beaker.cache.comic_archives.type = libmemcached
    ... beaker.cache.comic_archives.url = 127.0.0.1:11211
    ... beaker.cache.comic_archives.expire = 604800
    ... beaker.cache.navigation.type = mongodb
    ... beaker.cache.navigation.url = mongodb://localhost:27017/beaker.navigation
    ... beaker.cache.navigation.expire = 86400

The Beaker docs[1] contain detailed information on configuring regions.  The
item we're interested in here is the **beaker.cache.navigation** keys.  Each
beaker cache definition needs a *type* field, which defines which backend to
use.  Specifying mongodb will (if the module is properly installed) tell
Beaker to cache via mongodb.  Note that if Beaker cannot load the extension,
it will tell you that mongodb is an invalid backend.

Expiration is standard beaker syntax, although not supported at the moment in
this backend.

Finally, you need to define a URL to connect to MongoDB.  This follows the standardized
MongoDB URI Format[3]_. Currently the only options supported is 'slaveOK'.
For backwards compatibility with old versions of beaker_mongodb, separating
database and collection with a '#' instead of '.' is supported, but deprecated.
The syntax is mongodb://<hostname>[:port]/<database>.<collection>

You must define a collection for MongoDB to store data in, in addition to a database.

If you want to use MongoDB's optional authentication support, that is also supported.  Simply define your URL as such::

    >>> beaker.cache.navigation.url = mongodb://bwmcadams@passW0Rd?@localhost:27017/beaker.navigation

The beaker_mongodb backend will attempt to authenticate with the username and
password.  You must configure MongoDB's optional authentication support[2]_ for
this to work (By default MongoDB doesn't use authentication).

.. [2] MongoDB Authentication Documentation: http://www.mongodb.org/display/DOCS/Security+and+Authentication
.. [3] MongoDB URI Format: http://www.mongodb.org/display/DOCS/Connections


Reading from Secondaries (SlaveOK)
==================================

If you'd like to enable reading from secondaries (SlaveOK), you can add that to your URL::

    >>> beaker.cache.navigation.url = mongodb://bwmcadams@passW0Rd?@localhost:27017/beaker.navigation?slaveok=true


Using Beaker Sessions and disabling pickling
=============================================

.. _disable:

If you want to save some CPU cycles and can guarantee that what you're
passing in is either "mongo-safe" and doesn't need pickling, or you know
it's already pickled (such as while using beaker sessions), you can set an
extra beaker config flag of skip_pickle=True.  ``.. admonition:: To make that
perfectly clear, Beaker sessions are ALREADY PASSED IN pickled, so you want to
configure it to skip_pickle.`` It shouldn't hurt anything to double-pickle,
but you will certainly waste precious CPU cycles.  And wasting CPU cycles is
kind of counterproductive in a caching system.

My pylons application configuration for beaker_mongodb has the
following session_configuration::

    >>> beaker.session.type = mongodb
    ... beaker.session.url = mongodb://localhost:27017/beaker.sessions
    ... beaker.session.skip_pickle = True

Depending on your individual needs, you may also wish to create a
capped collection for your caching (e.g. memcache-like only most recently used storage)

See the MongoDB CappedCollection_. docs for details.

.. _CappedCollection: http://www.mongodb.org/display/DOCS/Capped+Collections

Sparse Collection Support
=========================

The default behavior of beaker_mongodb is to create a single MongoDB Document for each namespace, and store each
cache key/value on that document.  In this case, the "_id" of the document will be the namespace, and each new cache entry
will be attached to that document.

This approach works well in many cases and makes it very easy for Mongo to efficiently manage your cache.  However, in other cases
you may wish to change behavior.  This may be for efficiency reasons, or because you're worried about documents getting too large.

In this case, you can enable a "sparse collection" mode, where beaker_mongodb will create a document for EACH key in the namespace.
When sparse collections are enabled, the "_id" of a document is a compound document containing the namespace and the key::

   { "_id" : { "namespace" : "testcache", "key" : "value" } }

The cache data for that key will be stored in a document field 'data'.  You can enable sparse collections in your config with the
'sparse_collections' variable::

    >>> beaker.session.type = mongodb
    ... beaker.session.url = mongodb://localhost:27017/beaker.sessions
    ... beaker.session.sparse_collections = True

Note for Users of Previous Releases
====================================

For bug fix and feature reasons, MongoDB Beaker 0.5+ are not compatible with caches created by previous releases.
Because this is cache data, it shouldn't be a big deal.  We recommend dropping or flushing your entire cache collection(s)
before upgrading to 0.5+ and be aware that it will generate new caches.


A part of this code is a copy of https://raw.githubusercontent.com/bbangert/beaker/master/beaker/ext/mongodb.py 2023-03-22
"""


import datetime
import os
import threading
import time
import pickle

try:
    import pymongo
    import pymongo.errors
    import bson
except ImportError:
    pymongo = None
    bson = None

from beaker.container import NamespaceManager
from beaker.synchronization import SynchronizerImpl
from beaker.util import SyncDict, machine_identifier
from beaker.crypto.util import sha1
from beaker._compat import string_type, PY2


class MongoNamespaceManager(NamespaceManager):
    """Provides the :class:`.NamespaceManager` API over MongoDB.

    Provided ``url`` can be both a mongodb connection string or
    an already existing MongoClient instance.

    The data will be stored into ``beaker_cache`` collection of the
    *default database*, so make sure your connection string or
    MongoClient point to a default database.
    """
    MAX_KEY_LENGTH = 1024

    clients = SyncDict()

    def __init__(self, namespace, url, **kw):
        super(MongoNamespaceManager, self).__init__(namespace)
        self.lock_dir = None  # MongoDB uses mongo itself for locking.

        if pymongo is None:
            raise RuntimeError('pymongo3 is not available')

        if isinstance(url, string_type):
            self.client = MongoNamespaceManager.clients.get(url, pymongo.MongoClient, url)
        else:
            self.client = url
        self.db = self.client.get_default_database()

    def _format_key(self, key):
        if not isinstance(key, str):
            key = key.decode('ascii')
        if len(key) > (self.MAX_KEY_LENGTH - len(self.namespace) - 1):
            if not PY2:
                key = key.encode('utf-8')
            key = sha1(key).hexdigest()
        return '%s:%s' % (self.namespace, key)

    def get_creation_lock(self, key):
        return MongoSynchronizer(self._format_key(key), self.client)

    def __getitem__(self, key):
        self._clear_expired()
        entry = self.db.backer_cache.find_one({'_id': self._format_key(key)})
        if entry is None:
            raise KeyError(key)
        return pickle.loads(entry['value'])

    def __contains__(self, key):
        self._clear_expired()
        entry = self.db.backer_cache.find_one({'_id': self._format_key(key)})
        return entry is not None

    def has_key(self, key):
        return key in self

    def set_value(self, key, value, expiretime=None):
        self._clear_expired()

        expiration = None
        if expiretime is not None:
            expiration = time.time() + expiretime

        value = pickle.dumps(value)
        self.db.backer_cache.update_one({'_id': self._format_key(key)},
                                        {'$set': {'value': bson.Binary(value),
                                                  'expiration': expiration}},
                                        upsert=True)

    def __setitem__(self, key, value):
        self.set_value(key, value)

    def __delitem__(self, key):
        self._clear_expired()
        self.db.backer_cache.delete_many({'_id': self._format_key(key)})

    def do_remove(self):
        self.db.backer_cache.delete_many({'_id': {'$regex': '^%s' % self.namespace}})

    def keys(self):
        return [e['key'].split(':', 1)[-1] for e in self.db.backer_cache.find_all(
            {'_id': {'$regex': '^%s' % self.namespace}}
        )]

    def _clear_expired(self):
        now = time.time()
        self.db.backer_cache.delete_many({'_id': {'$regex': '^%s' % self.namespace},
                                          'expiration': {'$ne': None, '$lte': now}})


class MongoSynchronizer(SynchronizerImpl):
    """Provides a Writer/Reader lock based on MongoDB.

    Provided ``url`` can be both a mongodb connection string or
    an already existing MongoClient instance.

    The data will be stored into ``beaker_locks`` collection of the
    *default database*, so make sure your connection string or
    MongoClient point to a default database.

    Locks are identified by local machine, PID and threadid, so
    are suitable for use in both local and distributed environments.
    """
    # If a cache entry generation function can take a lot,
    # but 15 minutes is more than a reasonable time.
    LOCK_EXPIRATION = 900
    MACHINE_ID = machine_identifier()

    def __init__(self, identifier, url):
        super(MongoSynchronizer, self).__init__()
        self.identifier = identifier
        if isinstance(url, string_type):
            self.client = MongoNamespaceManager.clients.get(url, pymongo.MongoClient, url)
        else:
            self.client = url
        self.db = self.client.get_default_database()

    def _clear_expired_locks(self):
        now = datetime.datetime.utcnow()
        expired = now - datetime.timedelta(seconds=self.LOCK_EXPIRATION)
        self.db.beaker_locks.delete_many({'_id': self.identifier, 'timestamp': {'$lte': expired}})
        return now

    def _get_owner_id(self):
        return '%s-%s-%s' % (self.MACHINE_ID, os.getpid(), threading.current_thread().ident)

    def do_release_read_lock(self):
        owner_id = self._get_owner_id()
        self.db.beaker_locks.update_one({'_id': self.identifier, 'readers': owner_id},
                                        {'$pull': {'readers': owner_id}})

    def do_acquire_read_lock(self, wait):
        now = self._clear_expired_locks()
        owner_id = self._get_owner_id()
        while True:
            try:
                self.db.beaker_locks.update_one({'_id': self.identifier, 'owner': None},
                                                {'$set': {'timestamp': now},
                                                 '$push': {'readers': owner_id}},
                                                upsert=True)
                return True
            except pymongo.errors.DuplicateKeyError:
                if not wait:
                    return False
                time.sleep(0.2)

    def do_release_write_lock(self):
        self.db.beaker_locks.delete_one({'_id': self.identifier, 'owner': self._get_owner_id()})

    def do_acquire_write_lock(self, wait):
        now = self._clear_expired_locks()
        owner_id = self._get_owner_id()
        while True:
            try:
                self.db.beaker_locks.update_one({'_id': self.identifier, 'owner': None,
                                                 'readers': []},
                                                {'$set': {'owner': owner_id,
                                                          'timestamp': now}},
                                                upsert=True)
                return True
            except pymongo.errors.DuplicateKeyError:
                if not wait:
                    return False
                time.sleep(0.2)


def _partition(source, sub):
    """Our own string partitioning method.

    Splits `source` on `sub`.
    """
    i = source.find(sub)
    if i == -1:
        return (source, None)
    return (source[:i], source[i + len(sub):])


def _str_to_node(string, default_port=27017):
    """Convert a string to a node tuple.

    "localhost:27017" -> ("localhost", 27017)
    """
    (host, port) = _partition(string, ":")
    if port:
        port = int(port)
    else:
        port = default_port
    return (host, port)


def _parse_uri(uri, default_port=27017):
    """MongoDB URI parser.
    """

    if uri.startswith("mongodb://"):
        uri = uri[len("mongodb://"):]
    elif "://" in uri:
        raise InvalidURI("Invalid uri scheme: %s" % _partition(uri, "://")[0])

    (hosts, namespace) = _partition(uri, "/")

    raw_options = None
    if namespace:
        (namespace, raw_options) = _partition(namespace, "?")
        if '.' not in namespace and '#' not in namespace:
            db = namespace
            collection = None
        else:
            if '#' in namespace:
                (db, collection) = namespace.split("#", 1)
            else:
                (db, collection) = namespace.split(".", 1)
    else:
        db = None
        collection = None

    username = None
    password = None
    if "@" in hosts:
        (auth, hosts) = _partition(hosts, "@")

        if ":" not in auth:
            raise InvalidURI("auth must be specified as "
                             "'username:password@'")
        (username, password) = _partition(auth, ":")

    host_list = []
    for host in hosts.split(","):
        if not host:
            raise InvalidURI("empty host (or extra comma in host list)")
        host_list.append(_str_to_node(host, default_port))

    options = {}
    if raw_options:
        and_idx = raw_options.find("&")
        semi_idx = raw_options.find(";")
        if and_idx >= 0 and semi_idx >= 0:
            raise InvalidURI("Cannot mix & and ; for option separators.")
        elif and_idx >= 0:
            options = dict([kv.split("=") for kv in raw_options.split("&")])
        elif semi_idx >= 0:
            options = dict([kv.split("=") for kv in raw_options.split(";")])
        elif raw_options.find("="):
            options = dict([raw_options.split("=")])


    return (host_list, db, username, password, collection, options)

def _depickle(value):
    try:
        return pickle.loads(value)
    except Exception as e:
        log.exception("Failed to unpickle value '{0}'.".format(e))
        return None
