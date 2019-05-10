# -*- coding: utf-8 -*-

# (c) 2014 Andreas Motl, Elmyra UG

import logging
from datetime import datetime, timedelta

import python_jwt
from jwcrypto import jwk
from zope.interface.interface import Interface
#from zope.interface.declarations import implements
#from zope.interface import implementer

log = logging.getLogger(__name__)


class ISigner(Interface):
    pass


class JwtSigner(object):
    """
    Generate and verify JSON Web Tokens.

    - https://en.wikipedia.org/wiki/JSON_Web_Token
    - https://github.com/davedoesdev/python-jwt
    - https://github.com/latchset/jwcrypto
    - https://jwcrypto.readthedocs.io/
    """

# py27  implements(ISigner)

    def __init__(self, key=None, ttl=None):
        self.key = key
        #self.ttl = ttl or timedelta(seconds=1)
        #self.ttl = ttl or timedelta(minutes=60)
        self.ttl = ttl or timedelta(hours=24)
        #self.ttl = ttl or timedelta(days=30 * 12 * 5)   # 5 years

    def genkey(self, keysize=512):
        """
        Generate RSA key using jwcrypto.
        """
        self.key = jwk.JWK.generate(kty='RSA', size=keysize)
        return self.key

    def readkey(self, pemfile):
        """
        Read RSA key using jwcrypto.
        """
        with open(pemfile, "rb") as pemfile:
            self.key = jwk.JWK.from_pem(pemfile.read())
            return self.key

    def sign(self, data, ttl=None):
        # TODO: handle error conditions
        # TODO: maybe croak if self.key is None
        ttl = ttl or self.ttl
        payload = {'data': data}
        kwargs = {}
        if isinstance(ttl, timedelta):
            kwargs["lifetime"] = ttl
        elif isinstance(ttl, datetime):
            kwargs["expires"] = ttl
        else:
            raise ValueError("value={}, type={} is an invalid JWT expiration date, "
                             "use `datetime.datetime` or `datetime.timedelta`".format(ttl, type(ttl)))
        token = python_jwt.generate_jwt(payload, priv_key=self.key, algorithm='RS256', **kwargs)
        return token

    def unsign(self, token):
        token = str(token)
        try:
            header_future, payload_future = python_jwt.process_jwt(token)
        except (ValueError, TypeError, python_jwt._JWTError) as ex:
            error_payload = {
                'location': 'JSON Web Signature',
                'name': ex.__class__.__name__,
                'description': str(ex),
            }
            raise JwtVerifyError(error_payload)

        try:
            header, payload = python_jwt.verify_jwt(
                jwt=token,
                pub_key=self.key,
                allowed_algs=['HS256', 'RS256', 'ES256', 'PS256'],
                iat_skew=timedelta(minutes=5),
            )

            if 'data' not in payload:
                error_payload = {
                    'location': 'JSON Web Token',
                    'name': self.__class__.__name__,
                    'description': 'No "data" attribute in payload/claims',
                    'jwt_header': header_future,
                    'jwt_payload': payload_future,
                    }
                raise JwtVerifyError(error_payload)

            # compute metadata without payload data
            metadata = payload.copy()
            del metadata['data']

            return payload['data'], metadata

        except python_jwt._JWTError as ex:
            if str(ex) == 'expired':
                error_payload = {
                    'location': 'JSON Web Token',
                    'name': ex.__class__.__name__,
                    'description': str(ex),
                    'jwt_header': header_future,
                    'jwt_expiry': payload_future.get('exp'),
                }
                raise JwtExpiryError(error_payload)
            else:
                error_payload = {
                    'location': 'JSON Web Token',
                    'name': ex.__class__.__name__,
                    'description': str(ex),
                    'jwt_header': header_future,
                    'jwt_payload': payload_future,
                }
                raise JwtVerifyError(error_payload)


class JwtVerifyError(Exception):
    pass


class JwtExpiryError(Exception):
    pass
