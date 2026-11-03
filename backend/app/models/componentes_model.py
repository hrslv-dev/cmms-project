from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.base.base_model import Base


class ComponentesModel(Base):
    __tablename__ = "componentes"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )

    nome: Mapped[str] = mapped_column(
        String(100), nullable=False
    )

    maquina_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("maquinas.id"), nullable=False
    )
    maquina: Mapped["MaquinasModel"] = relationship(
        back_populates="componentes"
    )
    manutencoes: Mapped[list["ManutencoesModel"]] = relationship(
        back_populates="componente"
    )
