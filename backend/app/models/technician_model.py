from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sq
import sqlalchemy.orm as orm

from app.infrastructure.base.base_model import Base

if TYPE_CHECKING:
    from app.models.maintenance_model import MaintenanceModel
    from app.models.technical_function_model import TechnicalFunctionModel


class TechnicianModel(Base):
    """Tabela ``technicians``: técnico com exatamente uma função cadastrada."""

    __tablename__ = "technicians"
    __table_args__ = (sq.Index("idx_technicians_function", "function_id"),)

    name: orm.Mapped[str] = orm.mapped_column(sq.String(100), nullable=False)
    function_id: orm.Mapped[int] = orm.mapped_column(
        sq.ForeignKey(
            "technical_functions.id",
            name="fk_technical_function",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    # ``function`` agora é o objeto da função técnica (antes era uma string).
    # O nome fica em ``technician.function.name``.
    function: orm.Mapped[TechnicalFunctionModel] = orm.relationship(
        back_populates="technicians"
    )
    maintenances: orm.Mapped[list[MaintenanceModel]] = orm.relationship(
        back_populates="technician", passive_deletes="all"
    )
