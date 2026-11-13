import sqlalchemy as sq
import sqlalchemy.orm as orm

from app.infrastructure.base.base_repository import GenericRepository
from app.models.technical_function_model import TechnicalFunctionModel


class TechnicalFunctionRepository(GenericRepository[TechnicalFunctionModel]):
    def __init__(self, session: orm.Session) -> None:
        super().__init__(session, TechnicalFunctionModel)

    def search_by_name(self, name: str) -> TechnicalFunctionModel | None:
        """Busca a função pelo nome exato ou retorna ``None``.

        ``name`` é único no banco, então há no máximo um resultado. A
        comparação diferencia maiúsculas, minúsculas e espaços.
        """
        stmt = sq.select(TechnicalFunctionModel).where(
            TechnicalFunctionModel.name == name
        )
        return self.session.scalars(stmt).one_or_none()

    def list_active(self) -> list[TechnicalFunctionModel]:
        """Lista as funções ativas, as únicas atribuíveis a técnicos."""
        stmt = sq.select(TechnicalFunctionModel).where(
            TechnicalFunctionModel.active.is_(True)
        )
        return list(self.session.scalars(stmt).all())
