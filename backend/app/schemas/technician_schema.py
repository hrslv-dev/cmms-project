"""Schemas da API para técnicos."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


class TechnicianCreate(BaseModel):
    """Dados que o cliente envia para cadastrar um técnico.

    A existência da função técnica e a exigência de que ela esteja ativa são
    regras do ``TechnicianService``.
    """

    # Recusa os campos que não estejam na ficha
    model_config = ConfigDict(extra="forbid")

    # Os espaços das pontas são removidos antes de medir o tamanho. O máximo é o
    # mesmo da coluna ``technicians.name VARCHAR(100)``.
    name: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=5, max_length=100),
    ]
    function_id: int = Field(gt=0)


class TechnicianResponse(BaseModel):
    """Dados devolvidos pela API, montados a partir do ``TechnicianModel``."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    function_id: int
