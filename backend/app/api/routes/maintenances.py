"""Rotas de manutenções."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_maintenance_service
from app.schemas.error_schema import ErrorResponse
from app.schemas.maintenance_schema import MaintenanceCreate, MaintenanceRead
from app.services.maintenance_service import MaintenanceService

router = APIRouter(prefix="/maintenances", tags=["Manutenções"])


@router.post(
    "",
    status_code=201,
    response_model=MaintenanceRead,
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def create_maintenance(
    body: MaintenanceCreate,
    service: Annotated[MaintenanceService, Depends(get_maintenance_service)],
):
    """Registra uma manutenção já encerrada e vincula seus subconjuntos."""
    return service.create_maintenance(**body.model_dump())
