# -*- coding: utf-8 -*-
# (c) 2022 Andreas Motl <andreas.motl@ip-tools.org>
from __future__ import absolute_import
import logging
import os
import shutil

import platformdirs
from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options

logger = logging.getLogger(__name__)


def get_cache_directory(testing=False):
    appname = "patzilla"
    if testing:
        appname += "-testing"
    cache_directory = os.path.join(platformdirs.user_cache_dir(appname=appname), "cache")
    if not os.path.exists(cache_directory):
        os.makedirs(cache_directory)
    return cache_directory


def configure_cache_backend(kind="memory", cache_directory=None, clear_cache=False):
    """
    Configure and bootstrap the Beaker cache backend adapter.

    Currently, it supports "memory", "filesystem" and "mongodb".
    """

    cache_location = None

    # Cache backend: memory.
    if kind == "memory":
        cache_opts = {
            'cache.type': 'memory',
        }

    # Cache backend: filesystem.
    elif kind == "filesystem":

        if cache_directory is None:
            cache_directory = get_cache_directory()

        if clear_cache:
            shutil.rmtree(cache_directory)

        cache_data_dir = os.path.join(cache_directory, "data")
        cache_lock_dir = os.path.join(cache_directory, "lock")
        cache_opts = {
            'cache.type': 'file',
            'cache.data_dir': cache_data_dir,
            'cache.lock_dir': cache_lock_dir,
        }

        cache_location = cache_directory

    elif kind == "mongodb":
        cache_opts = {
            'cache.type': 'ext:mongodb',
            'cache.url': 'mongodb://localhost:27017/beaker.cache',
            'cache.sparse_collection': True,
        }

    else:
        raise TypeError("Unknown cache backend: {}".format(kind))

    # Set general options.
    cache_opts.update({
        'cache.regions': 'static,search,medium',
        'cache.static.expire': 2592000,  # 1 month
        'cache.search.expire': 604800,   # 1 week
        'cache.medium.expire': 86400,    # 1 day
        'cache.key_length': 512,
    })

    # Configure the caching subsystem at runtime.
    logger.info("Configuring object cache. kind={}, location={}".format(kind, cache_location))
    CacheManager(**parse_cache_config_options(cache_opts))
