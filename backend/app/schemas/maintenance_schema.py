"""Schemas da API para manutenções."""

from typing import Any

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.services.enums import MaintenanceType, ProblemCategory, ServiceCategory


class MaintenanceCreate(BaseModel):
    """Dados que o cliente envia para registrar uma manutenção.

    As regras de negócio (existência de máquina/técnico/operador, subconjunto
    da mesma máquina) ficam no ``MaintenanceService``.
    """

    # Recusa os campos que não estejam na ficha
    model_config = ConfigDict(extra="forbid")

    # Obrigatórios: não têm valor padrão
    machine_id: int = Field(gt=0)
    technician_id: int = Field(gt=0)
    started_at: AwareDatetime  # data e hora COM fuso
    finished_at: AwareDatetime
    service: ServiceCategory
    maintenance_type: MaintenanceType

    # Opcionais: têm valor padrão
    operator_id: int | None = Field(default=None, gt=0)
    problem: ProblemCategory | None = None  # obrigatório em corretiva
    description: str | None = None
    subset_ids: list[int] = Field(default_factory=list)  # Começa vazia

    @field_validator("description", mode="before")
    @classmethod
    def blank_to_none(cls, value: Any) -> Any:
        """Trata texto vazio ou só com espaços como ``None`` (não preenchido)."""
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @model_validator(mode="after")
    def validate_problem(self) -> "MaintenanceCreate":
        """Exige ``problem`` em corretiva; em preventiva é opcional."""
        if (
            self.maintenance_type is MaintenanceType.CORRECTIVE
            and self.problem is None
        ):
            raise ValueError("problem é obrigatório em manutenção corretiva")
        return self

    @model_validator(mode="after")
    def validate_period(self) -> "MaintenanceCreate":
        """Recusa fim anterior ao início, como o CHECK do banco."""
        if self.finished_at < self.started_at:
            raise ValueError("finished_at não pode ser anterior a started_at")
        return self
