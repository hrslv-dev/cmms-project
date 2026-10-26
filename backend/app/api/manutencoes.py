"""Rotas HTTP para manutenções."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.infrastructure.persistence.session import get_db_session
from backend.app.schemas.manutencao import ManutencaoCreate, ManutencaoRead
from backend.app.services.manutencao_service import ManutencaoService


router = APIRouter(prefix="/manutencoes", tags=["Manutenções"])


@router.post(
    "/",
    response_model=ManutencaoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar uma manutenção",
)
def registrar_manutencao(
    dados: ManutencaoCreate,
    session: Annotated[Session, Depends(get_db_session)],
) -> ManutencaoRead:
    """Valida o pedido e encaminha o caso de uso ao service."""
    service = ManutencaoService(session)
    return service.registrar(dados)
