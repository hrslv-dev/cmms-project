"""Schemas da API para criação e consulta de manutenções."""

from datetime import date, time, timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


TipoManutencao = Literal["Corretiva", "Preventiva"]
ServicoManutencao = Literal[
    "Inspeção",
    "Limpeza",
    "Ajuste",
    "Lubrificação",
    "Substituição",
    "Reparo",
    "Instalação",
    "Configuração",
    "Calibração",
    "Modificação",
]


class ManutencaoCreate(BaseModel):
    """Dados que o cliente precisa enviar para registrar uma manutenção.

    O ID é gerado pelo banco, e ``tempo_manutencao`` é calculado pela coluna
    persistida; por isso, nenhum dos dois faz parte dos dados de entrada.
    """

    model_config = ConfigDict(extra="forbid")

    maquina_id: int = Field(gt=0)
    tecnico_id: int = Field(gt=0)
    componente_id: int = Field(gt=0)
    operador_id: int = Field(gt=0)
    tipo: TipoManutencao
    problema: str | None = None
    servico: ServicoManutencao
    descricao: str | None = None
    data_manutencao: date
    hora_inicio: time
    hora_fim: time | None = None

    @model_validator(mode="after")
    def validar_horario(self) -> "ManutencaoCreate":
        """Mantém no contrato da API a regra de horário do banco."""
        if self.hora_fim is not None and self.hora_inicio >= self.hora_fim:
            raise ValueError("hora_fim deve ser posterior a hora_inicio")
        return self


class ManutencaoRead(ManutencaoCreate):
    """Formato de resposta da API, incluindo os valores gerados pelo banco."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    tempo_manutencao: timedelta | None
