"""Schemas da API para criação e consulta de manutenções.

Os schemas validam FORMATO e TIPOS da entrada/saída. As regras de negócio
(``problem`` obrigatório em corretiva, subconjunto da mesma máquina, existência
de máquina/técnico/operador) ficam no ``MaintenanceService``.
"""

from datetime import datetime, timedelta

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from app.services.enums import MaintenanceType, ProblemCategory, ServiceCategory


class MaintenanceCreate(BaseModel):
    """Dados que o cliente envia para registrar uma manutenção.

    ``id`` e ``elapsed_time`` são gerados pelo banco e não fazem parte da
    entrada. ``AwareDatetime`` recusa data/hora sem fuso: o cliente deve
    enviar, por exemplo, ``"2026-09-14T11:30:00-03:00"``.
    """

    model_config = ConfigDict(extra="forbid")

    machine_id: int = Field(gt=0)
    technician_id: int = Field(gt=0)
    operator_id: int | None = Field(default=None, gt=0)
    started_at: AwareDatetime
    finished_at: AwareDatetime | None = None
    service: ServiceCategory
    maintenance_type: MaintenanceType
    problem: ProblemCategory | None = None
    description: str | None = None
    subset_ids: list[int] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_period(self) -> "MaintenanceCreate":
        """Mantém no contrato da API a regra do CHECK de período do banco."""
        if self.finished_at is not None and self.finished_at < self.started_at:
            raise ValueError("finished_at não pode ser anterior a started_at")
        return self


class MaintenanceRead(BaseModel):
    """Formato de resposta da API, incluindo os valores gerados pelo banco."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    machine_id: int
    technician_id: int
    operator_id: int | None
    started_at: datetime
    finished_at: datetime | None
    elapsed_time: timedelta | None
    service: str
    maintenance_type: str
    problem: str | None
    description: str | None
