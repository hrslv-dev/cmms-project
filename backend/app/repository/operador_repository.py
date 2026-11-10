import sqlalchemy.orm as orm

from app.infrastructure.base.base_repository import GenericRepository
from app.models.operadores_model import OperadorModel


class OperadorRepository(GenericRepository[OperadorModel]):
    def __init__(self, session: orm.Session) -> None:
        super().__init__(session, OperadorModel)
