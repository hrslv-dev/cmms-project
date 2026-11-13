import sqlalchemy as sq
import sqlalchemy.orm as orm

from app.infrastructure.base.base_repository import GenericRepository
from app.models.subset_model import SubsetModel


class SubsetRepository(GenericRepository[SubsetModel]):
    def __init__(self, session: orm.Session) -> None:
        super().__init__(session, SubsetModel)

    def list_by_machine_id(self, machine_id: int) -> list[SubsetModel]:
        """Lista os subconjuntos associados à máquina informada."""
        stmt = sq.select(SubsetModel).where(
            SubsetModel.machine_id == machine_id
        )
        return list(self.session.scalars(stmt).all())
