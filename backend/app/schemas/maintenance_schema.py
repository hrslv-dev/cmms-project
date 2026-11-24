"""Schemas da API para manutenções."""

from typing import Annotated

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
    # Começa vazia; cada item deve ser maior que 0; repetidos são removidos
    subset_ids: list[Annotated[int, Field(gt=0)]] = Field(default_factory=list)

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        """Apara os espaços do início e do fim; se não sobrar texto, é ``None``."""
        if value is None:
            return None
        return value.strip() or None

    @field_validator("subset_ids")
    @classmethod
    def remove_duplicate_ids(cls, value: list[int]) -> list[int]:
        """Remove ids repetidos, mantendo a ordem em que foram enviados.

        Repetir um subconjunto é tratado como a mesma escolha, não como erro.
        """
        return list(dict.fromkeys(value))

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
