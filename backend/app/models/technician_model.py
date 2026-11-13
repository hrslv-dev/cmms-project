from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sq
import sqlalchemy.orm as orm

from app.infrastructure.base.base_model import Base

if TYPE_CHECKING:
    from app.models.maintenance_model import MaintenanceModel


class TechnicianModel(Base):
    __tablename__ = "tecnicos"
    __table_args__ = (
        sq.CheckConstraint(
            "funcao IN ('Eletricista', 'Mecânico')",
            name="ck_funcao_tecnico",
        ),
    )

    id: orm.Mapped[int] = orm.mapped_column(sq.Integer, primary_key=True)
    name: orm.Mapped[str] = orm.mapped_column("nome", sq.String(50), nullable=False)
    function: orm.Mapped[str] = orm.mapped_column("funcao", sq.String(50), nullable=False)
    maintenances: orm.Mapped[list[MaintenanceModel]] = orm.relationship(
        back_populates="technician"
    )
