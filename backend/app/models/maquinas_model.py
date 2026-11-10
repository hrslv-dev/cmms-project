from __future__ import annotations

from typing import TYPE_CHECKING


import sqlalchemy as sq
import sqlalchemy.orm as orm 
from app.infrastructure.base.base_model import Base

if TYPE_CHECKING:
    from app.models.componentes_model import ComponentesModel
    from app.models.manutencoes_model import ManutencoesModel


class MaquinasModel(Base):
    __tablename__ = "maquinas"

    id: orm.Mapped[int] = orm.mapped_column(sq.Integer, primary_key=True)
    nome: orm.Mapped[str] = orm.mapped_column(sq.String(100), nullable=False)
    componentes: orm.Mapped[list[ComponentesModel]] = orm.relationship(
        back_populates="maquina"
    )
    manutencoes: orm.Mapped[list[ManutencoesModel]] = orm.relationship(
        back_populates="maquina"
    )
