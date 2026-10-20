from fastapi import Request
from fastapi.responses import JSONResponse

from app.domain.errors import (
    Conflict,
    Forbidden,
    InvalidInput,
    NotFound,
    PayloadTooLarge,
)


def not_found_handler(request: Request, exception: NotFound) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exception)})


def conflict_handler(request: Request, exception: Conflict) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exception)})


def invalid_input_handler(request: Request, exception: InvalidInput) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exception)})


def forbidden_handler(request: Request, exception: Forbidden) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": str(exception)})


def payload_too_large_handler(
    request: Request, exception: PayloadTooLarge
) -> JSONResponse:
    return JSONResponse(status_code=413, content={"detail": str(exception)})
