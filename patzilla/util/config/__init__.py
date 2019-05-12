# -*- coding: utf-8 -*-
# (c) 2016-2018 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
import os
import logging
from glob import glob
from ConfigParser import ConfigParser

logger = logging.getLogger(__name__)

def get_configuration(*args, **kwargs):
    config_files = []
    config_files += list(args)
    logger.info('Requested configuration files: {}'.format(make_list(config_files)))
    config, used = read_config(config_files, kind=kwargs.get('kind'))
    if config:
        if 'main' in config and 'include' in config.main:
            includes = read_list(config.main.include)
            for include in includes:
                if include != os.path.abspath(include):
                    # FIXME: Use base paths of *all* requested configuration files
                    include = os.path.join(os.path.dirname(config_files[0]), include)
                if '*' in include or '?' in include:
                    config_files += glob(include)
                else:
                    config_files.append(include)
            logger.debug('Expanded configuration files:  {}'.format(make_list(config_files)))
            config, used = read_config(config_files, kind=kwargs.get('kind'))
        logger.info('Effective configuration files: {}'.format(make_list(used)))
        return config
    else:
        msg = u'Could not read settings from configuration files: {}'.format(config_files)
        logger.critical(msg)
        raise ValueError(msg)

def read_config(configfiles, kind=None):
    configfiles_requested = to_list(configfiles)
    config = ConfigParser()
    configfiles_used = config.read(configfiles_requested)
    settings = convert_config(config, kind=kind)
    return settings, configfiles_used

def convert_config(config, kind=None):
    """
    Serialize section-based ConfigParser contents
    into nested dict or other dict-like thing.
    """
    kind = kind or dict
    if isinstance(config, ConfigParser):
        config_dict = kind()
        for section in config.sections():
            config_dict[section] = kind(config.items(section, raw=True))
        return config_dict
    else:
        return config

def to_list(obj):
    """Convert an object to a list if it is not already one"""
    # stolen from cornice.util
    if not isinstance(obj, (list, tuple)):
        obj = [obj, ]
    return obj

truthy = frozenset(('t', 'true', 'y', 'yes', 'on', '1'))
def asbool(s):
    """ Return the boolean value ``True`` if the case-lowered value of string
    input ``s`` is any of ``t``, ``true``, ``y``, ``on``, or ``1``, otherwise
    return the boolean value ``False``.  If ``s`` is the value ``None``,
    return ``False``.  If ``s`` is already one of the boolean values ``True``
    or ``False``, return it."""
    # stolen from pyramid.settings
    if s is None:
        return False
    if isinstance(s, bool):
        return s
    s = str(s).strip()
    return s.lower() in truthy

def read_list(string, separator=u','):
    if string is None:
        return []
    elif isinstance(string, list):
        return string
    result = map(unicode.strip, string.split(separator))
    if len(result) == 1 and not result[0]:
        result = []
    return result

def make_list(items, separator=u', '):
    return separator.join(items)

def normalize_docopt_options(options):
    normalized = {}
    for key, value in options.items():
        key = key.strip('--<>')
        normalized[key] = value
    return normalized
