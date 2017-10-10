# -*- coding: utf-8 -*-
# (c) 2013-2016 Andreas Motl, Elmyra UG
import traceback
import collections
from cornice.util import _JSONError

def get_exception_message(ex, add_traceback=False):
    name = ex.__class__.__name__
    description = '%s: %s' % (name, unicode(ex.message))
    if add_traceback:
        description += '\n' + get_safe_traceback(ex)
    return description

def get_safe_traceback(ex):
    if type(ex) is not _JSONError:
        tb = traceback.format_exc()
        return tb
    else:
        return 'traceback not displayed due to _JSONError not being printable'

def safe_value(value):
    """
    Gracefully convert a dict-like object to a vanilla dict,
    e.g. CaseInsensitiveDict to dict
    """
    if hasattr(value, 'items') and callable(value.items):
        return dict(value.items())
    else:
        return value

def dict_subset(bigdict, *wanted_keys):
    #return dict([(i, safe_value(bigdict[i])) for i in wanted_keys if i in bigdict])
    return dict([(i, safe_value(bigdict[i])) for i in wanted_keys])

def dict_prefix_key(d, prefix):
    # prefix keys in dictionary
    new = {}
    for key, value in d.iteritems():
        key = prefix + key
        new[key] = value
    return new

def object_attributes_to_dict(obj, attribute_names):
    return dict([(attr, safe_value(getattr(obj, attr))) for attr in attribute_names if hasattr(obj, attr)])

# https://gist.github.com/angstwad/bf22d1822c38a92ec0a9
def dict_merge(dct, merge_dct):
    """ Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
    updating only top-level keys, dict_merge recurses down into dicts nested
    to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
    ``dct``.
    :param dct: dict onto which the merge is executed
    :param merge_dct: dct merged into dct
    :return: None
    """
    for k, v in merge_dct.iteritems():
        if (k in dct and isinstance(dct[k], dict)
            and isinstance(merge_dct[k], collections.Mapping)):
            dict_merge(dct[k], merge_dct[k])
        else:
            dct[k] = merge_dct[k]
