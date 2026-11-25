"""Rotas de operadores."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_operator_service
from app.schemas.error_schema import ErrorResponse
from app.schemas.operator_schema import OperatorCreate, OperatorRead
from app.services.operator_service import OperatorService

router = APIRouter(prefix="/operators", tags=["Operadores"])


@router.get("", response_model=list[OperatorRead])
def list_operators(service: Annotated[OperatorService, Depends(get_operator_service)]):
    """Lista os operadores em ordem alfabética."""
    return service.list_operators()


@router.post(
    "",
    status_code=201,
    response_model=OperatorRead,
    responses={409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def create_operator(
    body: OperatorCreate,
    service: Annotated[OperatorService, Depends(get_operator_service)],
):
    """Cadastra um operador."""
    return service.create_operator(**body.model_dump())
