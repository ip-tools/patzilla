# -*- coding: utf-8 -*-
# (c) 2016 Andreas Motl, Elmyra UG
from bunch import Bunch

class SmartBunch(Bunch):

    def dump(self):
        return self.toJSON()

    def prettify(self):
        return self.toJSON(indent=4)

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
