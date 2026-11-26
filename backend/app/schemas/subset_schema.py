"""Schemas da API para subconjuntos."""

from pydantic import BaseModel, ConfigDict


class SubsetRead(BaseModel):
    """Dados devolvidos pela API, montados a partir do ``SubsetModel``.

    Sem ``machine_id``: a lista já é pedida para uma máquina específica.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
