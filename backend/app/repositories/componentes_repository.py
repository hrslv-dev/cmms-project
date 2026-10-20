"""Consultas e operações de persistência para componentes de máquinas."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.domain.componentes import Components
from backend.app.repositories.base_repository import BaseRepository


class ComponentsRepository(BaseRepository[Components]):
    """Repository de componentes, com acesso às consultas específicas da entidade."""

    def __init__(self, session: Session) -> None:
        """Vincula o modelo de componentes à sessão da unidade de trabalho.

        Essa configuração permite reutilizar o CRUD comum com a mesma sessão
        que o serviço usa para relacionar componentes e máquinas.
        """
        super().__init__(session, Components)

    def list_by_machine_id(
        self,
        machine_id: int,
        *,
        offset: int = 0,
        limit: int | None = 100,
    ) -> list[Components]:
        """Lista os componentes ligados a uma máquina, com paginação.

        A FK torna essa consulta necessária para carregar os componentes de
        uma máquina sem espalhar detalhes SQL pelos serviços.
        """
        statement = select(Components).where(Components.maquina_id == machine_id)
        return self._list(statement, offset=offset, limit=limit)

    def list_by_name(
        self,
        name: str,
        *,
        offset: int = 0,
        limit: int | None = 100,
    ) -> list[Components]:
        """Lista componentes com nome exato, sem presumir que o nome seja único.

        A busca fica aqui por consultar uma coluna persistida e pode retornar
        resultados de qualquer máquina que tenha esse mesmo nome.
        """
        statement = select(Components).where(Components.nome == name)
        return self._list(statement, offset=offset, limit=limit)
