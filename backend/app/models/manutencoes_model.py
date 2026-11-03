from datetime import date, time, timedelta

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    Interval,
    String,
    Text,
    Time,
    Computed,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.base.base_model import Base


class ManutencoesModel(Base):
    __tablename__ = "manutencoes"
    __table_args__ = (
        CheckConstraint(
            "tipo IN ('Preventiva', 'Corretiva')",
            name="chk_manutencao_tipo",
        ),
        CheckConstraint(
            "servico IN ('Inspeção', 'Limpeza', 'Ajuste', 'Lubrificação', "
            "'Substituição', 'Reparo', 'Instalação', 'Configuração', "
            "'Calibração', 'Modificação')",
            name="chk_manutencao_servico",
        ),
        CheckConstraint(
            "hora_fim IS NULL OR hora_inicio < hora_fim",
            name="chk_manutencao_horario",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    maquina_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("maquinas.id"), nullable=False
    )
    componente_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("componentes.id"), nullable=False
    )
    tecnico_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tecnicos.id"), nullable=False
    )
    operador_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("operadores.id"), nullable=False
    )
    tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    problema: Mapped[str | None] = mapped_column(Text, nullable=True)
    servico: Mapped[str] = mapped_column(String(100), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_manutencao: Mapped[date] = mapped_column(Date, nullable=False)
    hora_inicio: Mapped[time] = mapped_column(Time, nullable=False)
    hora_fim: Mapped[time | None] = mapped_column(Time, nullable=True)
    tempo_manutencao: Mapped[timedelta | None] = mapped_column(
        Interval,
        Computed("hora_fim - hora_inicio", persisted=True),
        nullable=True,
    )

    maquina: Mapped["MaquinasModel"] = relationship(
        back_populates="manutencoes"
    )
    componente: Mapped["ComponentesModel"] = relationship(
        back_populates="manutencoes"
    )
    tecnico: Mapped["TecnicoModel"] = relationship(
        back_populates="manutencoes"
    )
    operador: Mapped["OperadorModel"] = relationship(
        back_populates="manutencoes"
    )
