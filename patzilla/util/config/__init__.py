# -*- coding: utf-8 -*-
# (c) 2016 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
from ConfigParser import ConfigParser

def read_config(configfiles, kind=None):
    configfiles = to_list(configfiles)
    config = ConfigParser()
    config.read(configfiles)
    if kind is not None:
        settings = convert_config(config, kind=kind)
    else:
        settings = convert_config(config)

    # Amend settings: Make real Booleans from strings
    settings['smtp']['tls'] = asbool(settings['smtp'].get('tls', True))
    # Amend settings: Properly decode specific settings using appropriate charset
    settings['email']['signature'] = settings['email']['signature'].decode('utf-8')

    return settings

def convert_config(config, kind=dict):
    # serialize section-based ConfigParser contents into
    # nested dict or other dict-like thing
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

def normalize_docopt_options(options):
    normalized = {}
    for key, value in options.items():
        key = key.strip('--<>')
        normalized[key] = value
    return normalized
