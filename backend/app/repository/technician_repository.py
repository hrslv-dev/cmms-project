import sqlalchemy as sq
import sqlalchemy.orm as orm

from app.infrastructure.base.base_repository import GenericRepository
from app.models.technician_model import TechnicianModel


class TechnicianRepository(GenericRepository[TechnicianModel]):
    def __init__(self, session: orm.Session) -> None:
        super().__init__(session, TechnicianModel)

    def list_by_function(self, function_id: int) -> list[TechnicianModel]:
        """Lista os técnicos que exercem a função técnica informada."""
        stmt = sq.select(TechnicianModel).where(
            TechnicianModel.function_id == function_id
        )
        return list(self.session.scalars(stmt).all())
