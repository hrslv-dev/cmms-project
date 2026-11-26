from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sq
import sqlalchemy.orm as orm

from app.infrastructure.base.base_model import Base

if TYPE_CHECKING:
    from app.models.machine_model import MachineModel
    from app.models.subset_maintenance_model import SubsetMaintenanceModel


class SubsetModel(Base):
    """Tabela ``subsets``: subconjunto pertencente a exatamente uma máquina."""

    __tablename__ = "subsets"
    __table_args__ = (sq.Index("idx_subsets_machine", "machine_id"),)

    name: orm.Mapped[str] = orm.mapped_column(sq.String(100), nullable=False)
    machine_id: orm.Mapped[int] = orm.mapped_column(
        sq.ForeignKey("machines.id", name="fk_subsets_machines"), nullable=False
    )

    machine: orm.Mapped[MachineModel] = orm.relationship(back_populates="subsets")

    # Lado "um" do N:N com manutenções: cada item é uma linha de
    # ``subsets_maintenance``. Para chegar à manutenção: ``link.maintenance``.
    maintenance_links: orm.Mapped[list[SubsetMaintenanceModel]] = orm.relationship(
        back_populates="subset", passive_deletes="all"
    )
