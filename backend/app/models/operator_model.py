from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sq
import sqlalchemy.orm as orm

from app.infrastructure.base.base_model import Base

if TYPE_CHECKING:
    from app.models.maintenance_model import MaintenanceModel


class OperatorModel(Base):
    """Tabela ``operators``. O ``id`` é herdado de ``Base``."""

    __tablename__ = "operators"

    name: orm.Mapped[str] = orm.mapped_column(sq.String(100), nullable=False)

    # ``maintenance.operator_id`` aceita NULL. Sem ``passive_deletes="all"``,
    # excluir um operador faria o ORM gravar NULL nas manutenções dele antes do
    # DELETE, apagando o vínculo do histórico sem nenhum erro. Com a opção, a
    # foreign key do banco recusa a exclusão enquanto houver manutenções.
    maintenances: orm.Mapped[list[MaintenanceModel]] = orm.relationship(
        back_populates="operator", passive_deletes="all"
    )
