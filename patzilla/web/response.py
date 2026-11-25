# -*- coding: utf-8 -*-
# (c) 2026 Andreas Motl <andreas.motl@ip-tools.org>
"""
Response objects with a WebOb-compatible surface.

Request handlers historically mutate ``request.response`` (status, headers,
content type) or return response objects. This module provides a small,
framework-neutral response model for that purpose, which is converted into
a Starlette response at the edge, see ``ResponseMixin.to_starlette``.
"""
import datetime
import json
import typing as t
from email.utils import format_datetime
from http import HTTPStatus
from http.cookies import SimpleCookie
from urllib.parse import urljoin

from starlette.datastructures import MutableHeaders
from starlette.responses import Response as StarletteResponse

# Content types for which a ``charset`` parameter is emitted by default.
_CHARSET_CONTENT_TYPES = (
    "application/javascript",
    "application/xml",
    "application/xhtml+xml",
)


def status_reason(code: int) -> str:
    try:
        return HTTPStatus(code).phrase
    except ValueError:
        return "Unknown"


def parse_status(status: t.Union[int, str]) -> int:
    """
    Accept both ``404`` and ``"404 Not Found"``.
    """
    if isinstance(status, int):
        return status
    return int(str(status).strip().split(" ", 1)[0])


def make_location_absolute(location: str, base_url: str) -> str:
    if "://" in location:
        return location
    if location.startswith("//"):
        return base_url.split(":", 1)[0] + ":" + location
    return urljoin(base_url, location)


def format_set_cookie(
    name: str,
    value: str = "",
    max_age: t.Optional[t.Union[int, datetime.timedelta]] = None,
    path: t.Optional[str] = "/",
    domain: t.Optional[str] = None,
    secure: bool = False,
    httponly: bool = False,
    expires: t.Optional[t.Union[datetime.datetime, int]] = None,
    samesite: t.Optional[str] = None,
) -> str:
    """
    Format a ``Set-Cookie`` header value. Modelled after Starlette's ``Response.set_cookie``.
    """
    if value == "" and max_age == 0:
        # Deletion: Use the same format as WebOb, without quoting the empty value.
        parts = [f"{name}=", "Max-Age=0"]
        if path is not None:
            parts.append(f"Path={path}")
        if domain is not None:
            parts.append(f"Domain={domain}")
        parts.append("expires=Wed, 31-Dec-97 23:59:59 GMT")
        if secure:
            parts.append("Secure")
        if httponly:
            parts.append("HttpOnly")
        if samesite is not None:
            parts.append(f"SameSite={samesite}")
        return "; ".join(parts)
    cookie: SimpleCookie = SimpleCookie()
    cookie[name] = value
    if max_age is not None:
        if isinstance(max_age, datetime.timedelta):
            max_age = int(max_age.total_seconds())
        cookie[name]["max-age"] = max_age
    if expires is not None:
        if isinstance(expires, datetime.datetime):
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=datetime.timezone.utc)
            cookie[name]["expires"] = format_datetime(expires, usegmt=True)
        else:
            cookie[name]["expires"] = expires
    if path is not None:
        cookie[name]["path"] = path
    if domain is not None:
        cookie[name]["domain"] = domain
    if secure:
        cookie[name]["secure"] = True
    if httponly:
        cookie[name]["httponly"] = True
    if samesite is not None:
        if samesite.lower() not in ("strict", "lax", "none"):
            raise ValueError("samesite must be either 'strict', 'lax' or 'none'")
        cookie[name]["samesite"] = samesite
    return cookie.output(header="").strip()


