# -*- coding: utf-8 -*-
# (c) 2016-2017 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
import html
import json
import logging
from contextlib import contextmanager
from pyramid.httpexceptions import HTTPError
from pyramid.response import Response

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



class ExampleJsonException(HTTPError, GenericAdapterException):
    def __init__(self, data=None, status=404):
        #body = {'status': 'error', 'errors': errors}
        Response.__init__(self, json.dumps(data, use_decimal=True))
        self.status = status
        self.content_type = 'application/json'


# https://stackoverflow.com/questions/15572288/general-decorator-to-wrap-try-except-in-python/15573313#15573313
@contextmanager
def ignored(*exceptions):
    try:
        yield
    except exceptions as ex:
        log.warning('Ignored exception: {name}({ex})'.format(name=ex.__class__.__name__, ex=ex))

