"""Rotas de técnicos."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_technician_service
from app.schemas.technician_schema import TechnicianRead
from app.services.technician_service import TechnicianService

router = APIRouter(prefix="/technicians", tags=["Técnicos"])


@router.get("", response_model=list[TechnicianRead])
def list_technicians(
    service: Annotated[TechnicianService, Depends(get_technician_service)],
):
    """Lista os técnicos em ordem alfabética."""
    return service.list_technicians()
