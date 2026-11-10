from typing import Any, Generic, TypeVar

import sqlalchemy as sq
import sqlalchemy.orm as orm

from app.infrastructure.base.base_model import Base


ModelType = TypeVar("ModelType", bound=Base)


class GenericRepository(Generic[ModelType]):
    """Operações de persistência compartilhadas pelas entidades do sistema.

    O repository usa a sessão recebida, mas não confirma nem reverte a
    transação. Essa decisão pertence ao service ou à camada que o chamou.
    """

    def __init__(self, session: orm.Session, model: type[ModelType]) -> None:
        self.session = session
        self.model = model

    def list_all(
        self, limit: int | None = None, offset: int = 0
    ) -> list[ModelType]:
        """Retorna os registros da entidade, com paginação opcional."""
        stmt = sq.select(self.model).offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(self.session.scalars(stmt).all())

    def add(self, model: ModelType) -> ModelType:
        """Adiciona uma entidade à sessão e a envia ao banco sem commit."""
        self.session.add(model)
        self.session.flush()
        return model

    def search_by_id(self, model_id: int) -> ModelType | None:
        """Busca uma entidade pela chave primária ou retorna ``None``."""
        return self.session.get(self.model, model_id)

    def update(self, model: ModelType) -> ModelType:
        """Mescla alterações de uma entidade, inclusive se estiver detached."""
        updated_model = self.session.merge(model)
        self.session.flush()
        return updated_model

    def update_by_id(self, model_id: int, **values: Any) -> ModelType | None:
        """Atualiza os campos informados; retorna ``None`` se não existir."""
        model = self.search_by_id(model_id)
        if model is None:
            return None

        for field, value in values.items():
            if field == "id":
                raise ValueError("O ID da entidade não pode ser alterado.")
            if not hasattr(model, field):
                raise ValueError(f"Campo inexistente em {self.model.__name__}: {field}")
            setattr(model, field, value)

        self.session.flush()
        return model

    def delete(self, model: ModelType) -> None:
        """Marca uma entidade para exclusão e envia a operação ao banco."""
        self.session.delete(model)
        self.session.flush()

    def delete_by_id(self, model_id: int) -> bool:
        """Exclui pela chave primária e indica se a entidade foi encontrada."""
        model = self.search_by_id(model_id)
        if model is None:
            return False

        self.delete(model)
        return True
