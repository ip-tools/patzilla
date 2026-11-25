# -*- coding: utf-8 -*-
# (c) 2017-2026 Andreas Motl <andreas.motl@ip-tools.org>
"""
Error accumulation and the JSON error envelope for API services.

The frontend expects errors in the format established by Cornice::

    {"status": "error", "errors": [{"location": ..., "name": ..., "description": ...}]}

Request handlers add errors to ``request.errors``. When the error list is
not empty after the handler returns, the service responds with the envelope
above, using ``request.errors.status`` as HTTP status code (default: 400).
"""
import json
import typing as t

from patzilla.web.exceptions import HTTPError


class Errors(list):
    """
    Holds errors reported while processing a request. Compatible with ``cornice.errors.Errors``.

    Other than Cornice, any label is accepted as ``location``, because it is used
    to convey the origin of an error throughout PatZilla.
    """

    def __init__(self, status: int = 400):
        super().__init__()
        self.status = status

    def add(self, location: str, name: t.Optional[str] = None, description: t.Any = None, **kw: t.Any) -> None:
        self.append(dict(location=location, name=name, description=description, **kw))


class JSONError(HTTPError):
    """
    An HTTP error response carrying the JSON error envelope. Compatible with ``cornice.renderer.JSONError``.
    """

    code = 400
    title = "Bad Request"

    def __init__(self, errors: t.Iterable[t.Dict[str, t.Any]], status: int = 400,
                 serializer: t.Callable[..., str] = json.dumps, serializer_kw: t.Optional[t.Dict[str, t.Any]] = None):
        super().__init__()
        self.errors = list(errors)
        body = {"status": "error", "errors": self.errors}
        self.body = serializer(body, **(serializer_kw or {})).encode("utf-8")
        self.status = status
        self.content_type = "application/json"
        self._charset = None
        self._charset_explicit = False


def json_error(request: t.Any) -> JSONError:
    """
    Build a ``JSONError`` from the errors recorded on the request.

    Upstream responses may carry their content as bytes, which is decoded here.
    """
    for error in request.errors:
        description = error.get("description")
        if isinstance(description, dict) and isinstance(description.get("content"), bytes):
            description["content"] = description["content"].decode("utf-8")
    return JSONError(errors=request.errors)
