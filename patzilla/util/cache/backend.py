import os
import shutil

import appdirs
from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options


def get_cache_directory(testing=False):
    appname = "patzilla"
    if testing:
        appname += "-testing"
    cache_directory = os.path.join(appdirs.user_cache_dir(appname=appname), "cache")
    if not os.path.exists(cache_directory):
        os.makedirs(cache_directory)
    return cache_directory


def configure_cache_backend(kind="memory", cache_directory=None, clear_cache=False):

    if cache_directory is None:
        cache_directory = get_cache_directory()

    # Cache backend: memory.
    if kind == "memory":
        cache_opts = {
            'cache.type': 'memory',
        }

    # Cache backend: filesystem.
    elif kind == "filesystem":

        if clear_cache:
            shutil.rmtree(cache_directory)

        cache_data_dir = os.path.join(cache_directory, "data")
        cache_lock_dir = os.path.join(cache_directory, "lock")
        cache_opts = {
            'cache.type': 'file',
            'cache.data_dir': cache_data_dir,
            'cache.lock_dir': cache_lock_dir,
        }

    else:
        raise TypeError("Unknown cache backend: {}".format(kind))

    cache_opts.update({
        'cache.regions': 'static',
        'cache.static.expire': 2592000,
        'cache.key_length': 512,
    })
    CacheManager(**parse_cache_config_options(cache_opts))
