"""Consultas e operações de persistência para operadores."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.operadores import Operador
from backend.app.repositories.base_repository import BaseRepository


class OperadorRepository(BaseRepository[Operador]):
    """Repository de operadores cadastrados no CMMS."""

    def __init__(self, session: Session) -> None:
        """Vincula o modelo de operador à sessão da unidade de trabalho.

        O repository usa essa sessão compartilhada para consultar e incluir
        operadores dentro da transação coordenada pelo serviço.
        """
        super().__init__(session, Operador)

    def list_by_name(
        self,
        name: str,
        *,
        offset: int = 0,
        limit: int | None = 100,
    ) -> list[Operador]:
        """Lista operadores com nome exato sem supor unicidade no banco.

        O repository encapsula a consulta por coluna e devolve lista porque o
        modelo não declara uma restrição de unicidade para ``nome``.
        """
        statement = select(Operador).where(Operador.nome == name)
        return self._list(statement, offset=offset, limit=limit)
