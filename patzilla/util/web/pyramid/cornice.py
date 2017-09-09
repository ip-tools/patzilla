# -*- coding: utf-8 -*-
# (c) 2017 Andreas Motl, Elmyra UG
from __future__ import absolute_import
from cornice.errors import Errors

def add_location_whitelisted(self, location, name=None, description=None, **kw):
    """Registers a new error."""

    # Allow all labels as "location", as this is used throughout PatZilla.
    # Patch required after upgrading to cornice-2.4.0.
    """
    allowed = ('body', 'querystring', 'url', 'header', 'path',
               'cookies', 'method')
    if location != '' and location not in allowed:
        raise ValueError('%r not in %s' % (location, allowed))
    """

    self.append(dict(
        location=location,
        name=name,
        description=description, **kw))

Errors.add = add_location_whitelisted
