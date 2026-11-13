import sqlalchemy.orm as orm

from app.infrastructure.base.base_repository import GenericRepository
from app.models.operator_model import OperatorModel


class OperatorRepository(GenericRepository[OperatorModel]):
    def __init__(self, session: orm.Session) -> None:
        super().__init__(session, OperatorModel)
