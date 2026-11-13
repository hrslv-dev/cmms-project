from __future__ import annotations

from datetime import date, time, timedelta
from typing import TYPE_CHECKING

import sqlalchemy as sq
import sqlalchemy.orm as orm

from app.infrastructure.base.base_model import Base

if TYPE_CHECKING:
    from app.models.machine_model import MachineModel
    from app.models.operator_model import OperatorModel
    from app.models.subset_maintenance_model import SubsetMaintenanceModel
    from app.models.technician_model import TechnicianModel


class MaintenanceModel(Base):
    """Tabela ``maintenance``: uma manutenção de uma máquina por um técnico.

    Os subconjuntos NÃO ficam mais em uma coluna desta tabela: a relação com
    ``subsets`` é N:N e passa por ``subsets_maintenance`` (``subset_links``).

    Dois atributos têm nome Python diferente do nome da coluna:
    ``maintenance_date`` (coluna ``date``) e ``maintenance_type`` (coluna
    ``type``). Um atributo chamado ``date`` esconderia a classe
    ``datetime.date`` usada nas anotações, e ``type`` esconderia a função
    embutida do Python. Os demais atributos repetem o nome da coluna.
    """

    __tablename__ = "maintenance"
    __table_args__ = (
        sq.CheckConstraint(
            "type IN ('Corretiva', 'Preventiva')",
            name="ck_maintenance_type",
        ),
        sq.CheckConstraint(
            "service IN ('Inspeção', 'Lubrificação', 'Substituição', 'Ajuste', "
            "'Limpeza', 'Reparo', 'Instalação', 'Configuração', 'Calibração', "
            "'Modificação')",
            name="ck_maintenance_service",
        ),
        # Manutenção corretiva exige a descrição do problema.
        sq.CheckConstraint(
            "type <> 'Corretiva' OR problem IS NOT NULL",
            name="ck_maintenance_problem_corrective",
        ),
        sq.Index("idx_maintenance_operator", "operator_id"),
        sq.Index("idx_maintenance_technician", "technician_id"),
        sq.Index("idx_maintenance_machine", "machine_id"),
    )

    # O operador é opcional: a coluna aceita NULL.
    operator_id: orm.Mapped[int | None] = orm.mapped_column(
        sq.ForeignKey("operators.id", name="fk_maintenance_operator"),
        nullable=True,
    )
    technician_id: orm.Mapped[int] = orm.mapped_column(
        sq.ForeignKey("technicians.id", name="fk_maintenance_technician"),
        nullable=False,
    )
    machine_id: orm.Mapped[int] = orm.mapped_column(
        sq.ForeignKey("machines.id", name="fk_maintenance_machine"),
        nullable=False,
    )
    maintenance_date: orm.Mapped[date] = orm.mapped_column(
        "date", sq.Date, nullable=False
    )
    time_start: orm.Mapped[time] = orm.mapped_column(sq.Time, nullable=False)
    # NULL significa manutenção ainda em andamento.
    time_end: orm.Mapped[time | None] = orm.mapped_column(sq.Time, nullable=True)
    service: orm.Mapped[str] = orm.mapped_column(sq.String(20), nullable=False)
    problem: orm.Mapped[str | None] = orm.mapped_column(sq.Text, nullable=True)
    maintenance_type: orm.Mapped[str] = orm.mapped_column(
        "type", sq.String(20), nullable=False
    )
    # Coluna gerada pelo banco (GENERATED ALWAYS ... STORED). ``Computed`` faz
    # o ORM nunca enviá-la em INSERT/UPDATE e ler o valor calculado de volta.
    # Se ``time_end`` for menor que ``time_start``, o banco entende que a
    # manutenção atravessou a meia-noite e soma 24 horas.
    elapsed_time: orm.Mapped[timedelta | None] = orm.mapped_column(
        sq.Interval,
        sq.Computed(
            "CASE "
            "WHEN time_end IS NULL THEN NULL::interval "
            "WHEN time_end >= time_start THEN time_end - time_start "
            "ELSE time_end - time_start + INTERVAL '24 hours' "
            "END",
            persisted=True,
        ),
        nullable=True,
    )
    description: orm.Mapped[str | None] = orm.mapped_column(sq.Text, nullable=True)

    operator: orm.Mapped[OperatorModel | None] = orm.relationship(
        back_populates="maintenances"
    )
    technician: orm.Mapped[TechnicianModel] = orm.relationship(
        back_populates="maintenances"
    )
    machine: orm.Mapped[MachineModel] = orm.relationship(
        back_populates="maintenances"
    )

    # Lado "um" do N:N com subconjuntos: cada item é uma linha de
    # ``subsets_maintenance``. Para chegar ao subconjunto: ``link.subset``.
    subset_links: orm.Mapped[list[SubsetMaintenanceModel]] = orm.relationship(
        back_populates="maintenance", passive_deletes="all"
    )
