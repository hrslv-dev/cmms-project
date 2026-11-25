"""Dependências das rotas: sessão por requisição e Services."""

from collections.abc import Iterator
from typing import Annotated

import sqlalchemy.orm as orm
from fastapi import Depends

from app.infrastructure.conf.session import create_session
from app.services.machine_service import MachineService
from app.services.maintenance_service import MaintenanceService
from app.services.operator_service import OperatorService
from app.services.subset_service import SubsetService
from app.services.technician_service import TechnicianService


def get_session() -> Iterator[orm.Session]:
    """Abre uma sessão por requisição e a fecha no fim, mesmo com erro.

    Não faz ``commit``: o limite da transação é do Service. ``close`` desfaz o
    que não foi confirmado e devolve a conexão ao pool.
    """
    session = create_session()
    try:
        yield session
    finally:
        session.close()


SessionDep = Annotated[orm.Session, Depends(get_session)]


def get_machine_service(session: SessionDep) -> MachineService:
    return MachineService(session)


def get_subset_service(session: SessionDep) -> SubsetService:
    return SubsetService(session)


def get_technician_service(session: SessionDep) -> TechnicianService:
    return TechnicianService(session)


def get_operator_service(session: SessionDep) -> OperatorService:
    return OperatorService(session)


def get_maintenance_service(session: SessionDep) -> MaintenanceService:
    return MaintenanceService(session)
