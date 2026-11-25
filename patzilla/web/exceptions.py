# -*- coding: utf-8 -*-
# (c) 2026 Andreas Motl <andreas.motl@ip-tools.org>
"""
HTTP exceptions, which are also responses.

This is a drop-in replacement for the subset of ``pyramid.httpexceptions``
used by PatZilla. Like with Pyramid, request handlers can either raise or
return them. Their default body is negotiated using the ``Accept`` header
(HTML, JSON, or plain text), matching Pyramid's output.
"""
import json
import typing as t
from html import escape as _html_escape
from string import Template

from patzilla.web.accept import Accept
from patzilla.web.response import ResponseMixin


class HTTPException(ResponseMixin, Exception):
    code = 520
    title = "Unknown Error"
    explanation = ""
    empty_body = False

    body_template_obj = Template("""\
${explanation}${br}${br}
${detail}
${html_comment}
""")

    plain_template_obj = Template("""\
${status}

${body}""")

    html_template_obj = Template("""\
<html>
 <head>
  <title>${status}</title>
 </head>
 <body>
  <h1>${status}</h1>
  ${body}
 </body>
</html>""")

    def __init__(
        self,
        detail: t.Any = None,
        headers: t.Optional[t.Union[t.Mapping[str, str], t.Iterable[t.Tuple[str, str]]]] = None,
        comment: t.Optional[str] = None,
        body_template: t.Optional[str] = None,
        json_formatter: t.Optional[t.Callable[..., t.Any]] = None,
        **kw: t.Any,
    ):
        Exception.__init__(self, detail)
        self._init_response(status=self.code, headers=headers, content_type=kw.pop("content_type", None),
                            charset=kw.pop("charset", None))
        self.detail = self.message = detail
        self.comment = comment
        if body_template is not None:
            self.body_template_obj = Template(body_template)
        if json_formatter is not None:
            self._json_formatter = json_formatter  # type: ignore[method-assign]
        body = kw.pop("body", None)
        text = kw.pop("text", None)
        json_body = kw.pop("json_body", None)
        if body is not None:
            self.body = body.encode("utf-8") if isinstance(body, str) else body
        if text is not None:
            self.text = text
        if json_body is not None:
            self.content_type = "application/json"
            self.body = json.dumps(json_body).encode("utf-8")
        for key, value in kw.items():
            setattr(self, key, value)

    def __str__(self) -> str:
        return str(self.detail) if self.detail else self.explanation

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} at {hex(id(self))} {self.status}>"

    def _json_formatter(self, status: str, body: str, title: str, environ: t.Any) -> t.Dict[str, t.Any]:
        return {"message": body, "code": status, "title": self.title}

    def _template_args(self) -> t.Dict[str, str]:
        return {}

    def prepare(self, accept: t.Optional[str] = None) -> None:
        """
        Compute the default body, unless an explicit body has been assigned.
        """
        if self.has_body or self.empty_body:
            return

        comment = self.comment or ""
        # Like Pyramid, a missing or empty ``Accept`` header yields plain text.
        acceptable = []
        if accept:
            acceptable = [offer for offer, _ in Accept(accept).acceptable_offers(["text/html", "application/json"])]
        match = (acceptable + ["text/plain"])[0]

        html_comment = ""
        if match == "text/html":
            self._content_type, self._charset = "text/html", "UTF-8"
            escape: t.Callable[[str], str] = _html_escape
            br = "<br/>"
            if comment:
                html_comment = "<!-- %s -->" % escape(comment)
        elif match == "application/json":
            self._content_type, self._charset = "application/json", None
            escape = str
            br = "\n"
            html_comment = comment
        else:
            self._content_type, self._charset = "text/plain", "UTF-8"
            escape = str
            br = "\n"
            html_comment = comment

        args = {
            "br": br,
            "explanation": escape(self.explanation),
            "detail": escape(str(self.detail or "")),
            "comment": escape(comment),
            "html_comment": html_comment,
        }
        args.update({key: escape(value) for key, value in self._template_args().items()})
        body = self.body_template_obj.substitute(args)

        if match == "application/json":
            page = json.dumps(self._json_formatter(status=self.status, body=body, title=self.title, environ=None))
        elif match == "text/html":
            page = self.html_template_obj.substitute(status=self.status, body=body)
        else:
            page = self.plain_template_obj.substitute(status=self.status, body=body)
        self._body = page.encode("UTF-8")


class HTTPError(HTTPException):
    pass


class HTTPRedirection(HTTPException):
    pass


class _HTTPMove(HTTPRedirection):
    explanation = "The resource has been moved to"
    body_template_obj = Template("""\
${explanation} ${location}; you should be redirected automatically.
${detail}
${html_comment}""")

    def __init__(self, location: str = "", detail: t.Any = None, headers=None, comment=None, body_template=None, **kw):
        if location is None:
            raise ValueError("HTTP redirects need a location to redirect to.")
        super().__init__(detail=detail, headers=headers, comment=comment, body_template=body_template, **kw)
        self.location = location

    def _template_args(self) -> t.Dict[str, str]:
        return {"location": self.location or ""}


class HTTPFound(_HTTPMove):
    code = 302
    title = "Found"
    explanation = "The resource was found at"


class HTTPSeeOther(_HTTPMove):
    code = 303
    title = "See Other"


class HTTPTemporaryRedirect(_HTTPMove):
    code = 307
    title = "Temporary Redirect"


class HTTPClientError(HTTPError):
    code = 400
    title = "Bad Request"


class HTTPBadRequest(HTTPClientError):
    explanation = "The server could not comply with the request since it is either malformed or otherwise incorrect."


class HTTPUnauthorized(HTTPClientError):
    code = 401
    title = "Unauthorized"
    explanation = (
        "This server could not verify that you are authorized to access the document you requested.  "
        "Either you supplied the wrong credentials (e.g., bad password), or your browser does not "
        "understand how to supply the credentials required."
    )


class HTTPForbidden(HTTPClientError):
    code = 403
    title = "Forbidden"
    explanation = "Access was denied to this resource."


class HTTPNotFound(HTTPClientError):
    code = 404
    title = "Not Found"
    explanation = "The resource could not be found."


class HTTPMethodNotAllowed(HTTPClientError):
    code = 405
    title = "Method Not Allowed"
    body_template_obj = Template("""\
The method ${REQUEST_METHOD} is not allowed for this resource. ${br}${br}
${detail}""")

    def __init__(self, *args: t.Any, request_method: str = "", **kw: t.Any):
        super().__init__(*args, **kw)
        self.request_method = request_method

    def _template_args(self) -> t.Dict[str, str]:
        return {"REQUEST_METHOD": self.request_method}


class HTTPNotAcceptable(HTTPClientError):
    code = 406
    title = "Not Acceptable"


class HTTPTooManyRequests(HTTPClientError):
    code = 429
    title = "Too Many Requests"
    explanation = "The action could not be performed because there were too many requests by the client."


class HTTPServerError(HTTPError):
    code = 500
    title = "Internal Server Error"


class HTTPInternalServerError(HTTPServerError):
    explanation = "The server has either erred or is incapable of performing the requested operation."


class HTTPBadGateway(HTTPServerError):
    code = 502
    title = "Bad Gateway"
    explanation = "Bad gateway."


class HTTPServiceUnavailable(HTTPServerError):
    code = 503
    title = "Service Unavailable"
    explanation = "The server is currently unavailable. Please try again at a later time."
