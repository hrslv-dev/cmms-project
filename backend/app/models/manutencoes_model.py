from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.base.base_model import Base


class ManutencoesModel(Base):
    __tablename__ = "manutencoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    maquina_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("maquinas.id"), nullable=False
    )
    operador_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("operadores.id"), nullable=True
    )
    tecnico_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tecnicos.id"), nullable=True
    )
    descricao: Mapped[str] = mapped_column(Text, nullable=True)

    