"""Operações de persistência compartilhadas pelos repositories do domínio."""

from typing import Generic, TypeVar

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from backend.app.domain.base import Base


ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Concentra o CRUD comum sem decidir o ciclo da transação.

    Cada repository concreto escolhe seu modelo e acrescenta consultas próprias.
    A sessão é recebida de fora para que serviços controlem commit e rollback.
    """

    def __init__(self, session: Session, model: type[ModelT]) -> None:
        """Guarda a sessão e o modelo usados nas operações comuns.

        Isso evita repetir o mesmo CRUD em cada arquivo e mantém a sessão sob
        controle da camada que inicia a unidade de trabalho.
        """
        self.session = session
        self.model = model

    def add(self, entity: ModelT) -> ModelT:
        """Agenda uma entidade nova para persistência na sessão atual.

        O repository conhece a operação de inclusão, mas não confirma a
        transação; assim, o serviço pode salvar várias alterações atomicamente.
        """
        self.session.add(entity)
        return entity

    def get_by_id(self, entity_id: int) -> ModelT | None:
        """Busca uma entidade pela chave primária.

        A consulta por ID é uma operação básica de qualquer repository e usa
        ``Session.get`` para aproveitar a identidade já carregada na sessão.
        """
        return self.session.get(self.model, entity_id)

    def list_all(
        self,
        *,
        offset: int = 0,
        limit: int | None = 100,
    ) -> list[ModelT]:
        """Lista entidades com paginação para limitar o uso de memória.

        ``limit=None`` permite solicitar explicitamente todos os registros;
        o padrão retorna no máximo cem para manter consultas previsíveis.
        """
        statement = select(self.model)
        return self._list(statement, offset=offset, limit=limit)

    def update_by_id(self, entity_id: int, **changes: object) -> ModelT | None:
        """Aplica alterações a colunas mapeadas sem permitir trocar a chave.

        Validar os campos aqui centraliza a escrita no modelo e evita que um
        payload com nomes desconhecidos seja silenciosamente ignorado.
        Retorna ``None`` quando a entidade não existe; a transação segue aberta.
        """
        mapped_columns = {column.key for column in self.model.__mapper__.column_attrs}
        primary_key_columns = {
            column.key for column in self.model.__mapper__.primary_key
        }
        invalid_fields = set(changes) - mapped_columns
        protected_fields = set(changes) & primary_key_columns

        if invalid_fields:
            fields = ", ".join(sorted(invalid_fields))
            raise ValueError(
                f"Campos não mapeados para {self.model.__name__}: {fields}"
            )
        if protected_fields:
            fields = ", ".join(sorted(protected_fields))
            raise ValueError(f"Não é permitido alterar a chave primária: {fields}")

        entity = self.get_by_id(entity_id)
        if entity is None:
            return None

        for field, value in changes.items():
            setattr(entity, field, value)
        return entity

    def delete_by_id(self, entity_id: int) -> bool:
        """Marca uma entidade existente para remoção na sessão atual.

        A remoção pertence ao repository porque depende do mapeamento ORM;
        ``False`` informa que o ID não foi encontrado. O commit fica com o serviço.
        """
        entity = self.get_by_id(entity_id)
        if entity is None:
            return False

        self.session.delete(entity)
        return True

    def _list(
        self,
        statement: Select[tuple[ModelT]],
        *,
        offset: int,
        limit: int | None,
    ) -> list[ModelT]:
        """Executa uma consulta de lista com ordenação e paginação uniformes.

        A ordenação pela chave primária torna as páginas estáveis; este helper
        também evita duplicar a mesma mecânica nas consultas específicas.
        """
        if offset < 0:
            raise ValueError("offset deve ser maior ou igual a zero")
        if limit is not None and limit < 0:
            raise ValueError("limit deve ser maior ou igual a zero")

        statement = statement.order_by(*self.model.__mapper__.primary_key)
        if limit is not None:
            statement = statement.limit(limit)
        if offset:
            statement = statement.offset(offset)
        return list(self.session.scalars(statement).all())
