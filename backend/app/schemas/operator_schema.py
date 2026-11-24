"""Schemas da API para operadores."""

from pydantic import BaseModel, ConfigDict, Field


class OperatorCreate(BaseModel):
    """Dados que o cliente envia para cadastrar um operador.

    Aqui só se exige que ``name`` exista e seja texto. As regras do nome
    (normalização, nome e sobrenome, caracteres, tamanho e duplicidade) ficam
    no ``OperatorService``.
    """

    # Recusa os campos que não estejam na ficha
    # Extra forbid diz que é impossível mandar alguma informação além de name pela tela
    model_config = ConfigDict(extra="forbid")

    # Não tem valor padrão, ou seja, é obrigatório
    name: str = Field(
        description="Nome e sobrenome do operador.",
        examples=["Ana-Maria D'Ávila"],
    )