class ResponseMixin:
    """
    The WebOb-compatible response surface shared by ``Response`` and HTTP exceptions.
    """

    default_content_type = "text/html"
    default_charset = "UTF-8"

    status_code: int
    headers: MutableHeaders
    _body: bytes
    _content_type: t.Optional[str]
    _charset: t.Optional[str]
    _charset_explicit: bool

    def _init_response(
        self,
        status: t.Union[int, str] = 200,
        headers: t.Optional[t.Union[t.Mapping[str, str], t.Iterable[t.Tuple[str, str]]]] = None,
        content_type: t.Optional[str] = None,
        charset: t.Optional[str] = None,
    ) -> None:
        self.status_code = parse_status(status)
        self.headers = MutableHeaders(raw=[])
        if headers:
            items = headers.items() if isinstance(headers, t.Mapping) else headers
            for key, value in items:
                self.headers.append(key, value)
        self._body = b""
        self._content_type = content_type or self.default_content_type
        self._charset = charset or self.default_charset
        self._charset_explicit = charset is not None

    # Status.
    @property
    def status(self) -> str:
        return f"{self.status_code} {status_reason(self.status_code)}"

    @status.setter
    def status(self, value: t.Union[int, str]) -> None:
        self.status_code = parse_status(value)

    @property
    def status_int(self) -> int:
        return self.status_code

    @status_int.setter
    def status_int(self, value: int) -> None:
        self.status_code = int(value)

    # Content type and charset.
    @property
    def content_type(self) -> t.Optional[str]:
        return self._content_type

    @content_type.setter
    def content_type(self, value: t.Optional[str]) -> None:
        if value and ";" in value:
            value, params = value.split(";", 1)
            for param in params.split(";"):
                key, _, param_value = param.strip().partition("=")
                if key.lower() == "charset" and param_value:
                    self.charset = param_value.strip('"')
        self._content_type = value.strip() if value else None

    @property
    def charset(self) -> t.Optional[str]:
        return self._charset

    @charset.setter
    def charset(self, value: t.Optional[str]) -> None:
        self._charset = value
        self._charset_explicit = value is not None

    @property
    def content_type_header(self) -> t.Optional[str]:
        content_type = self._content_type
        if not content_type:
            return None
        wants_charset = (
            self._charset_explicit
            or content_type.startswith("text/")
            or content_type in _CHARSET_CONTENT_TYPES
        )
        if self._charset and wants_charset:
            return f"{content_type}; charset={self._charset}"
        return content_type

    # Body.
    @property
    def body(self) -> bytes:
        return self._body

    @body.setter
    def body(self, value: t.Union[bytes, bytearray, memoryview]) -> None:
        self._body = bytes(value)

    @property
    def text(self) -> str:
        return self._body.decode(self._charset or "UTF-8")

    @text.setter
    def text(self, value: str) -> None:
        self._body = value.encode(self._charset or "UTF-8")

    @property
    def has_body(self) -> bool:
        return bool(self._body)

    @property
    def json(self) -> t.Any:
        return json.loads(self._body.decode(self._charset or "UTF-8"))

    json_body = json

    # Headers.
    @property
    def location(self) -> t.Optional[str]:
        return self.headers.get("Location")

    @location.setter
    def location(self, value: t.Optional[str]) -> None:
        if "Location" in self.headers:
            del self.headers["Location"]
        if value is not None:
            self.headers["Location"] = value

    # Cookies.
    def set_cookie(
        self,
        name: str,
        value: t.Optional[str] = "",
        max_age: t.Optional[t.Union[int, datetime.timedelta]] = None,
        path: str = "/",
        domain: t.Optional[str] = None,
        secure: bool = False,
        httponly: bool = False,
        comment: t.Optional[str] = None,
        expires: t.Optional[t.Union[datetime.datetime, int]] = None,
        overwrite: bool = False,
        samesite: t.Optional[str] = None,
    ) -> None:
        """
        Add a ``Set-Cookie`` header. The signature follows ``webob.Response.set_cookie``.
        """
        if overwrite:
            self.unset_cookie(name, strict=False)
        if value is None:
            value = ""
            max_age = 0
        header = format_set_cookie(
            name, value, max_age=max_age, path=path, domain=domain, secure=secure,
            httponly=httponly, expires=expires, samesite=samesite,
        )
        self.headers.append("Set-Cookie", header)

    def delete_cookie(self, name: str, path: str = "/", domain: t.Optional[str] = None) -> None:
        """
        Instruct the client to drop the cookie. The signature follows ``webob.Response.delete_cookie``.
        """
        self.set_cookie(name, None, path=path, domain=domain)

    def unset_cookie(self, name: str, strict: bool = True) -> None:
        """
        Remove all ``Set-Cookie`` headers for the given cookie name from this response.
        """
        keep = []
        found = False
        for key, value in self.headers.raw:
            if key.lower() == b"set-cookie" and value.decode("latin-1").split("=", 1)[0].strip() == name:
                found = True
                continue
            keep.append((key, value))
        if strict and not found:
            raise KeyError(name)
        self.headers.raw[:] = keep

    # Conversion.
    def prepare(self, accept: t.Optional[str] = None) -> None:
        """
        Hook for subclasses to compute a body before it is sent. See ``HTTPException``.
        """

    def to_starlette(self, accept: t.Optional[str] = None, base_url: t.Optional[str] = None) -> StarletteResponse:
        """
        Convert into a Starlette response. Like WebOb, relative ``Location`` headers
        are made absolute, resolved against ``base_url``, the URL of the request.
        """
        self.prepare(accept=accept)
        response = StarletteResponse(content=self._body, status_code=self.status_code)
        raw_headers = []
        for key, value in self.headers.raw:
            if key.lower() in (b"content-type", b"content-length"):
                continue
            if key.lower() == b"location" and base_url:
                value = make_location_absolute(value.decode("latin-1"), base_url).encode("latin-1")
            raw_headers.append((key, value))
        content_type = self.headers.get("Content-Type") or self.content_type_header
        if content_type:
            raw_headers.append((b"content-type", content_type.encode("latin-1")))
        body_allowed = self.status_code >= 200 and self.status_code not in (204, 304)
        if body_allowed:
            raw_headers.append((b"content-length", str(len(self._body)).encode("latin-1")))
        response.raw_headers = raw_headers
        return response


