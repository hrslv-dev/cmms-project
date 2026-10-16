"""Modelo SQLAlchemy dos operadores cadastrados no PostgreSQL."""

from sqlalchemy import Identity, Integer, PrimaryKeyConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Operador(Base):
    """Representa um operador cadastrado na tabela ``operadores``.

    O banco gera o ID automaticamente. O nome é obrigatório e pode ter até
    100 caracteres, conforme a estrutura existente no PostgreSQL.
    """

    __tablename__ = "operadores"
    __table_args__ = (PrimaryKeyConstraint("id", name="pk_operadores"),)

    id: Mapped[int] = mapped_column(
        Integer, Identity(always=True), nullable=False
    )
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
