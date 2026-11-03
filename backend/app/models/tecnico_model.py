from sqlalchemy import CheckConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.base.base_model import Base


class TecnicoModel(Base):
    __tablename__ = "tecnicos"
    __table_args__ = (
        CheckConstraint(
            "funcao IN ('Eletricista', 'Mecânico')",
            name="ck_funcao_tecnico",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(50), nullable=False)
    funcao: Mapped[str] = mapped_column(String(50), nullable=False)
    manutencoes: Mapped[list["ManutencoesModel"]] = relationship(
        back_populates="tecnico"
    )
