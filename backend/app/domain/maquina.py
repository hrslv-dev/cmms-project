"""Entidade persistida que representa uma máquina do CMMS."""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Maquina(Base):
    """Máquina identificada por um ID gerado pelo banco e um nome obrigatório."""
    # Chama a identificação da tabela SQL 
    __tablename__ = "maquinas"

    # Mapeia os valores com as respectivas constraints do banco  
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)
    nome: Mapped[str] = mapped_column(String, nullable=False)
