"""Rotas de máquinas e de seus subconjuntos."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_machine_service, get_subset_service
from app.schemas.error_schema import ErrorResponse
from app.schemas.machine_schema import MachineRead
from app.schemas.subset_schema import SubsetRead
from app.services.machine_service import MachineService
from app.services.subset_service import SubsetService

router = APIRouter(prefix="/machines", tags=["Máquinas"])


@router.get("", response_model=list[MachineRead])
def list_machines(service: Annotated[MachineService, Depends(get_machine_service)]):
    """Lista as máquinas em ordem alfabética."""
    return service.list_machines()


@router.get(
    "/{machine_id}/subsets",
    response_model=list[SubsetRead],
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def list_subsets(
    machine_id: int, service: Annotated[SubsetService, Depends(get_subset_service)]
):
    """Lista os subconjuntos da máquina em ordem alfabética."""
    return service.list_subsets_by_machine(machine_id)
