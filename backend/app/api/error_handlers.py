"""Converte exceções em respostas HTTP no formato ``ErrorResponse``.

As rotas não precisam de ``try/except``: o FastAPI entrega a exceção ao
tratador registrado para a classe dela ou para a classe base mais próxima.
"""

import logging
from collections.abc import Mapping, Sequence
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.schemas.error_schema import ErrorResponse
from app.services.exceptions import (
    DomainError,
    DuplicateOperatorError,
    DuplicateSubsetLinkError,
    NotFoundError,
)

logger = logging.getLogger(__name__)

# Erros de domínio fora desta lista respondem 422 (dados a corrigir).
# ``NotFoundError`` é 404 tanto para id na URL quanto no corpo.
_DOMAIN_STATUS: dict[type[DomainError], int] = {
    NotFoundError: 404,
    DuplicateOperatorError: 409,
    DuplicateSubsetLinkError: 409,
}
_DEFAULT_DOMAIN_STATUS = 422

_HTTP_ERRORS = {
    404: ("route_not_found", "Endereço não encontrado."),
    405: ("method_not_allowed", "Método não permitido para este endereço."),
}

# Tipo de erro do Pydantic -> mensagem. As chaves entre {} vêm de ``ctx``.
_VALIDATION_MESSAGES = {
    "missing": "Campo obrigatório.",
    "extra_forbidden": "Campo não permitido.",
    "json_invalid": "O corpo da requisição não é um JSON válido.",
    "enum": "Valor inválido. Use: {expected}.",
    "greater_than": "Deve ser maior que {gt}.",
    "string_type": "Deve ser um texto.",
    "string_too_short": "Deve ter no mínimo {min_length} caracteres.",
    "string_too_long": "Deve ter no máximo {max_length} caracteres.",
    "int_type": "Deve ser um número inteiro.",
    "int_parsing": "Deve ser um número inteiro.",
    "int_from_float": "Deve ser um número inteiro.",
    "list_type": "Deve ser uma lista.",
    "timezone_aware": "Informe o fuso horário, por exemplo 2026-09-14T11:30:00-03:00.",
    "datetime_parsing": "Data e hora inválidas.",
    "datetime_from_date_parsing": "Data e hora inválidas.",
    "model_attributes_type": "Deve ser um objeto JSON.",
}
_DEFAULT_VALIDATION_MESSAGE = "Valor inválido."


def register_error_handlers(app: FastAPI) -> None:
    """Registra os tratadores; deve ser chamada ao criar o ``app``."""
    app.add_exception_handler(DomainError, _handle_domain_error)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(HTTPException, _handle_http_exception)
    app.add_exception_handler(Exception, _handle_unexpected_error)


def _error_response(
    status: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    body = ErrorResponse(code=code, message=message, details=details or {})
    return JSONResponse(body.model_dump(), status_code=status, headers=headers)


def _handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
    status = _DOMAIN_STATUS.get(type(exc), _DEFAULT_DOMAIN_STATUS)
    return _error_response(status, exc.code, str(exc), exc.details)


def _handle_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = [
        {"field": _field_name(error), "message": _validation_message(error)}
        for error in exc.errors()
    ]
    return _error_response(
        422, "validation_error", "Confira os campos informados.", {"errors": errors}
    )


def _handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    """Erros do próprio framework, como rota inexistente (404) e método (405)."""
    code, message = _HTTP_ERRORS.get(
        exc.status_code, ("http_error", "Não foi possível processar a requisição.")
    )
    # Os cabeçalhos são mantidos: o 405 informa em ``Allow`` os métodos aceitos.
    return _error_response(exc.status_code, code, message, headers=exc.headers)


def _handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    """Responde sem expor a causa, que pode conter SQL ou dados internos.

    O traceback não é registrado aqui: depois deste tratador, o Starlette
    relança a exceção, e o servidor a registra no log.
    """
    logger.error("Erro inesperado em %s %s", request.method, request.url.path)
    return _error_response(
        500, "internal_error", "Erro interno. Tente novamente mais tarde."
    )


def _field_name(error: Mapping[str, Any]) -> str | None:
    """``("body", "subset_ids", 0)`` vira ``"subset_ids.0"``.

    Devolve ``None`` quando o erro não pertence a um campo: regra que envolve
    mais de um campo ou JSON malformado (cujo ``loc`` traz só a posição).
    """
    loc: Sequence[str | int] = error["loc"]
    if error["type"] == "json_invalid" or len(loc) < 2:
        return None
    return ".".join(str(part) for part in loc[1:])


def _validation_message(error: Mapping[str, Any]) -> str:
    ctx = error.get("ctx") or {}
    if error["type"] == "value_error":
        # ``ValueError`` dos nossos validators; ``msg`` traria "Value error, ".
        return str(ctx["error"]) if "error" in ctx else _DEFAULT_VALIDATION_MESSAGE
    message = _VALIDATION_MESSAGES.get(error["type"], _DEFAULT_VALIDATION_MESSAGE)
    if error["type"] == "enum":
        ctx = {"expected": str(ctx["expected"]).replace(" or ", " ou ")}
    return message.format(**ctx)
