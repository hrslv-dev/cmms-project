from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.base.base_model import Base


class OperadorModel(Base):
    __tablename__ = "operadores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    manutencoes: Mapped[list["ManutencoesModel"]] = relationship(
        back_populates="operador"
    )
