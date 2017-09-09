from mongodb_gridfs_beaker import MongoDBGridFSNamespaceManager, log, pickle

def includeme(config):

    # Monkey patch 3rd party class to fix runtime error
    MongoDBGridFSNamespaceManager.lock_dir = None

    # Monkey patch "set_value" method after upgrade to Beaker-1.9.0 to accept the "expiretime" argument.
    def set_value(self, key, value, expiretime=None):
        query = {'namespace': self.namespace, 'filename': key}
        log.debug("[MongoDBGridFS %s] Set Key: %s" % (self.gridfs, query))

        try:
            value = pickle.dumps(value)
        except:
            log.exception("[MongoDBGridFS] Failed to pickle value.")
            return None

        mongo, gridfs = self.gridfs
        self.__delitem__(key)
        gridfs.put(value, **query)

    MongoDBGridFSNamespaceManager.set_value = set_value
