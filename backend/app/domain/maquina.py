"""Entidade persistida que representa uma máquina do CMMS."""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import  ( PrimaryKeyConstraint, 
                         Identity)
                         

from .base import Base


class Maquina(Base):
    """Máquina identificada por um ID gerado pelo banco e um nome obrigatório."""
    # Chama a identificação da tabela SQL 
    __tablename__ = "maquinas"
    
    __table_args__ = ( 
                      PrimaryKeyConstraint("id", name ="pk_maquinas")
                      )

    # Mapeia os valores com as respectivas constraints do banco  
    id: Mapped[int] = mapped_column(Integer, Identity(always=True), nullable=False)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
