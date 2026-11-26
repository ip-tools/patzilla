# -*- coding: utf-8 -*-
# (c) 2014-2026 Andreas Motl, Elmyra UG
"""
Opaque links: Sign request parameters into a JWT token (`op` parameter), to share
links with fixed parameters and an optional expiry time.
"""
import dataclasses
import datetime
import logging
import os
from typing import Annotated, Dict, Optional, cast

from fastapi import APIRouter, Body, HTTPException, Request

from patzilla.util.crypto.jwt import JwtExpiryError, JwtSigner, JwtVerifyError
from patzilla.util.date import datetime_iso, unixtime_to_datetime
from patzilla.util.python import exception_traceback
from patzilla.web.dependencies import State

log = logging.getLogger(__name__)

KEYFILE = os.path.join(os.path.dirname(__file__), 'resources', 'opaquelinks.pem')

router = APIRouter(tags=["opaquelinks"])


def create_signer():
    signer = JwtSigner()
    signer.readkey(KEYFILE)
    return signer


@dataclasses.dataclass
class OpaqueParameters:
    data: Dict = dataclasses.field(default_factory=dict)
    meta: Dict = dataclasses.field(default_factory=dict)


def decode_opaque_parameters(signer, token: Optional[str]) -> OpaqueParameters:
    """
    Decode the opaque parameters token. Errors are reported within `meta`.
    """
    opaque = OpaqueParameters()
    if not token:
        return opaque

    try:
        data, meta = signer.unsign(token)
        if data:
            opaque.data.update(data)
        else:
            log.error('opaque parameter token is empty. data=%s, token=%s', data, token)
        if meta:
            opaque.meta.update(meta)
            opaque.meta.update({'status': 'ok'})
        else:
            log.error('metadata of opaque parameter token is empty. meta=%s, token=%s', meta, token)

    except JwtExpiryError as ex:
        info: Dict = cast(dict, ex.args[0])
        expiry_iso = datetime_iso(unixtime_to_datetime(info['jwt_expiry']))
        msg = f'Opaque parameter token expired: expiry={expiry_iso}'
        opaque.meta.update({'status': 'error', 'errors': [msg]})
        log.error(exception_traceback())

    except JwtVerifyError as ex:
        msg = f'Decoding opaque parameter token failed: {ex}'
        opaque.meta.update({'status': 'error', 'errors': [msg]})
        log.error(exception_traceback())

    return opaque


@router.post("/api/opaquelinks/token", name="opaquelinks-token", summary="opaquelinks token generator")
def opaquelinks_token_handler(request: Request, state: State, payload: Annotated[Optional[dict], Body()] = None,
                              ttl: Optional[int] = None):
    """Generate an opaquelinks token. Query parameters are signed, too."""
    data = dict(payload or {})
    data.update(request.query_params)
    return state.signer.sign(data, ttl=datetime.timedelta(seconds=ttl) if ttl else None)


@router.post("/api/opaquelinks/token/verify", name="opaquelinks-verify", summary="opaquelinks token verifier")
def opaquelinks_verify_handler(state: State, token: Annotated[Optional[str], Body()] = None):
    """Verify an opaquelinks token"""
    if not token:
        raise HTTPException(400, 'Token missing')
    data, meta = state.signer.unsign(token)
    return data
