"""Schema da API para respostas de erro."""

from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Formato único de todo erro devolvido pela API."""

    code: str = Field(description="Identificador fixo do erro.")
    message: str = Field(description="Texto em português, pronto para exibir.")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Dados extras do erro."
    )
