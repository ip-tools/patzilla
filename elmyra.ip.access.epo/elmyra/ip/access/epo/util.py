# -*- coding: utf-8 -*-
# (c) 2013 Andreas Motl, Elmyra UG
import traceback
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

def object_attributes_to_dict(obj, attribute_names):
    return dict([(attr, safe_value(getattr(obj, attr))) for attr in attribute_names if hasattr(obj, attr)])


class PngRenderer(object):

    def __init__(self, info):
        pass

    def __call__(self, value, system):
        request = system.get('request')
        if request is not None:
            response = request.response
            response.content_type = 'image/png'
        return value
