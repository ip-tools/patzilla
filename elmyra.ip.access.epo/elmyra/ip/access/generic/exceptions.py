# -*- coding: utf-8 -*-
# (c) 2016-2017 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
import cgi
import json
import logging
from contextlib import contextmanager
from pyramid.httpexceptions import HTTPError
from pyramid.response import Response

log = logging.getLogger(__name__)

class GenericAdapterException(Exception):

    def __init__(self, *args, **kwargs):

        self.data = None
        if kwargs.has_key('data'):
            self.data = kwargs['data']

        self.user_info = ''
        if kwargs.has_key('user_info'):
            self.user_info = kwargs['user_info']

        super(GenericAdapterException, self).__init__(*args)

    def get_message(self):
        message = {'user': '', 'details': ''}
        message_parts = []
        if hasattr(self, 'user_info'):
            #message_parts.append(ex.user_info)
            message['user'] = cgi.escape(self.user_info)
        if hasattr(self, 'message'):
            message_parts.append(self.__class__.__name__ + u': ' + u'<pre>{message}</pre>'.format(message=cgi.escape(self.message)))
        if hasattr(self, 'details'):
            message_parts.append(u'<pre>{message}</pre>'.format(message=cgi.escape(self.details)))

        message['details'] = u'<br/>'.join(message_parts)

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

