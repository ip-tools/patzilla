# -*- coding: utf-8 -*-
# (c) 2026 Andreas Motl <andreas.motl@ip-tools.org>
"""
The request object handed to PatZilla's request handlers.

It wraps a Starlette request and offers the WebOb-compatible surface used
throughout the code base (``params``, ``matchdict``, ``json``, ``host_url``,
``client_addr``, ``response``, ``errors``, ...). Request handlers are synchronous
and run within a worker thread, so the body is read upfront, see
``patzilla.web.routing``.

Request objects can also be created without an HTTP connection, for command
line programs and software tests, see ``patzilla.web.testing.DummyRequest``.
"""
import typing as t
from urllib.parse import parse_qsl, quote

import simplejson
from starlette.datastructures import Headers, MutableHeaders
from starlette.requests import Request as StarletteRequest
from starlette.requests import cookie_parser

from patzilla.web.accept import Accept
from patzilla.web.errors import Errors
from patzilla.web.response import Response

if t.TYPE_CHECKING:  # pragma: no cover
    from patzilla.web.registry import Registry


FORM_CONTENT_TYPES = ("application/x-www-form-urlencoded", "multipart/form-data")
# Characters not quoted within URL paths, like WebOb.
PATH_SAFE = "/~!$&'()*+,;=:@"
FORM_METHODS = ("POST", "PUT", "PATCH", "DELETE")


class MultiDict(t.MutableMapping[str, t.Any]):
    """
    An ordered dictionary that can hold multiple values per key.
    Compatible with ``webob.multidict.MultiDict``: Item access returns the last value.
    """

    def __init__(self, *args: t.Any, **kwargs: t.Any):
        self._items: t.List[t.Tuple[str, t.Any]] = []
        if args:
            source = args[0]
            if hasattr(source, "items") and callable(source.items):
                if isinstance(source, MultiDict):
                    self._items = list(source.items())
                else:
                    self._items = list(source.items())
            else:
                self._items = list(source)
        if kwargs:
            self._items.extend(kwargs.items())

    def __getitem__(self, key: str) -> t.Any:
        for item_key, value in reversed(self._items):
            if item_key == key:
                return value
        raise KeyError(key)

    def __setitem__(self, key: str, value: t.Any) -> None:
        self._items = [(item_key, item_value) for item_key, item_value in self._items if item_key != key]
        self._items.append((key, value))

    def __delitem__(self, key: str) -> None:
        items = [(item_key, item_value) for item_key, item_value in self._items if item_key != key]
        if len(items) == len(self._items):
            raise KeyError(key)
        self._items = items

    def __iter__(self) -> t.Iterator[str]:
        for key, _ in self._items:
            yield key

    def __len__(self) -> int:
        return len(self._items)

    def __contains__(self, key: object) -> bool:
        return any(item_key == key for item_key, _ in self._items)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._items!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, MultiDict):
            return self._items == list(other.items())
        if isinstance(other, t.Mapping):
            return dict(self.items()) == dict(other.items())
        return NotImplemented

    def keys(self) -> t.List[str]:  # type: ignore[override]
        return [key for key, _ in self._items]

    def values(self) -> t.List[t.Any]:  # type: ignore[override]
        return [value for _, value in self._items]

    def items(self) -> t.List[t.Tuple[str, t.Any]]:  # type: ignore[override]
        return list(self._items)

    def add(self, key: str, value: t.Any) -> None:
        self._items.append((key, value))

    def getall(self, key: str) -> t.List[t.Any]:
        return [value for item_key, value in self._items if item_key == key]

    def getone(self, key: str) -> t.Any:
        values = self.getall(key)
        if not values:
            raise KeyError(key)
        if len(values) > 1:
            raise KeyError(f"Multiple values match {key!r}: {values!r}")
        return values[0]

    def mixed(self) -> t.Dict[str, t.Any]:
        result: t.Dict[str, t.Any] = {}
        for key, value in self._items:
            if key in result:
                if isinstance(result[key], list):
                    result[key].append(value)
                else:
                    result[key] = [result[key], value]
            else:
                result[key] = value
        return result

    def dict_of_lists(self) -> t.Dict[str, t.List[t.Any]]:
        result: t.Dict[str, t.List[t.Any]] = {}
        for key, value in self._items:
            result.setdefault(key, []).append(value)
        return result

    def copy(self) -> "MultiDict":
        return MultiDict(self._items)


