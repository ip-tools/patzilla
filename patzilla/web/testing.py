# -*- coding: utf-8 -*-
# (c) 2026 Andreas Motl <andreas.motl@ip-tools.org>
"""
Utilities for software tests, the replacement for ``pyramid.testing``.
"""
import copy
import json as _json
import typing as t
from urllib.parse import urlencode

from patzilla.web.context import get_current_registry
from patzilla.web.registry import Registry
from patzilla.web.request import MultiDict, Request


def fresh_registry() -> Registry:
    """
    Provide a registry for a test request. When an application environment is active,
    its settings and service objects are inherited, without sharing the registry itself.
    """
    current = get_current_registry()
    if current is None:
        return Registry()
    return copy.copy(current)


class DummyRequest(Request):
    """
    A request object without an HTTP connection, with an interface
    similar to ``pyramid.testing.DummyRequest``.

    - ``params`` become query parameters, ``post`` become form parameters.
    - ``json`` or ``json_body`` become the JSON request body.
    - Additional keyword arguments are assigned as attributes.
    """

    def __init__(
        self,
        params: t.Optional[t.Mapping[str, t.Any]] = None,
        post: t.Optional[t.Mapping[str, t.Any]] = None,
        json: t.Any = None,
        json_body: t.Any = None,
        headers: t.Optional[t.Mapping[str, str]] = None,
        cookies: t.Optional[t.Mapping[str, str]] = None,
        matchdict: t.Optional[t.Dict[str, t.Any]] = None,
        path: str = "/",
        method: t.Optional[str] = None,
        host: str = "example.com:80",
        body: t.Optional[bytes] = None,
        content_type: t.Optional[str] = None,
        registry: t.Optional[Registry] = None,
        **kwargs: t.Any,
    ):
        payload = json if json is not None else json_body
        if method is None:
            method = "POST" if post is not None or payload is not None or body is not None else "GET"
        query_string = urlencode(list(MultiDict(params).items())) if params else ""

        super().__init__(
            method=method,
            path=path,
            query_string=query_string,
            host=host,
            headers=headers,
            cookies=cookies,
            matchdict=matchdict,
            registry=registry if registry is not None else fresh_registry(),
        )
        if content_type is not None:
            self.content_type = content_type
        if payload is not None:
            if content_type is None:
                self.content_type = "application/json"
            self.body = _json.dumps(payload).encode("utf-8")
        if body is not None:
            self.body = body
        if params is not None:
            self.GET = MultiDict(params)
        if post is not None:
            self.POST = MultiDict(post)
        for key, value in kwargs.items():
            setattr(self, key, value)
