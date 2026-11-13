from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sq
import sqlalchemy.orm as orm

from app.infrastructure.base.base_model import Base

if TYPE_CHECKING:
    from app.models.maintenance_model import MaintenanceModel


class OperatorModel(Base):
    __tablename__ = "operadores"

    id: orm.Mapped[int] = orm.mapped_column(sq.Integer, primary_key=True)
    name: orm.Mapped[str] = orm.mapped_column("nome", sq.String(100), nullable=False)
    maintenances: orm.Mapped[list[MaintenanceModel]] = orm.relationship(
        back_populates="operator"
    )
