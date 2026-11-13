import sqlalchemy.orm as orm

from app.infrastructure.base.base_repository import GenericRepository
from app.models.maquinas_model import MaquinasModel


class MaquinaRepository(GenericRepository[MaquinasModel]):
    def __init__(self, session: orm.Session) -> None:
        super().__init__(session, MaquinasModel)
