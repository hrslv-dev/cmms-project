from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sq
import sqlalchemy.orm as orm

from app.infrastructure.base.base_model import Base

if TYPE_CHECKING:
    from app.models.maintenance_model import MaintenanceModel
    from app.models.subset_model import SubsetModel


class MachineModel(Base):
    """Tabela ``machines``. O ``id`` é herdado de ``Base``."""

    __tablename__ = "machines"

    name: orm.Mapped[str] = orm.mapped_column(sq.String(100), nullable=False)

    # ``passive_deletes="all"``: ao excluir a máquina, o ORM NÃO tenta alterar
    # as linhas filhas; emite só o DELETE e deixa a foreign key do banco
    # recusar a exclusão se houver subconjuntos ou manutenções vinculados.
    subsets: orm.Mapped[list[SubsetModel]] = orm.relationship(
        back_populates="machine", passive_deletes="all"
    )
    maintenances: orm.Mapped[list[MaintenanceModel]] = orm.relationship(
        back_populates="machine", passive_deletes="all"
    )
