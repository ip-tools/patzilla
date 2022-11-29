# -*- coding: utf-8 -*-
# (c) 2016 Andreas Motl, Elmyra UG
import json
import types
from bunch import Bunch
from jsonpointer import JsonPointer


class SmartBunch(Bunch):

    def dump(self):
        return self.toJSON()

    def pretty(self):
        return self.toJSON(indent=4)

    def prettify(self):
        return self.pretty()

    @classmethod
    def bunchify(cls, x):
        """
        Recursively transforms a dictionary into a SmartBunch via copy.
        Generic "bunchify", also works with descendants of Bunch.
        """
        if isinstance(x, dict):
            return cls( (k, cls.bunchify(v)) for k,v in x.iteritems() )
        elif isinstance(x, (list, tuple)):
            return type(x)( cls.bunchify(v) for v in x )
        else:
            return x


def unique_sequence(seq):
    # https://stackoverflow.com/questions/480214/how-do-you-remove-duplicates-from-a-list-in-python-whilst-preserving-order/480227#480227
    seen = set()
    seen_add = seen.add
    unhashable_types = (types.ListType, types.DictionaryType)
    return [x for x in seq if type(x) in unhashable_types or not (x in seen or seen_add(x))]


def jpath(path, doc):
    """
    Resolve JSON Pointers according to RFC 6901.

    - https://datatracker.ietf.org/doc/html/rfc6901
    - https://github.com/stefankoegl/python-json-pointer
    """
    return JsonPointer(path).resolve(doc)


def jd(data):
    """
    Serialize data to JSON, for printing to STDOUT.
    """
    return json.dumps(data, indent=2)
