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



"""


import logging
from beaker.container import NamespaceManager, Container
from beaker.exceptions import InvalidCacheBackendError, MissingCacheParameter
from beaker.synchronization import null_synchronizer
from beaker.util import verify_directory, SyncDict

from StringIO import StringIO
try:
    import cPickle as pickle
except ImportError:
    import pickle

try:
    from pymongo.connection import Connection
    import bson
    import bson.errors
except ImportError:
    raise InvalidCacheBackendError("Unable to load the pymongo driver.")

log = logging.getLogger(__name__)
#log.setLevel(logging.DEBUG)

class MongoDBNamespaceManager(NamespaceManager):
    clients = SyncDict()
    _pickle = True
    _sparse = False

    # TODO _- support write concern / safe
    def __init__(self, namespace, url=None, data_dir=None, skip_pickle=False,
                 sparse_collection=False, **params):
        NamespaceManager.__init__(self, namespace)

        if not url:
            raise MissingCacheParameter("MongoDB url is required")

        if skip_pickle:
            log.info("Disabling pickling for namespace: %s" % self.namespace)
            self._pickle = False

        if sparse_collection:
            log.info("Separating data to one row per key (sparse collection) for ns %s ." % self.namespace)
            self._sparse = True

        # Temporarily uses a local copy of the functions until pymongo upgrades to new parser code
        (host_list, database, username, password, collection, options) = _parse_uri(url)

        if database and host_list:
            data_key = "mongodb:%s" % (database)
        else:
            raise MissingCacheParameter("Invalid Cache URL.  Cannot parse.")

        def _create_mongo_conn():
            host_uri = 'mongodb://'
            for x in host_list:
                host_uri += '%s:%s' % x
            log.info("Host URI: %s" % host_uri)
            conn = Connection(host_uri, slave_okay=options.get('slaveok', False))

            db = conn[database]

            if username:
                log.info("Attempting to authenticate %s/%s " % (username, password))
                if not db.authenticate(username, password):
                    raise InvalidCacheBackendError('Cannot authenticate to '
                                                   ' MongoDB.')
            return db[collection]

        self.mongo = MongoDBNamespaceManager.clients.get(data_key,
            _create_mongo_conn)

    def get_creation_lock(self, key):
        """@TODO - stop hitting filesystem for this...
        I think mongo can properly avoid dog piling for us.
        """
        return null_synchronizer()

    def do_remove(self):
        """Clears the entire filesystem (drops the collection)"""
        log.debug("[MongoDB] Remove namespace: %s" % self.namespace)
        q = {}
        if self._sparse:
            q = {'_id.namespace': self.namespace}
        else:
            q = {'_id': self.namespace}

        log.debug("[MongoDB] Remove Query: %s" % q)
        self.mongo.remove(q)


    def __getitem__(self, key):
        log.debug("[MongoDB %s] Get Key: %s" % (self.mongo,
                                                key))

        _id = {}
        fields = {}
        if self._sparse:
            _id = {
                'namespace': self.namespace,
                'key': key
            }
            fields['data'] = True
        else:
            _id = self.namespace
            fields['data.' + key] = True

        log.debug("[MongoDB] Get Query: id == %s Fields: %s", _id, fields)
        result = self.mongo.find_one({'_id': _id}, fields=fields)
        log.debug("[MongoDB] Get Result: %s", result)

        if result:
            """Running into instances in which mongo is returning
            -1, which causes an error as __len__ should return 0
            or positive integers, hence the check of size explicit"""
            log.debug("Result: %s", result)
            data = result.get('data', None)
            log.debug("Data: %s", data)
            if self._sparse:
                value = data
            else:
                value = data.get(key, None)

            if not value:
                return None

            if self._pickle or key == 'session':
                value = _depickle(value)
            else:
                if value['pickled']:
                    value = (value['stored'], value['expires'], _depickle(value['value']))
                else:
                    value = (value['stored'], value['expires'], value['value'])

            log.debug("[key: %s] Value: %s" % (key, value))

            return value
        else:
            return None


    def __contains__(self, key):
        def _has():
            result = self.__getitem__(key)
            if result:
                log.debug("[MongoDB] %s == %s" % (key, result))
                return result is not None
            else:
                return False

        log.debug("[MongoDB] Has '%s'? " % key)
        ret = _has()


        return ret

    def has_key(self, key):
        return key in self

    def set_value(self, key, value, expiretime=None):
        log.debug("[MongoDB %s] Set Key: %s (Expiry: %s) ... " %
                  (self.mongo, key, expiretime))

        _id = {}
        doc = {}

        if self._pickle or key == 'session':
            try:
                value = pickle.dumps(value)
            except:
                log.exception("Failed to pickle value.")
        else:
            value = {
                'stored': value[0],
                'expires': value[1],
                'value': value[2],
                'pickled': False
            }
            try:
                bson.BSON.encode(value)
            except:
                log.warning("Value is not bson serializable, pickling inner value.")
                value['value'] = pickle.dumps(value['value'])
                value['pickled'] = True



        if self._sparse:
            _id = {
                'namespace': self.namespace,
                'key': key
            }

            doc['data'] = bson.Binary(value)
            doc['_id'] = _id
            if expiretime:
                # TODO - What is the datatype of this? it should be instantiated as a datetime instance
                doc['valid_until'] = expiretime
        else:
            _id = self.namespace
            doc['$set'] = {'data.' + key: bson.Binary(value)}
            if expiretime:
                # TODO - What is the datatype of this? it should be instantiated as a datetime instance
                doc['$set']['valid_until'] = expiretime

        log.debug("Upserting Doc '%s' to _id '%s'" % (doc, _id))
        self.mongo.update({"_id": _id}, doc, upsert=True, safe=True)

    def __setitem__(self, key, value):
        self.set_value(key, value)

    def __delitem__(self, key):
        """Delete JUST the key, by setting it to None."""
        if self._sparse:
            self.mongo.remove({'_id.namespace': self.namespace})
        else:
            self.mongo.update({'_id': self.namespace},
                    {'$unset': {'data.' + key: True}}, upsert=False)

    def keys(self):
        if self._sparse:
            return [row['_id']['field'] for row in self.mongo.find({'_id.namespace': self.namespace}, {'_id': True})]
        else:
            return self.mongo.find_one({'_id': self.namespace}, {'data': True}).get('data', {})

class MongoDBContainer(Container):
    namespace_class = MongoDBNamespaceManager

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
    except Exception, e:
        log.exception("Failed to unpickle value '{0}'.".format(e))
        return None
