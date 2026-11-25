"""Schemas da API para máquinas."""

from pydantic import BaseModel, ConfigDict


class MachineRead(BaseModel):
    """Dados devolvidos pela API, montados a partir do ``MachineModel``."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
