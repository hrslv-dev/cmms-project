from __future__ import annotations

from datetime import datetime, timedelta
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

    Período: ``started_at`` e ``finished_at`` são ``TIMESTAMPTZ``, instantes
    completos (data + hora + fuso). O PostgreSQL guarda o instante absoluto
    (internamente em UTC), não o nome do fuso; ao ler, converte para o fuso
    da sessão, e o psycopg2 devolve ``datetime`` com deslocamento (ex.:
    ``-03:00``). ``finished_at`` NULL significa manutenção em andamento.

    Um atributo tem nome Python diferente do nome da coluna:
    ``maintenance_type`` (coluna ``type``), para não esconder a função
    embutida ``type``. Os demais atributos repetem o nome da coluna.
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
        # O fim não pode ser anterior ao início (em andamento = NULL).
        sq.CheckConstraint(
            "finished_at IS NULL OR finished_at >= started_at",
            name="ck_maintenance_finished_after_started",
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
    service: orm.Mapped[str] = orm.mapped_column(sq.String(20), nullable=False)
    problem: orm.Mapped[str | None] = orm.mapped_column(sq.Text, nullable=True)
    maintenance_type: orm.Mapped[str] = orm.mapped_column(
        "type", sq.String(20), nullable=False
    )
    description: orm.Mapped[str | None] = orm.mapped_column(sq.Text, nullable=True)
    # ``DateTime(timezone=True)`` corresponde a TIMESTAMPTZ. Grave sempre
    # ``datetime`` COM fuso: um horário sem fuso seria interpretado no fuso
    # da sessão do banco, que pode não ser o da fábrica.
    started_at: orm.Mapped[datetime] = orm.mapped_column(
        sq.DateTime(timezone=True), nullable=False
    )
    # NULL significa manutenção ainda em andamento.
    finished_at: orm.Mapped[datetime | None] = orm.mapped_column(
        sq.DateTime(timezone=True), nullable=True
    )
    # Coluna gerada pelo banco (GENERATED ALWAYS ... STORED). ``Computed`` faz
    # o ORM nunca enviá-la em INSERT/UPDATE e ler o valor calculado de volta.
    # É a diferença real entre dois instantes: 26 h viram
    # ``timedelta(days=1, hours=2)``; NULL enquanto ``finished_at`` for NULL.
    elapsed_time: orm.Mapped[timedelta | None] = orm.mapped_column(
        sq.Interval,
        sq.Computed("finished_at - started_at", persisted=True),
        nullable=True,
    )

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
