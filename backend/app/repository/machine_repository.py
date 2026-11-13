import sqlalchemy.orm as orm

from app.infrastructure.base.base_repository import GenericRepository
from app.models.machine_model import MachineModel


class MachineRepository(GenericRepository[MachineModel]):
    def __init__(self, session: orm.Session) -> None:
        super().__init__(session, MachineModel)
