from sqlalchemy import ForeignKey, Integer, Text, Computed, Interval, Time, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import CheckConstraint

from app.infrastructure.base.base_model import Base

from datetime import timedelta
from datetime import time 


class ManutencoesModel(Base):
    __tablename__ = "manutencoes"
    __table_args__ = (CheckConstraint(
        "funcao IN ('Preventiva', 'Corretiva')", 
        name = 'chk_manutencao_tipo' 
        ), 
        CheckConstraint("funcao IN ('Inspeção','Limpeza','Ajuste','Lubrificação', 'Substituição','Reparo','Instalação','Configuração','Calibração','Modificação')", 
            name='chk_servicos'),
    )
        

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
    maquina_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("maquinas.id"), nullable=False
    )
    descricao: Mapped[str] = mapped_column(Text, nullable=True)
    tempo_passado: Mapped[timedelta | None] = mapped_column(
        Interval, Computed("hora_fim - hora_inicio", persisted=True)
    )
    hora_inicio: Mapped[time] = mapped_column(Time, nullable=False)
    hora_fim: Mapped[time] = mapped_column(Time, nullable=False)
    servico: Mapped[str] = mapped_column(String(100), nullable=True)
    problema: Mapped[str] = mapped_column(Text, nullable=False) 
    tipo : Mapped[str] = mapped_column(String(50), nullable=True)  
    