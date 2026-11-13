from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sq
import sqlalchemy.orm as orm

from app.infrastructure.base.base_model import Base

if TYPE_CHECKING:
    from app.models.maintenance_model import MaintenanceModel
    from app.models.subset_model import SubsetModel


class SubsetMaintenanceModel(Base):
    """Tabela ``subsets_maintenance``: liga uma manutenção a um subconjunto.

    É a implementação física do N:N entre ``maintenance`` e ``subsets``. A
    tabela tem ``id`` próprio, então é mapeada como classe (Association
    Object), igual às demais, em vez de ficar escondida em um
    ``relationship(secondary=...)``. Esta classe é o ÚNICO caminho de escrita
    da associação: para vincular, cria-se um ``SubsetMaintenanceModel``.

    O par ``(maintenance_id, subset_id)`` é único. O banco NÃO verifica se o
    subconjunto pertence à mesma máquina da manutenção; essa regra pertence à
    camada Service.
    """

    __tablename__ = "subsets_maintenance"
    __table_args__ = (
        sq.UniqueConstraint(
            "maintenance_id", "subset_id", name="uq_maintenance_subset"
        ),
        # Não há índice só de ``maintenance_id``: o índice da constraint única
        # acima já começa por essa coluna e atende a essas buscas.
        sq.Index("idx_subsets_maintenance_subset", "subset_id"),
    )

    subset_id: orm.Mapped[int] = orm.mapped_column(
        sq.ForeignKey("subsets.id", name="fk_assoc_subsets"), nullable=False
    )
    maintenance_id: orm.Mapped[int] = orm.mapped_column(
        sq.ForeignKey("maintenance.id", name="fk_assoc_maintenance"),
        nullable=False,
    )

    subset: orm.Mapped[SubsetModel] = orm.relationship(
        back_populates="maintenance_links"
    )
    maintenance: orm.Mapped[MaintenanceModel] = orm.relationship(
        back_populates="subset_links"
    )
