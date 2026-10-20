"""Consultas e operações de persistência para o histórico de manutenção."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.domain.manutencao import HistoricoManutencao
from backend.app.repositories.base_repository import BaseRepository


class HistoricoManutencaoRepository(BaseRepository[HistoricoManutencao]):
    """Repository para registrar e consultar manutenções realizadas."""

    def __init__(self, session: Session) -> None:
        """Vincula o histórico à sessão da unidade de trabalho.

        Assim, inclusões e consultas do histórico participam da transação
        controlada pelo serviço que as solicitou.
        """
        super().__init__(session, HistoricoManutencao)

    def list_by_machine_id(
        self,
        machine_id: int,
        *,
        offset: int = 0,
        limit: int | None = 100,
    ) -> list[HistoricoManutencao]:
        """Lista manutenções de uma máquina em ordem de chave primária.

        O filtro atende consultas do histórico por ativo e mantém a regra de
        acesso aos dados no repository, onde o relacionamento está mapeado.
        """
        statement = select(HistoricoManutencao).where(
            HistoricoManutencao.maquina_id == machine_id
        )
        return self._list(statement, offset=offset, limit=limit)

    def list_by_technician_id(
        self,
        technician_id: int,
        *,
        offset: int = 0,
        limit: int | None = 100,
    ) -> list[HistoricoManutencao]:
        """Lista os registros associados a um técnico.

        Essa consulta usa a FK de técnico para permitir histórico por pessoa
        sem exigir que a camada de serviço monte SQLAlchemy statements.
        """
        statement = select(HistoricoManutencao).where(
            HistoricoManutencao.tecnico_id == technician_id
        )
        return self._list(statement, offset=offset, limit=limit)

    def list_by_component_id(
        self,
        component_id: int,
        *,
        offset: int = 0,
        limit: int | None = 100,
    ) -> list[HistoricoManutencao]:
        """Lista os registros de manutenção que citam um componente.

        O filtro corresponde à FK obrigatória do histórico e centraliza essa
        consulta de persistência junto das demais consultas da entidade.
        """
        statement = select(HistoricoManutencao).where(
            HistoricoManutencao.componente_id == component_id
        )
        return self._list(statement, offset=offset, limit=limit)

    def list_by_operator_id(
        self,
        operator_id: int,
        *,
        offset: int = 0,
        limit: int | None = 100,
    ) -> list[HistoricoManutencao]:
        """Lista os registros informados por um operador.

        A consulta atende a navegação do histórico por operador usando a FK
        já definida no modelo ORM.
        """
        statement = select(HistoricoManutencao).where(
            HistoricoManutencao.operador_id == operator_id
        )
        return self._list(statement, offset=offset, limit=limit)

    def list_between_dates(
        self,
        start_date: date,
        end_date: date,
        *,
        offset: int = 0,
        limit: int | None = 100,
    ) -> list[HistoricoManutencao]:
        """Lista manutenções entre duas datas, incluindo os limites.

        A consulta por período é própria do histórico e serve relatórios sem
        obrigar outras camadas a conhecer sua coluna de data.
        """
        if start_date > end_date:
            raise ValueError("start_date deve ser anterior ou igual a end_date")

        statement = select(HistoricoManutencao).where(
            HistoricoManutencao.data_manutencao.between(start_date, end_date)
        )
        return self._list(statement, offset=offset, limit=limit)

    def list_by_type(
        self,
        maintenance_type: str,
        *,
        offset: int = 0,
        limit: int | None = 100,
    ) -> list[HistoricoManutencao]:
        """Lista manutenções de um tipo, como preventiva ou corretiva.

        O tipo é um atributo próprio do registro; centralizar o filtro permite
        reutilizá-lo em telas e relatórios de manutenção.
        """
        statement = select(HistoricoManutencao).where(
            HistoricoManutencao.tipo == maintenance_type
        )
        return self._list(statement, offset=offset, limit=limit)
