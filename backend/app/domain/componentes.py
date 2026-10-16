"""Entidade persistida que representa um componente de máquina."""

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Components(Base):
    """Componente associado a uma máquina existente."""

    __tablename__ = "componentes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_maquina: Mapped[int] = mapped_column(
        Integer, ForeignKey("maquinas.id"), nullable=False
    )
    nome: Mapped[str] = mapped_column(String, nullable=False)
