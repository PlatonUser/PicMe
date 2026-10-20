import pytest
from fastapi import Request

from app.domain.errors import (
    Conflict,
    Forbidden,
    InvalidInput,
    NotFound,
    PayloadTooLarge,
)
from app.infrastructure.web.errors import (
    conflict_handler,
    forbidden_handler,
    invalid_input_handler,
    not_found_handler,
    payload_too_large_handler,
)


@pytest.mark.parametrize(
    ("exception", "handler", "status_code"),
    [
        (NotFound, not_found_handler, 404),
        (Conflict, conflict_handler, 409),
        (InvalidInput, invalid_input_handler, 422),
        (Forbidden, forbidden_handler, 403),
        (PayloadTooLarge, payload_too_large_handler, 413),
    ],
)
def test_domain_error_handler_maps_exception_to_json_response(
    exception, handler, status_code
):
    response = handler(Request(scope={"type": "http"}), exception("problem"))

    assert response.status_code == status_code
    assert response.body == b'{"detail":"problem"}'