class Response(ResponseMixin):
    """
    A response object with a ``webob.Response``-compatible constructor.
    """

    def __init__(
        self,
        body: t.Optional[t.Union[bytes, str]] = None,
        status: t.Union[int, str] = 200,
        headerlist: t.Optional[t.Iterable[t.Tuple[str, str]]] = None,
        content_type: t.Optional[str] = None,
        charset: t.Optional[str] = None,
        text: t.Optional[str] = None,
        json_body: t.Any = None,
        headers: t.Optional[t.Mapping[str, str]] = None,
        **kwargs: t.Any,
    ):
        if json_body is not None:
            content_type = content_type or "application/json"
        self._init_response(status=status, headers=headers or headerlist, content_type=content_type, charset=charset)
        if isinstance(body, str):
            self.text = body
        elif body is not None:
            self.body = body
        if text is not None:
            self.text = text
        if json_body is not None:
            self.body = json.dumps(json_body).encode("utf-8")
        for key, value in kwargs.items():
            setattr(self, key, value)


class StarletteResponseAdapter:
    """
    Wrap a native Starlette response, offering the WebOb-compatible cookie
    interface to response callbacks.
    """

    def __init__(self, response: StarletteResponse):
        self.response = response

    @property
    def headers(self) -> MutableHeaders:
        return self.response.headers

    @property
    def status_code(self) -> int:
        return self.response.status_code

    def set_cookie(self, name: str, value: t.Optional[str] = "", max_age=None, path="/", domain=None,
                   secure=False, httponly=False, comment=None, expires=None, overwrite=False, samesite=None) -> None:
        if value is None:
            value, max_age = "", 0
        header = format_set_cookie(
            name, value, max_age=max_age, path=path, domain=domain, secure=secure,
            httponly=httponly, expires=expires, samesite=samesite,
        )
        self.response.raw_headers.append((b"set-cookie", header.encode("latin-1")))

    def delete_cookie(self, name: str, path: str = "/", domain: t.Optional[str] = None) -> None:
        self.set_cookie(name, None, path=path, domain=domain)
