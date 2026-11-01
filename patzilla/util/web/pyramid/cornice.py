# -*- coding: utf-8 -*-
# (c) 2017 Andreas Motl, Elmyra UG
import json

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


def json_error(request):
    """Returns an HTTPError with the given status and message.

    The HTTP error content type is "application/json"
    """
    from cornice.renderer import JSONError
    # Cornice >= 5 yields content as bytes. Let's decode it.
    for error in request.errors:
        content = error["description"]["content"]
        if isinstance(content, bytes):
            content = content.decode("utf-8")
        error["description"]["content"] = content
    return JSONError(serializer=json.dumps, serializer_kw={}, errors=request.errors)
