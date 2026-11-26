# -*- coding: utf-8 -*-
# (c) 2016-2017 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
import html
import logging
from contextlib import contextmanager

log = logging.getLogger(__name__)


class GenericAdapterException(Exception):

    def __init__(self, *args, **kwargs):

        self.data = None
        if 'data' in kwargs:
            self.data = kwargs['data']

        self.user_info = ''
        if 'user_info' in kwargs:
            self.user_info = kwargs['user_info']

        super(GenericAdapterException, self).__init__(*args)

    def get_message(self):
        message = {'user': '', 'details': ''}
        message_parts = []
        if hasattr(self, 'user_info'):
            #message_parts.append(ex.user_info)
            message['user'] = html.escape(self.user_info)
        if hasattr(self, 'message'):
            val = str(getattr(self, 'message'))
            message_parts.append(self.__class__.__name__ + ': ' + '<pre>{message}</pre>'.format(message=html.escape(val)))
        if hasattr(self, 'details'):
            val = str(getattr(self, 'details'))
            message_parts.append('<pre>{message}</pre>'.format(message=html.escape(val)))

        message['details'] = '<br/>'.join(message_parts)

        return message


class SearchException(GenericAdapterException):
    pass

class NoResultsException(GenericAdapterException):
    pass



def is_http_error(ex, status_code=None):
    """Whether `ex` is an HTTP error or service error, optionally with the given status code."""
    code = getattr(ex, "status_code", None)
    if not isinstance(code, int) or not isinstance(ex, Exception):
        return False
    return status_code is None or code == status_code


class ServiceError(Exception):
    """
    An error reported to API clients using the JSON error envelope the frontend expects:
    `{"status": "error", "errors": [{"location": ..., "name": ..., "description": ...}]}`.
    """

    def __init__(self, location, name, description, status_code=400, detail=None):
        self.errors = [{"location": location, "name": name, "description": description}]
        self.status_code = status_code
        self.detail = detail or str(description)
        super().__init__(self.detail)

    @property
    def envelope(self):
        return {"status": "error", "errors": self.errors}


# https://stackoverflow.com/questions/15572288/general-decorator-to-wrap-try-except-in-python/15573313#15573313
@contextmanager
def ignored(*exceptions):
    try:
        yield
    except exceptions as ex:
        log.warning('Ignored exception: {name}({ex})'.format(name=ex.__class__.__name__, ex=ex))

