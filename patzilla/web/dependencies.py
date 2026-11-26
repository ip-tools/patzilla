# -*- coding: utf-8 -*-
# (c) 2026 Andreas Motl <andreas.motl@ip-tools.org>
"""
Request dependencies. Results are cached per request by FastAPI.
"""
import typing as t
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from pydantic import BeforeValidator

from patzilla.util.config import asbool
from patzilla.util.web.identity.store import User

if t.TYPE_CHECKING:  # pragma: no cover
    from patzilla.navigator.opaquelinks import OpaqueParameters
    from patzilla.navigator.settings import RuntimeSettings
    from patzilla.web.state import AppState

# Booleans like `asbool`, accepting e.g. "true", "yes", "1", "on", and treating anything else as false.
LenientBool = Annotated[bool, BeforeValidator(asbool)]


def get_state(request: Request) -> "AppState":
    return request.app.state.patzilla


State = Annotated["AppState", Depends(get_state)]


def get_user(request: Request) -> User:
    """The user resolved by `SessionAuthMiddleware`, or an anonymous one."""
    return request.scope.get("user") or User()


CurrentUser = Annotated[User, Depends(get_user)]


def get_opaque(request: Request, state: State) -> "OpaqueParameters":
    from patzilla.navigator.opaquelinks import decode_opaque_parameters
    return decode_opaque_parameters(state.signer, request.query_params.get("op"))


Opaque = Annotated["OpaqueParameters", Depends(get_opaque)]


def get_vendor(request: Request, state: State):
    from patzilla.navigator.settings import effective_vendor
    return effective_vendor(state.vendor_settings, request.headers.get("host", "").split(":")[0])


Vendor = Annotated[t.Any, Depends(get_vendor)]


def get_runtime_settings(request: Request, state: State, user: CurrentUser, opaque: Opaque) -> "RuntimeSettings":
    from patzilla.navigator.settings import RuntimeSettings
    return RuntimeSettings(request=request, settings=state.global_settings, user=user, opaque=opaque)


Runtime = Annotated["RuntimeSettings", Depends(get_runtime_settings)]


def client_dependency(datasource: str, label: str):
    """Create a dependency providing the upstream client for a data source, using the user's credentials."""

    def get_client(state: State, user: CurrentUser, vendor: Vendor):
        client = state.client(datasource, user=user, vendor=vendor)
        if client is None:
            raise HTTPException(502, f"{label}: Data source not enabled or not configured")
        return client

    return get_client


def get_ops_client(state: State, user: CurrentUser, vendor: Vendor):
    from patzilla.access.epo.ops.client import UserBoundClient
    client = client_dependency("ops", "EPO OPS")(state, user, vendor)
    return UserBoundClient(client, userid=user.userid)


OpsClient = Annotated[t.Any, Depends(get_ops_client)]
IfiClaimsClient = Annotated[t.Any, Depends(client_dependency("ificlaims", "IFI CLAIMS"))]
DepaTechClient = Annotated[t.Any, Depends(client_dependency("depatech", "depa.tech"))]
SipClient = Annotated[t.Any, Depends(client_dependency("sip", "SIP"))]


async def get_params(request: Request) -> t.Dict[str, str]:
    """Query and form parameters, for endpoints accepting both GET and POST."""
    params = dict(request.query_params)
    if request.method == "POST" and request.headers.get("content-type", "").startswith(
            ("application/x-www-form-urlencoded", "multipart/form-data")):
        params.update((key, value) for key, value in (await request.form()).items() if isinstance(value, str))
    return params


Params = Annotated[t.Dict[str, str], Depends(get_params)]


def prefers_xml(request: Request) -> bool:
    """Whether the client prefers XML over JSON, according to the `Accept` header. Defaults to JSON."""
    quality = {"xml": 0.0, "json": 0.0}
    for item in request.headers.get("accept", "").split(","):
        media_type, _, params = item.strip().partition(";")
        q = 1.0
        for param in params.split(";"):
            key, _, value = param.strip().partition("=")
            if key == "q":
                try:
                    q = float(value)
                except ValueError:
                    q = 0.0
        if media_type in ("text/xml", "application/xml"):
            quality["xml"] = max(quality["xml"], q)
        elif media_type == "application/json":
            quality["json"] = max(quality["json"], q)
    return quality["xml"] > quality["json"]
