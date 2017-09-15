# -*- coding: utf-8 -*-
# (c) 2014-2016 Andreas Motl, Elmyra UG
import logging
import Crypto
import datetime
from pkg_resources import resource_filename
from simplejson import JSONDecodeError
from cornice.service import Service
from pyramid.httpexceptions import HTTPBadRequest
from patzilla.util.crypto.jwt import JwtSigner, JwtVerifyError, ISigner, JwtExpiryError
from patzilla.util.date import datetime_iso, unixtime_to_datetime
from patzilla.util.python import exception_traceback

try:
    from patzilla.util.web.uwsgi.uwsgidecorators import postfork
except ImportError:
    class postfork(object):
        def __init__(self, f):
            pass
        def __call__(self, *args, **kwargs):
            pass

log = logging.getLogger(__name__)


@postfork
def init_random():
    Crypto.Random.atfork()


def includeme(config):

    # register a signer object used throughout this place
    signer = JwtSigner()

    # v1: always create a key
    #signer.genkey('12345', salt='patzilla.navigator.opaquelinks', keysize=768)

    # v2: have a key on the filesystem
    keyfile = resource_filename(__name__, 'resources/opaquelinks.pem')
    signer.readkey(keyfile)

    config.registry.registerUtility(signer)

    # attempt to decode opaque parameter tokens on each request
    config.add_subscriber(create_request_interceptor, 'pyramid.events.ContextFound')


# ------------------------------------------
#   hooks
# ------------------------------------------
def create_request_interceptor(event):
    """
    Intercept "op" (opaque parameters) request parameter,
    decode it and serve as ``request.opaque`` dictionary.
    """
    request = event.request

    request.opaque = {}
    request.opaque_meta = {}

    # extract opaque parameters token from request
    op_token = request.params.get('op')

    # do nothing if no token given
    if not op_token:
        return

    registry = event.request.registry
    signer = registry.getUtility(ISigner)

    try:
        data, meta = signer.unsign(op_token)
        if data:
            request.opaque.update(data)
        else:
            log.error('opaque parameter token is empty. data=%s, token=%s', data, op_token)
        if meta:
            request.opaque_meta.update(meta)
            request.opaque_meta.update({'status': 'ok'})
        else:
            log.error('metadata of opaque parameter token is empty. meta=%s, token=%s', meta, op_token)

    except JwtExpiryError as ex:
        expiry_unixtime = ex.message['jwt_expiry']
        expiry_iso = datetime_iso(unixtime_to_datetime(expiry_unixtime))
        ex.message['jwt_expiry_iso'] = expiry_iso
        log.error('Opaque parameter token expired: expiry=%s, message=%s', expiry_iso, ex.message)
        request.opaque_meta.update({'status': 'error', 'errors': [ex.message]})
        # TODO: log/send full stacktrace
        log.error(exception_traceback())

    except JwtVerifyError as ex:
        log.error('Error while decoding opaque parameter token: %s', ex.message)
        request.opaque_meta.update({'status': 'error', 'errors': [ex.message]})
        # TODO: log/send full stacktrace
        log.error(exception_traceback())


# ------------------------------------------
#   services
# ------------------------------------------
opaquelinks_token_service = Service(
    name='opaquelinks-token',
    path='/api/opaquelinks/token',
    description="opaquelinks token generator")

opaquelinks_verify_service = Service(
    name='opaquelinks-verify',
    path='/api/opaquelinks/token/verify',
    description="opaquelinks token verifier")


# ------------------------------------------
#   service handlers
# ------------------------------------------
@opaquelinks_token_service.post(accept="application/json")
def opaquelinks_token_handler(request):
    """Generate an opaquelinks token"""
    payload = request_payload(request)
    signer = request.registry.getUtility(ISigner)

    ttl = None
    if 'ttl' in request.params:
        ttl_seconds = int(request.params.get('ttl'))
        ttl = datetime.timedelta(seconds=ttl_seconds)

    return signer.sign(payload, ttl=ttl)


@opaquelinks_verify_service.post(accept="application/json")
def opaquelinks_verify_handler(request):
    """Verify an opaquelinks token"""

    token = token_payload(request)

    if not token:
        return HTTPBadRequest('Token missing')

    signer = request.registry.getUtility(ISigner)
    data, meta = signer.unsign(token)
    return data


# ------------------------------------------
#   utility functions
# ------------------------------------------
def request_payload(request):
    payload = {}
    if request.content_type == 'application/json':
        try:
            payload = request.json
        except JSONDecodeError as error:
            log.error('Could not derive data from json request: %s body=%s', error, request.body)

    payload.update(dict(request.params))
    return payload

def token_payload(request):
    token = None
    if request.content_type == 'application/json':

        try:
            token = str(request.json)
        except JSONDecodeError as error:
            log.error('Could not extract token from json request: %s body=%s', error, request.body)

    if not token:
        log.error('Could not extract token from request: content-type=%s, body=%s', request.content_type, request.body)

    return token
