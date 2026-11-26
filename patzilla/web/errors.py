# -*- coding: utf-8 -*-
# (c) 2026 Andreas Motl <andreas.motl@ip-tools.org>
"""
Error responses. API errors use the JSON envelope the frontend expects, see `ServiceError`.
"""
import logging
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.exceptions import HTTPException

from patzilla.access.generic.exceptions import ServiceError

log = logging.getLogger(__name__)


def is_api_request(request: Request) -> bool:
    return request.url.path.startswith("/api/")


def envelope(errors, status_code: int) -> JSONResponse:
    return JSONResponse({"status": "error", "errors": list(errors)}, status_code=status_code)


async def service_error_handler(request: Request, exc: ServiceError):
    return envelope(exc.errors, exc.status_code)


async def http_error_handler(request: Request, exc: HTTPException):
    title = HTTPStatus(exc.status_code).phrase
    if is_api_request(request):
        response = envelope([{"location": "http", "name": title, "description": str(exc.detail)}], exc.status_code)
    else:
        response = PlainTextResponse(f"{exc.status_code} {title}\n\n{exc.detail}", status_code=exc.status_code)
    for key, value in (exc.headers or {}).items():
        response.headers[key] = value
    return response


async def validation_error_handler(request: Request, exc: RequestValidationError):
    errors = [
        {"location": str(error["loc"][0]), "name": str(error["loc"][-1]), "description": error["msg"]}
        for error in exc.errors()
    ]
    return envelope(errors, 400)


def install_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ServiceError, service_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(HTTPException, http_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
