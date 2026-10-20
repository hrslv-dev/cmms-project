"""Consultas e operações de persistência para técnicos."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.domain.tecnicos import Tecnico
from backend.app.repositories.base_repository import BaseRepository


class TecnicoRepository(BaseRepository[Tecnico]):
    """Repository de técnicos cadastrados no CMMS."""

    def __init__(self, session: Session) -> None:
        """Vincula o modelo de técnico à sessão da unidade de trabalho.

        A injeção da sessão deixa o serviço responsável pela transação e este
        repository responsável pelas consultas do cadastro de técnicos.
        """
        super().__init__(session, Tecnico)

    def list_by_name(
        self,
        name: str,
        *,
        offset: int = 0,
        limit: int | None = 100,
    ) -> list[Tecnico]:
        """Lista técnicos com nome exato sem assumir que nomes sejam únicos.

        A busca é uma consulta de persistência recorrente e devolve todos os
        resultados compatíveis com o modelo atual.
        """
        statement = select(Tecnico).where(Tecnico.nome == name)
        return self._list(statement, offset=offset, limit=limit)

    def list_by_function(
        self,
        function: str,
        *,
        offset: int = 0,
        limit: int | None = 100,
    ) -> list[Tecnico]:
        """Lista técnicos pela função cadastrada, como mecânico ou eletricista.

        O filtro consulta uma coluna específica do modelo e permite selecionar
        os profissionais adequados sem espalhar SQL pela camada de serviço.
        """
        statement = select(Tecnico).where(Tecnico.funcao == function)
        return self._list(statement, offset=offset, limit=limit)
