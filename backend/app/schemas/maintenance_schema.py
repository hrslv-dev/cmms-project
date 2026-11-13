"""Schemas da API para criação e consulta de manutenções."""

from datetime import date, time, timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


MaintenanceType = Literal["Corretiva", "Preventiva"]
MaintenanceServiceType = Literal[
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


class MaintenanceCreate(BaseModel):
    """Dados que o cliente precisa enviar para registrar uma manutenção.

    O ID é gerado pelo banco, e ``duration`` é calculado pela coluna
    persistida; por isso, nenhum dos dois faz parte dos dados de entrada.
    """

    model_config = ConfigDict(extra="forbid")

    machine_id: int = Field(gt=0)
    technician_id: int = Field(gt=0)
    subset_id: int = Field(gt=0)
    operator_id: int = Field(gt=0)
    maintenance_type: MaintenanceType
    problem: str | None = None
    service: MaintenanceServiceType
    description: str | None = None
    maintenance_date: date
    start_time: time
    end_time: time | None = None

    @model_validator(mode="after")
    def validate_schedule(self) -> "MaintenanceCreate":
        """Mantém no contrato da API a regra de horário do banco."""
        if self.end_time is not None and self.start_time >= self.end_time:
            raise ValueError("end_time deve ser posterior a start_time")
        return self


class MaintenanceRead(MaintenanceCreate):
    """Formato de resposta da API, incluindo os valores gerados pelo banco."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    duration: timedelta | None
