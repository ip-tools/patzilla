from mongodb_gridfs_beaker import MongoDBGridFSNamespaceManager

def includeme(config):
    # monkey patch 3rd party class to fix runtime error
    MongoDBGridFSNamespaceManager.lock_dir = None
