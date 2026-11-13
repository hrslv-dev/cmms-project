from __future__ import annotations

from datetime import date, time, timedelta
from typing import TYPE_CHECKING

import sqlalchemy as sq
import sqlalchemy.orm as orm

from app.infrastructure.base.base_model import Base

if TYPE_CHECKING:
    from app.models.subset_model import SubsetModel
    from app.models.machine_model import MachineModel
    from app.models.operator_model import OperatorModel
    from app.models.technician_model import TechnicianModel


class MaintenanceModel(Base):
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
    machine_id: orm.Mapped[int] = orm.mapped_column(
        "maquina_id", sq.Integer, sq.ForeignKey("maquinas.id"), nullable=False
    )
    subset_id: orm.Mapped[int] = orm.mapped_column(
        "componente_id", sq.Integer, sq.ForeignKey("componentes.id"), nullable=False
    )
    technician_id: orm.Mapped[int] = orm.mapped_column(
        "tecnico_id", sq.Integer, sq.ForeignKey("tecnicos.id"), nullable=False
    )
    operator_id: orm.Mapped[int] = orm.mapped_column(
        "operador_id", sq.Integer, sq.ForeignKey("operadores.id"), nullable=False
    )
    maintenance_type: orm.Mapped[str] = orm.mapped_column(
        "tipo", sq.String(50), nullable=False
    )
    problem: orm.Mapped[str | None] = orm.mapped_column(
        "problema", sq.Text, nullable=True
    )
    service: orm.Mapped[str] = orm.mapped_column(
        "servico", sq.String(100), nullable=False
    )
    description: orm.Mapped[str | None] = orm.mapped_column(
        "descricao", sq.Text, nullable=True
    )
    maintenance_date: orm.Mapped[date] = orm.mapped_column(
        "data_manutencao", sq.Date, nullable=False
    )
    start_time: orm.Mapped[time] = orm.mapped_column(
        "hora_inicio", sq.Time, nullable=False
    )
    end_time: orm.Mapped[time | None] = orm.mapped_column(
        "hora_fim", sq.Time, nullable=True
    )
    duration: orm.Mapped[timedelta | None] = orm.mapped_column(
        "tempo_passado",
        sq.Interval,
        sq.Computed("hora_fim - hora_inicio", persisted=True),
        nullable=True,
    )

    machine: orm.Mapped[MachineModel] = orm.relationship(
        back_populates="maintenances"
    )
    subset: orm.Mapped[SubsetModel] = orm.relationship(
        back_populates="maintenances"
    )
    technician: orm.Mapped[TechnicianModel] = orm.relationship(
        back_populates="maintenances"
    )
    operator: orm.Mapped[OperatorModel] = orm.relationship(
        back_populates="maintenances"
    )
