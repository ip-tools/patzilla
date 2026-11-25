# -*- coding: utf-8 -*-
# (c) 2026 Andreas Motl <andreas.motl@ip-tools.org>
"""
Access to the current request and application registry from anywhere in the code base.

This replaces ``pyramid.threadlocal``. Instead of thread-local storage, it uses
``contextvars``, which are propagated correctly into the worker threads Starlette
uses to run synchronous request handlers.

For command line programs and software tests, there is no HTTP request in flight.
For those, ``app_context()`` designates a process-wide default request and registry,
mimicking ``pyramid.paster.bootstrap``.
"""
import contextlib
import typing as t
from contextvars import ContextVar

if t.TYPE_CHECKING:  # pragma: no cover
    from patzilla.web.registry import Registry
    from patzilla.web.request import Request


_current_request: ContextVar[t.Optional["Request"]] = ContextVar("patzilla_current_request", default=None)

# Process-wide defaults, only used by command line programs and software tests.
_default_request: t.Optional["Request"] = None
_default_registry: t.Optional["Registry"] = None


def get_current_request() -> t.Any:
    """
    Return the request currently being processed, or ``None``.
    """
    request = _current_request.get()
    if request is None:
        request = _default_request
    return request


def get_current_registry() -> t.Any:
    """
    Return the application registry of the request currently being processed,
    or the process-wide default registry.
    """
    request = get_current_request()
    registry = getattr(request, "registry", None)
    if registry is None:
        registry = _default_registry
    return registry


@contextlib.contextmanager
def request_context(request: "Request") -> t.Iterator["Request"]:
    """
    Designate the current request within the managed block.
    """
    token = _current_request.set(request)
    try:
        yield request
    finally:
        _current_request.reset(token)


def set_defaults(request: t.Optional["Request"] = None, registry: t.Optional["Registry"] = None) -> None:
    """
    Designate process-wide default request and registry objects.
    Only use this for command line programs and software tests.
    """
    global _default_request, _default_registry
    _default_request = request
    _default_registry = registry
