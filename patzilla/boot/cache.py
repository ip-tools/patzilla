# -*- coding: utf-8 -*-
# (c) 2022 Andreas Motl <andreas.motl@ip-tools.org>
from __future__ import absolute_import
import logging
import os
import shutil
from typing import Dict, Union

import platformdirs
from beaker.cache import CacheManager, cache_regions
from beaker.util import coerce_cache_params, parse_cache_config_options

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

    cache_opts: Dict[str, Union[str, bool, int]]
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


def configure_cache_regions(settings):
    """
    Configure Beaker cache regions from application settings with `cache.` prefix,
    e.g. `cache.regions = search, static` and `cache.search.expire = 7200`.

    This is the same procedure `pyramid_beaker` used before.
    """
    cache_settings = {"regions": []}
    for key, value in settings.items():
        for prefix in ("beaker.cache.", "cache."):
            if key.startswith(prefix):
                name = key[len(prefix):].strip()
                cache_settings[name] = value.strip() if isinstance(value, str) else value
    coerce_cache_params(cache_settings)
    cache_settings.setdefault("enabled", True)

    for region in cache_settings["regions"]:
        if not region:
            continue
        region_settings = {
            "data_dir": cache_settings.get("data_dir"),
            "lock_dir": cache_settings.get("lock_dir"),
            "expire": cache_settings.get("expire", 60),
            "enabled": cache_settings["enabled"],
            "key_length": cache_settings.get("key_length", 250),
            "type": cache_settings.get("type"),
            "url": cache_settings.get("url"),
        }
        region_prefix = "%s." % region
        for key in list(cache_settings.keys()):
            if key.startswith(region_prefix):
                region_settings[key[len(region_prefix):]] = cache_settings.pop(key)
        coerce_cache_params(region_settings)
        cache_regions[region] = region_settings
