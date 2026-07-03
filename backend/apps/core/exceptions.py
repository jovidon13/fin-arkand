"""
Unified error contract: every API error is ``{code, message, details}``
(design doc §07). Domain code raises :class:`DomainError`; DRF's default
exceptions are reshaped by :func:`custom_exception_handler`.
"""
from __future__ import annotations

from typing import Any

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


class DomainError(Exception):
    """Business-rule violation raised from services/selectors.

    Example: ``raise DomainError("cash_limit_exceeded", "Превышен лимит кассы")``.
    """

    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, code: str, message: str, *, details: Any = None,
                 status_code: int | None = None) -> None:
        self.code = code
        self.message = message
        self.details = details or {}
        if status_code is not None:
            self.status_code = status_code
        super().__init__(message)


def _envelope(code: str, message: str, details: Any = None) -> dict:
    return {"code": code, "message": message, "details": details or {}}


def custom_exception_handler(exc: Exception, context: dict) -> Response | None:
    if isinstance(exc, DomainError):
        return Response(
            _envelope(exc.code, exc.message, exc.details),
            status=exc.status_code,
        )

    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    data = response.data
    # Map DRF's shapes into the unified envelope.
    if isinstance(data, dict) and {"code", "message"} <= set(data.keys()):
        return response  # already in our shape

    code = "error"
    message = "Ошибка запроса"
    details: Any = data

    if isinstance(data, dict):
        detail = data.get("detail")
        if detail is not None:
            message = str(detail)
            details = {k: v for k, v in data.items() if k != "detail"}
        else:
            message = "Ошибка валидации"
            code = "validation_error"
    elif isinstance(data, list):
        message = "Ошибка валидации"
        code = "validation_error"

    # Refine common status codes.
    status_map = {
        status.HTTP_401_UNAUTHORIZED: "not_authenticated",
        status.HTTP_403_FORBIDDEN: "permission_denied",
        status.HTTP_404_NOT_FOUND: "not_found",
        status.HTTP_405_METHOD_NOT_ALLOWED: "method_not_allowed",
        status.HTTP_429_TOO_MANY_REQUESTS: "throttled",
    }
    code = status_map.get(response.status_code, code)

    response.data = _envelope(code, message, details)
    return response
