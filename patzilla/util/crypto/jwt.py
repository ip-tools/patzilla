# -*- coding: utf-8 -*-
# (c) 2014 Andreas Motl, Elmyra UG
from __future__ import absolute_import
import logging
import datetime
import jws
import python_jwt as jwt
from Crypto.Protocol.KDF import PBKDF2
from Crypto.PublicKey import RSA
from zope.interface.interface import Interface
from zope.interface.declarations import implements

log = logging.getLogger(__name__)

# https://github.com/davedoesdev/python-jwt

class ISigner(Interface):
    pass

class JwtSigner(object):

    implements(ISigner)

    def __init__(self, key=None, ttl=None):
        self.key = key
        #self.ttl = ttl or datetime.timedelta(seconds=1)
        #self.ttl = ttl or datetime.timedelta(minutes=60)
        self.ttl = ttl or datetime.timedelta(hours=24)
        #self.ttl = ttl or datetime.timedelta(days=30 * 12 * 5)   # 5 years

    # http://stackoverflow.com/questions/20483504/making-rsa-keys-from-a-password-in-python/20484325#20484325
    def genkey(self, password, salt='', keysize=2048):

        master_key = PBKDF2(password, salt)

        def my_rand(n):
            # kluge: use PBKDF2 with count=1 and incrementing salt as deterministic PRNG
            my_rand.counter += 1
            return PBKDF2(master_key, "my_rand:%d" % my_rand.counter, dkLen=n, count=1)

        my_rand.counter = 0
        self.key = RSA.generate(keysize, randfunc=my_rand)

        return self.key

    def readkey(self, pemfile):
        # read a key generated with openssl, e.g.::
        #
        #     openssl genrsa -out opaquelinks.pem 256
        f = open(pemfile, 'r')
        self.key = RSA.importKey(f.read())
        f.close()

        return self.key

    def sign(self, data, ttl=None):
        # TODO: handle error conditions
        # TODO: maybe croak if self.key is None
        ttl = ttl or self.ttl
        payload = {'data': data}
        token = jwt.generate_jwt(payload, priv_key=self.key, algorithm='RS256', lifetime=ttl)
        return token

    def unsign(self, token):
        token = str(token)
        try:
            header_future, payload_future = jwt.process_jwt(token)
            header, payload = jwt.verify_jwt(token, pub_key=self.key, allowed_algs=['HS256', 'RS256', 'ES256', 'PS256'])

            if not payload.has_key('data'):
                error_payload = {
                    'location': 'JSON Web Token',
                    'name': self.__class__.__name__,
                    'description': 'Payload lacks "data" attribute',
                    'token': token,
                    'jwt_header': header_future,
                    'jwt_payload': payload_future,
                    }
                raise JwtVerifyError(error_payload)

            # compute metadata without payload data
            metadata = payload.copy()
            del metadata['data']

            return payload['data'], metadata

        except (ValueError, TypeError) as ex:
            error_payload = {
                'location': 'JSON Web Signature',
                'name': ex.__class__.__name__,
                'description': str(ex),
                'token': token,
            }
            raise JwtVerifyError(error_payload)

        except jws.exceptions.SignatureError as ex:
            error_payload = {
                'location': 'JSON Web Signature',
                'name': ex.__class__.__name__,
                'description': ex.message,
                'token': token,
                'jwt_header': header_future,
                'jwt_payload': payload_future,
            }
            raise JwtVerifyError(error_payload)

        except jwt._JWTError as ex:
            if ex.message == 'expired':
                error_payload = {
                    'location': 'JSON Web Token',
                    'name': ex.__class__.__name__,
                    'description': ex.message,
                    'jwt_header': header_future,
                    'jwt_expiry': payload_future['exp'],
                }
                raise JwtExpiryError(error_payload)
            else:
                error_payload = {
                    'location': 'JSON Web Token',
                    'name': ex.__class__.__name__,
                    'description': ex.message,
                    'token': token,
                    'jwt_header': header_future,
                    'jwt_payload': payload_future,
                }
                raise JwtVerifyError(error_payload)


class JwtVerifyError(Exception):
    pass

class JwtExpiryError(Exception):
    pass