class NestedMultiDict(MultiDict):
    """
    A combined view on multiple ``MultiDict`` objects, like ``request.params``
    combines ``request.GET`` and ``request.POST``. Lookups try the first
    dictionary first. Compatible with ``webob.multidict.NestedMultiDict``.
    """

    def __init__(self, *dicts: MultiDict):
        super().__init__()
        self.dicts = list(dicts)

    @property  # type: ignore[override]
    def _items(self) -> t.List[t.Tuple[str, t.Any]]:
        items: t.List[t.Tuple[str, t.Any]] = []
        for nested in getattr(self, "dicts", []):
            items.extend(nested.items())
        return items

    @_items.setter
    def _items(self, value: t.List[t.Tuple[str, t.Any]]) -> None:
        # Mutations receive the combined items, so collapse into a single dictionary.
        if getattr(self, "dicts", None) is not None:
            self.dicts = [MultiDict(value)]

    def __getitem__(self, key: str) -> t.Any:
        for nested in self.dicts:
            if key in nested:
                return nested[key]
        raise KeyError(key)

    def _flat(self) -> MultiDict:
        if len(self.dicts) != 1:
            self.dicts = [MultiDict(self._items)]
        return self.dicts[0]

    def __setitem__(self, key: str, value: t.Any) -> None:
        self._flat()[key] = value

    def __delitem__(self, key: str) -> None:
        del self._flat()[key]

    def add(self, key: str, value: t.Any) -> None:
        self._flat().add(key, value)


