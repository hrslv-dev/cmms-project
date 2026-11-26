import sqlalchemy as sq
import sqlalchemy.orm as orm

from app.infrastructure.base.base_repository import GenericRepository
from app.models.machine_model import MachineModel


class MachineRepository(GenericRepository[MachineModel]):
    def __init__(self, session: orm.Session) -> None:
        super().__init__(session, MachineModel)

    def list_ordered_by_name(self) -> list[MachineModel]:
        """Lista todas as máquinas em ordem alfabética.

        O ``id`` desempata nomes iguais. Sem ele, o PostgreSQL pode devolver
        máquinas de mesmo nome em ordens diferentes a cada consulta.
        A ordem alfabética segue a collation do banco (ver ``SHOW lc_collate``).
        """
        stmt = sq.select(MachineModel).order_by(MachineModel.name, MachineModel.id)
        return list(self.session.scalars(stmt).all())
