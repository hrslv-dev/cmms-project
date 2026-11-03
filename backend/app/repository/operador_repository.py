from sqlalchemy.orm import Session

from app.infrastructure.base.base_repository import GenericRepository
from app.models.operadores_model import OperadorModel


class OperadorRepository(GenericRepository[OperadorModel]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, OperadorModel)
