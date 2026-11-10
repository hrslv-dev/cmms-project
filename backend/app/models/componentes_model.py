from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sq
import sqlalchemy.orm as orm

from app.infrastructure.base.base_model import Base

if TYPE_CHECKING:
    from app.models.maquinas_model import MaquinasModel
    from app.models.manutencoes_model import ManutencoesModel


class ComponentesModel(Base):
    __tablename__ = "componentes"

    id: orm.Mapped[int] = orm.mapped_column(
        sq.Integer, primary_key=True
    )

    nome: orm.Mapped[str] = orm.mapped_column(
        sq.String(100), nullable=False
    )

    maquina_id: orm.Mapped[int] = orm.mapped_column(
        sq.Integer, sq.ForeignKey("maquinas.id"), nullable=False
    )
    maquina: orm.Mapped[MaquinasModel] = orm.relationship(
        back_populates="componentes"
    )
    manutencoes: orm.Mapped[list[ManutencoesModel]] = orm.relationship(
        back_populates="componente"
    )
