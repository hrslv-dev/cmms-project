from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sq
import sqlalchemy.orm as orm

from app.infrastructure.base.base_model import Base

if TYPE_CHECKING:
    from app.models.technician_model import TechnicianModel


class TechnicalFunctionModel(Base):
    """Tabela ``technical_functions``: catálogo extensível de funções técnicas.

    Substitui o antigo ``CHECK (funcao IN ('Eletricista', 'Mecânico'))`` da
    tabela de técnicos: novas funções passam a ser linhas, não alterações de
    constraint. ``active`` permite aposentar uma função sem apagar o histórico.

    O banco não impede que um técnico aponte para uma função inativa; essa
    regra pertence à camada Service.
    """

    __tablename__ = "technical_functions"
    __table_args__ = (
        sq.CheckConstraint("length(btrim(name)) > 0", name="ck_function_name"),
    )

    name: orm.Mapped[str] = orm.mapped_column(
        sq.String(50), nullable=False, unique=True
    )
    # ``server_default`` espelha o ``DEFAULT true`` do banco: se ``active`` não
    # for informado, o INSERT omite a coluna e o PostgreSQL aplica o padrão.
    active: orm.Mapped[bool] = orm.mapped_column(
        sq.Boolean, nullable=False, server_default=sq.true()
    )

    technicians: orm.Mapped[list[TechnicianModel]] = orm.relationship(
        back_populates="function", passive_deletes="all"
    )
