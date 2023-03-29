# -*- coding: utf-8 -*-
# (c) 2022 Andreas Motl <andreas.motl@ip-tools.org>
import datetime

import pytest
import python_jwt
from pkg_resources import resource_filename

from patzilla.util.crypto.jwt import JwtSigner, JwtVerifyError, JwtExpiryError


PAYLOAD = {'foo': 'bar'}


@pytest.fixture(scope="session")
def jwt_signer():
    """
    A fixture to provide a session-wide signer object already populated with a
    key generated at runtime.
    """
    signer = JwtSigner()
    signer.genkey(keysize=512)
    return signer


def test_signer_genkey(jwt_signer):
    """
    Sign and unsign the demo payload with the runtime signer.
    """

    token = jwt_signer.sign(PAYLOAD)
    assert token.startswith("eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.")

    data, meta = jwt_signer.unsign(token)
    assert data == PAYLOAD


def test_signer_readkey():
    """
    Sign and unsign the demo payload with another signer which is using a key
    from the filesystem.
    """

    signer = JwtSigner()

    keyfile = resource_filename('patzilla.navigator', 'resources/opaquelinks.pem')
    signer.readkey(keyfile)

    token = signer.sign(PAYLOAD)
    assert token.startswith("eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.")

    data, meta = signer.unsign(token)
    assert data == PAYLOAD


def test_signer_sign_invalid_expiration(jwt_signer):
    """
    Proof that invalid expiration dates are rejected when signing.
    """
    with pytest.raises(ValueError) as ex:
        jwt_signer.sign("foo", ttl="bar")
    assert ex.match("value=bar, type=<class 'str'> is an invalid JWT expiration date, use `datetime.datetime` or `datetime.timedelta")


def test_signer_unsign_expired_token():
    """
    Proof that reading expired tokens is rejected.
    """
    signer = JwtSigner(ttl=datetime.datetime(year=2022, month=1, day=1, hour=0, minute=0, second=0, microsecond=0))
    signer.genkey()
    token = signer.sign("foo")
    with pytest.raises(JwtExpiryError) as ex:
        signer.unsign(token)
    value = ex.value.args[0]
    assert value == {
        'description': 'expired',
        'location': 'JSON Web Token',
        'name': '_JWTError',
        'jwt_expiry': 1640995200,
        'jwt_header': {'alg': 'RS256', 'typ': 'JWT'},
    }


def test_signer_unsign_invalid_token():
    """
    Proof that reading invalid tokens is rejected.
    """
    signer = JwtSigner()
    with pytest.raises(JwtVerifyError) as ex:
        signer.unsign("foo")
    value = ex.value.args[0]
    assert value == {
        'description': 'invalid JWT format',
        'location': 'JSON Web Signature',
        'name': '_JWTError',
    }


def test_signer_unsign_invalid_payload(jwt_signer):
    """
    Proof that reading claims in unknown format is rejected.
    """
    token = python_jwt.generate_jwt(
        claims={"foo": "bar"},
        priv_key=jwt_signer.key,
        algorithm='RS256',
        expires=datetime.datetime(year=2038, month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
    )
    with pytest.raises(JwtVerifyError) as ex:
        jwt_signer.unsign(token)
    value = ex.value.args[0]

    moving_targets = ["iat", "nbf", "jti"]
    for moving_target in moving_targets:
        if moving_target in value["jwt_payload"]:
            del value["jwt_payload"][moving_target]

    assert value == {
        'location': 'JSON Web Token',
        'jwt_header': {'alg': 'RS256', 'typ': 'JWT'},
        'description': 'No "data" attribute in payload/claims',
        'name': 'JwtSigner',
        'jwt_payload': {'foo': 'bar', 'exp': 2145916800},
    }
