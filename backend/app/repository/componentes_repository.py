import sqlalchemy as sq
import sqlalchemy.orm as orm

from app.infrastructure.base.base_repository import GenericRepository
from app.models.componentes_model import ComponentesModel


class Componentes_Repository(GenericRepository[ComponentesModel]):
    def __init__(self, session: orm.Session) -> None:
        super().__init__(session, ComponentesModel)

    def list_by_maquinas_id(self, maquina_id: int) -> list[ComponentesModel]:
        """Lista os componentes associados à máquina informada."""
        stmt = sq.select(ComponentesModel).where(
            ComponentesModel.maquina_id == maquina_id
        )
        return list(self.session.scalars(stmt).all())
