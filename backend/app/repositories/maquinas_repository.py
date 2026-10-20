"""Consultas e operações de persistência para máquinas."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.domain.maquina import Maquina
from backend.app.repositories.base_repository import BaseRepository


class MaquinaRepository(BaseRepository[Maquina]):
    """Repository de máquinas, com CRUD comum e consultas por nome."""

    def __init__(self, session: Session) -> None:
        """Vincula o modelo de máquina à sessão da unidade de trabalho.

        A sessão compartilhada permite que o serviço controle a transação
        enquanto este repository concentra as consultas de máquinas.
        """
        super().__init__(session, Maquina)

    def list_by_name(
        self,
        name: str,
        *,
        offset: int = 0,
        limit: int | None = 100,
    ) -> list[Maquina]:
        """Lista máquinas com nome exato, sem presumir uma restrição única.

        A busca por nome é própria da entidade e retorna uma lista para
        continuar correta mesmo se nomes repetidos forem permitidos no banco.
        """
        statement = select(Maquina).where(Maquina.nome == name)
        return self._list(statement, offset=offset, limit=limit)

    def search_id(self, order_id: int) -> Maquina | None:
        """Mantém o nome antigo de busca por ID e delega ao CRUD compartilhado.

        O alias evita quebrar chamadas existentes enquanto ``get_by_id`` é o
        nome recomendado para novos usos.
        """
        return self.get_by_id(order_id)

    def search_name(self, order_name: str) -> Maquina | None:
        """Mantém a busca antiga por nome e retorna a primeira correspondência.

        Como o modelo não declara nomes únicos, o método novo
        ``list_by_name`` é o recomendado; este alias existe para compatibilidade.
        """
        matches = self.list_by_name(order_name, limit=1)
        return matches[0] if matches else None

    def see_all(self) -> list[Maquina]:
        """Preserva a listagem antiga sem limite para chamadas existentes.

        Novos usos devem preferir ``list_all`` com paginação para evitar buscar
        toda a tabela quando não for necessário.
        """
        return self.list_all(limit=None)
