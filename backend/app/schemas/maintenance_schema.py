"""Schemas da API para manutenções."""

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from app.services.enums import MaintenanceType, ProblemCategory, ServiceCategory


class MaintenanceCreate(BaseModel):
    """Dados que o cliente envia para registrar uma manutenção.

    As regras de negócio (``problem`` obrigatório em corretiva, existência de
    máquina/técnico/operador, subconjunto da mesma máquina) ficam no
    ``MaintenanceService``.
    """

    # Recusa os campos que não estejam na ficha
    model_config = ConfigDict(extra="forbid")

    # Obrigatórios: não têm valor padrão
    machine_id: int
    technician_id: int
    started_at: AwareDatetime  # data e hora COM fuso
    service: ServiceCategory
    maintenance_type: MaintenanceType

    # Opcionais: têm valor padrão
    operator_id: int | None = None
    finished_at: AwareDatetime | None = None  # None = em andamento
    problem: ProblemCategory | None = None
    description: str | None = None
    subset_ids: list[int] = Field(default_factory=list)  # Começa vazia

    @model_validator(mode="after")
    def validate_period(self) -> "MaintenanceCreate":
        """Recusa fim anterior ao início, como o CHECK do banco."""
        if self.finished_at is not None and self.finished_at < self.started_at:
            raise ValueError("finished_at não pode ser anterior a started_at")
        return self
