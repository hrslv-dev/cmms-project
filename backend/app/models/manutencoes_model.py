from __future__ import annotations

from datetime import date, time, timedelta
from typing import TYPE_CHECKING

import sqlalchemy as sq
import sqlalchemy.orm as orm

from app.infrastructure.base.base_model import Base

if TYPE_CHECKING:
    from app.models.componentes_model import ComponentesModel
    from app.models.maquinas_model import MaquinasModel
    from app.models.operadores_model import OperadorModel
    from app.models.tecnico_model import TecnicoModel


class ManutencoesModel(Base):
    __tablename__ = "historico_manutencao"
    __table_args__ = (
        sq.CheckConstraint(
            "tipo IN ('Preventiva', 'Corretiva')",
            name="chk_manutencao_tipo",
        ),
        sq.CheckConstraint(
            "servico IN ('Inspeção', 'Limpeza', 'Ajuste', 'Lubrificação', "
            "'Substituição', 'Reparo', 'Instalação', 'Configuração', "
            "'Calibração', 'Modificação')",
            name="chk_manutencao_servico",
        ),
        sq.CheckConstraint(
            "hora_fim IS NULL OR hora_inicio < hora_fim",
            name="chk_manutencao_horario",
        ),
    )

    id: orm.Mapped[int] = orm.mapped_column(sq.Integer, primary_key=True)
    maquina_id: orm.Mapped[int] = orm.mapped_column(
        sq.Integer, sq.ForeignKey("maquinas.id"), nullable=False
    )
    componente_id: orm.Mapped[int] = orm.mapped_column(
        sq.Integer, sq.ForeignKey("componentes.id"), nullable=False
    )
    tecnico_id: orm.Mapped[int] = orm.mapped_column(
        sq.Integer, sq.ForeignKey("tecnicos.id"), nullable=False
    )
    operador_id: orm.Mapped[int] = orm.mapped_column(
        sq.Integer, sq.ForeignKey("operadores.id"), nullable=False
    )
    tipo: orm.Mapped[str] = orm.mapped_column(sq.String(50), nullable=False)
    problema: orm.Mapped[str | None] = orm.mapped_column(sq.Text, nullable=True)
    servico: orm.Mapped[str] = orm.mapped_column(sq.String(100), nullable=False)
    descricao: orm.Mapped[str | None] = orm.mapped_column(sq.Text, nullable=True)
    data_manutencao: orm.Mapped[date] = orm.mapped_column(sq.Date, nullable=False)
    hora_inicio: orm.Mapped[time] = orm.mapped_column(sq.Time, nullable=False)
    hora_fim: orm.Mapped[time | None] = orm.mapped_column(sq.Time, nullable=True)
    tempo_manutencao: orm.Mapped[timedelta | None] = orm.mapped_column(
        "tempo_passado",
        sq.Interval,
        sq.Computed("hora_fim - hora_inicio", persisted=True),
        nullable=True,
    )

    maquina: orm.Mapped[MaquinasModel] = orm.relationship(
        back_populates="manutencoes"
    )
    componente: orm.Mapped[ComponentesModel] = orm.relationship(
        back_populates="manutencoes"
    )
    tecnico: orm.Mapped[TecnicoModel] = orm.relationship(
        back_populates="manutencoes"
    )
    operador: orm.Mapped[OperadorModel] = orm.relationship(
        back_populates="manutencoes"
    )
