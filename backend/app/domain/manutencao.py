"""Modelo SQLAlchemy do histórico de manutenções existente no PostgreSQL."""

from datetime import date, time, timedelta

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Identity,
    Integer,
    Interval,
    PrimaryKeyConstraint,
    String,
    Text,
    Time,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class HistoricoManutencao(Base):
    """Representa um registro da tabela ``historico_manutencao``.

    Os campos e as regras abaixo espelham a estrutura encontrada no PostgreSQL.
    O banco gera o ``id`` e exige que máquina, técnico, componente, operador,
    tipo, serviço, data e hora de início sejam informados. Problema, descrição,
    hora de fim e duração podem ficar vazios.

    As chaves estrangeiras exigem que os IDs de máquina, técnico, componente e
    operador já existam em suas respectivas tabelas. Os três CHECKs limitam os
    tipos e serviços permitidos e garantem que a hora de fim, quando informada,
    seja posterior à hora de início.
    """

    __tablename__ = "historico_manutencao"
    __table_args__ = (
        CheckConstraint(
            "hora_fim IS NULL OR hora_inicio < hora_fim",
            name="chk_historico_horario",
        ),
        CheckConstraint(
            "servico IN ('Inspeção', 'Limpeza', 'Ajuste', 'Lubrificação', "
            "'Substituição', 'Reparo', 'Instalação', 'Configuração', "
            "'Calibração', 'Modificação')",
            name="chk_historico_servico",
        ),
        CheckConstraint(
            "tipo IN ('Corretiva', 'Preventiva')",
            name="chk_historico_tipo",
        ),
        PrimaryKeyConstraint("id", name="pk_historico_manutencao"),
    )

    id: Mapped[int] = mapped_column(
        Integer, Identity(always=True), nullable=False
    )
    maquina_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("maquinas.id", name="fk_historico_maquina"),
        nullable=False,
    )
    tecnico_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tecnicos.id", name="fk_historico_tecnico"),
        nullable=False,
    )
    componente_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("componentes.id", name="fk_historico_componente"),
        nullable=False,
    )
    operador_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("operadores.id", name="fk_historico_operador"),
        nullable=False,
    )
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    problema: Mapped[str | None] = mapped_column(Text, nullable=True)
    servico: Mapped[str] = mapped_column(String(20), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_manutencao: Mapped[date] = mapped_column(Date, nullable=False)
    hora_inicio: Mapped[time] = mapped_column(Time, nullable=False)
    hora_fim: Mapped[time | None] = mapped_column(Time, nullable=True)
    tempo_manutencao: Mapped[timedelta | None] = mapped_column(
        Interval, nullable=True
    )
