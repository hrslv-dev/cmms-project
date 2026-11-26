"""Schemas da API para manutenções."""

import re
from datetime import datetime, timedelta
from typing import Annotated, Any

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.services.enums import MaintenanceType, ProblemCategory, ServiceCategory

# Começo de "2026-09-14T11:30:00-03:00": data ISO, separador e hora. O resto
# (data existente, fuso) é conferido pelo ``AwareDatetime``.
_DATE_AND_TIME = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}[Tt ][0-9]{2}:")


class MaintenanceCreate(BaseModel):
    """Dados que o cliente envia para registrar uma manutenção.

    As regras de negócio (existência de máquina/técnico/operador, subconjunto
    da mesma máquina, data mínima do início e fim que não esteja no futuro)
    ficam no ``MaintenanceService``.
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

    @field_validator("started_at", "finished_at", mode="before")
    @classmethod
    def require_date_and_time(cls, value: Any) -> Any:
        """Aceita só texto com data e hora (ou um ``datetime`` já pronto).

        Por padrão, o Pydantic lê números, inclusive em texto (``"0"``), como
        timestamp Unix em UTC. O cliente escaparia de informar o fuso.
        ``mode="before"`` roda antes dessa conversão.
        """
        if isinstance(value, datetime):
            return value
        if isinstance(value, str) and _DATE_AND_TIME.match(value):
            return value
        raise ValueError(
            "informe data e hora com fuso em texto, "
            "por exemplo 2026-09-14T11:30:00-03:00"
        )

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
        """Recusa fim anterior ao início, como o CHECK do banco
        Fim igual ao inicio passa."""
        if self.finished_at < self.started_at:
            raise ValueError("finished_at não pode ser anterior a started_at")
        return self


class MaintenanceRead(BaseModel):
    """Dados devolvidos pela API, montados a partir do ``MaintenanceModel``.

    Não repete as regras da entrada: ``service``, ``maintenance_type`` e
    ``problem`` são ``str``, para que um valor gravado fora do Service (no
    banco, ``problem`` é texto livre) não impeça a leitura do registro.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    machine_id: int
    technician_id: int
    operator_id: int | None
    started_at: datetime
    finished_at: datetime
    elapsed_time: timedelta  # no JSON, duração ISO 8601 (ex.: "PT2H30M")
    service: str
    maintenance_type: str
    problem: str | None
    description: str | None
    # Lido de ``MaintenanceModel.subset_links``; no JSON sai como ``subset_ids``
    subset_ids: list[int] = Field(validation_alias="subset_links")

    @field_validator("subset_ids", mode="before")
    @classmethod
    def extract_subset_ids(cls, links: Any) -> list[int]:
        """Troca cada vínculo pelo id do subconjunto, em ordem crescente.

        A sessão precisa estar aberta: ler ``subset_links`` faz uma consulta.
        """
        return sorted(link.subset_id for link in links)
