"""Entidade persistida que representa um componente de máquina."""

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ( 
                        PrimaryKeyConstraint, 
                        ForeignKey, 
                        Identity)
from .base import Base


class Components(Base):
    """Componente associado a uma máquina existente."""

    __tablename__ = "componentes"
    __table_args__ = ( 
                      PrimaryKeyConstraint("id", name="pk_componentes")
                      )

    id: Mapped[int] = mapped_column(Integer,Identity, nullable=False)
    maquina_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("maquinas.id", name="fk_componentes"), nullable=False
    )
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