class Request:
    """
    PatZilla's request object, see module docstring.
    """

    def __init__(
        self,
        method: str = "GET",
        path: str = "/",
        query_string: str = "",
        scheme: str = "http",
        host: str = "localhost:80",
        script_name: str = "",
        headers: t.Optional[t.Union[t.Mapping[str, str], Headers]] = None,
        cookies: t.Optional[t.Mapping[str, str]] = None,
        body: bytes = b"",
        remote_addr: t.Optional[str] = None,
        registry: t.Optional["Registry"] = None,
        matchdict: t.Optional[t.Dict[str, t.Any]] = None,
        form: t.Optional[MultiDict] = None,
        starlette_request: t.Optional[StarletteRequest] = None,
    ):
        self.method = method.upper()
        self.scheme = scheme
        self.script_name = script_name
        self.path_info = path
        self.query_string = query_string
        self.remote_addr = remote_addr
        self.registry = registry
        self.matchdict = matchdict if matchdict is not None else {}
        self.starlette_request = starlette_request
        self.response_callbacks: t.List[t.Callable[["Request", t.Any], None]] = []

        self.headers = MutableHeaders(raw=[])
        if headers:
            items = headers.raw if isinstance(headers, Headers) else [
                (key.lower().encode("latin-1"), str(value).encode("latin-1")) for key, value in headers.items()
            ]
            self.headers.raw.extend(items)
        if "host" not in self.headers:
            self.headers["Host"] = host

        if cookies is None:
            cookies = cookie_parser(self.headers.get("cookie", ""))
        self.cookies: t.Dict[str, str] = dict(cookies)

        self._body = body or b""
        self._form = form
        self._GET: t.Optional[MultiDict] = None
        self._POST: t.Optional[MultiDict] = None
        self._params: t.Optional[MultiDict] = None
        self._json: t.Any = _MISSING
        self._errors: t.Optional[Errors] = None
        self._response: t.Optional[Response] = None

    @classmethod
    def from_starlette(
        cls,
        request: StarletteRequest,
        body: bytes = b"",
        registry: t.Optional["Registry"] = None,
        form: t.Optional[MultiDict] = None,
    ) -> "Request":
        scope = request.scope
        root_path = scope.get("root_path", "")
        path = scope.get("path", "/")
        if root_path and path.startswith(root_path):
            path = path[len(root_path):] or "/"
        client = scope.get("client")
        return cls(
            method=request.method,
            path=path,
            query_string=scope.get("query_string", b"").decode("latin-1"),
            scheme=request.url.scheme,
            host=request.url.netloc,
            script_name=root_path,
            headers=request.headers,
            cookies=request.cookies,
            body=body,
            remote_addr=client[0] if client else None,
            registry=registry,
            matchdict=dict(request.path_params),
            form=form,
            starlette_request=request,
        )

    def __getattr__(self, name: str) -> t.Any:
        """
        Compute lazy request properties registered with ``Registry.add_request_method``.
        """
        if name.startswith("_"):
            raise AttributeError(name)
        registry = self.__dict__.get("registry")
        methods = getattr(registry, "request_methods", None) or {}
        if name in methods:
            value = methods[name](self)
            self.__dict__[name] = value
            return value
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")

    # URL properties, following WebOb.
    @property
    def host(self) -> str:
        return self.headers.get("Host", "")

    @property
    def domain(self) -> str:
        return self.host.split(":", 1)[0]

    @property
    def host_port(self) -> str:
        host = self.host
        if ":" in host:
            return host.split(":", 1)[1]
        return "443" if self.scheme == "https" else "80"

    @property
    def host_url(self) -> str:
        host = self.host
        port = None
        if ":" in host:
            host, port = host.split(":", 1)
        if (self.scheme == "https" and port == "443") or (self.scheme == "http" and port == "80"):
            port = None
        return f"{self.scheme}://{host}" + (f":{port}" if port else "")

    @property
    def application_url(self) -> str:
        return self.host_url + quote(self.script_name, safe=PATH_SAFE)

    @property
    def path(self) -> str:
        return quote(self.script_name, safe=PATH_SAFE) + quote(self.path_info, safe=PATH_SAFE)

    @property
    def path_url(self) -> str:
        return self.application_url + quote(self.path_info, safe=PATH_SAFE)

    @property
    def path_qs(self) -> str:
        return self.path + (f"?{self.query_string}" if self.query_string else "")

    @property
    def url(self) -> str:
        return self.path_url + (f"?{self.query_string}" if self.query_string else "")

    @property
    def client_addr(self) -> t.Optional[str]:
        """
        The effective client IP address. Like WebOb, use the first address
        of the ``X-Forwarded-For`` header, if present.
        """
        forwarded = self.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return self.remote_addr

    @property
    def accept(self) -> Accept:
        return Accept(self.headers.get("Accept"))

    # Body and content type.
    @property
    def content_type(self) -> str:
        return self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()

    @content_type.setter
    def content_type(self, value: str) -> None:
        if "content-type" in self.headers:
            del self.headers["Content-Type"]
        if value:
            self.headers["Content-Type"] = value
        self._invalidate()

    @property
    def charset(self) -> str:
        for param in self.headers.get("Content-Type", "").split(";")[1:]:
            key, _, value = param.strip().partition("=")
            if key.lower() == "charset" and value:
                return value.strip('"')
        return "UTF-8"

    @property
    def body(self) -> bytes:
        return self._body

    @body.setter
    def body(self, value: t.Union[bytes, str]) -> None:
        if isinstance(value, str):
            value = value.encode(self.charset)
        self._body = value
        self._form = None
        self._invalidate()

    @property
    def text(self) -> str:
        return self._body.decode(self.charset)

    @text.setter
    def text(self, value: str) -> None:
        self.body = value.encode(self.charset)

    @property
    def content_length(self) -> int:
        return len(self._body)

    @property
    def json(self) -> t.Any:
        if self._json is _MISSING:
            return simplejson.loads(self._body.decode(self.charset))
        return self._json

    @json.setter
    def json(self, value: t.Any) -> None:
        self._json = value

    json_body = json

    def _invalidate(self) -> None:
        self._POST = None
        self._params = None
        self._json = _MISSING

    # Request parameters.
    @property
    def GET(self) -> MultiDict:
        if self._GET is None:
            self._GET = MultiDict(parse_qsl(self.query_string, keep_blank_values=True))
        return self._GET

    @GET.setter
    def GET(self, value: t.Mapping[str, t.Any]) -> None:
        self._GET = value if isinstance(value, MultiDict) else MultiDict(value)
        self._params = None

    @property
    def POST(self) -> MultiDict:
        if self._POST is None:
            if self._form is not None:
                self._POST = self._form
            elif self.method in FORM_METHODS and self.content_type == "application/x-www-form-urlencoded":
                self._POST = MultiDict(parse_qsl(self._body.decode(self.charset), keep_blank_values=True))
            else:
                self._POST = MultiDict()
        return self._POST

    @POST.setter
    def POST(self, value: t.Mapping[str, t.Any]) -> None:
        self._POST = value if isinstance(value, MultiDict) else MultiDict(value)
        self._params = None

    @property
    def params(self) -> MultiDict:
        if self._params is None:
            self._params = NestedMultiDict(self.GET, self.POST)
        return self._params

    @params.setter
    def params(self, value: t.Mapping[str, t.Any]) -> None:
        self._params = value if isinstance(value, MultiDict) else MultiDict(value)

    # Response handling.
    @property
    def errors(self) -> Errors:
        if self._errors is None:
            self._errors = Errors()
        return self._errors

    @errors.setter
    def errors(self, value: Errors) -> None:
        self._errors = value

    @property
    def response(self) -> Response:
        """
        The response object request handlers can mutate (status, headers, content type).
        It is used when a handler returns data to be rendered, rather than a response.
        """
        if self._response is None:
            self._response = Response()
        return self._response

    @response.setter
    def response(self, value: Response) -> None:
        self._response = value

    def add_response_callback(self, callback: t.Callable[["Request", t.Any], None]) -> None:
        """
        Register a callable invoked with ``(request, response)`` before the response is sent.
        """
        self.response_callbacks.append(callback)

    def route_url(self, name: str, _query: t.Optional[t.Mapping[str, t.Any]] = None, **path_params: t.Any) -> str:
        if self.starlette_request is None:
            raise RuntimeError("URL generation needs a request bound to the application")
        url = str(self.starlette_request.url_for(name, **{key: str(value) for key, value in path_params.items()}))
        if _query:
            from urllib.parse import urlencode
            url += "?" + urlencode(_query)
        return url

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.method} {self.url}>"


class _Missing:
    def __repr__(self) -> str:
        return "<missing>"


_MISSING = _Missing()
