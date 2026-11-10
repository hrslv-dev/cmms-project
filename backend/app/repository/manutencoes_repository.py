import sqlalchemy as sq
import sqlalchemy.orm as orm

from app.infrastructure.base.base_repository import GenericRepository
from app.models.manutencoes_model import ManutencoesModel


class ManutencoesRepository(GenericRepository[ManutencoesModel]):
    def __init__(self, session: orm.Session) -> None:
        super().__init__(session, ManutencoesModel)

    def list_by_maquinas(self, maquina_id: int) -> list[ManutencoesModel]:
        """Lista as manutenções registradas para a máquina informada."""
        stmt = sq.select(ManutencoesModel).where(
            ManutencoesModel.maquina_id == maquina_id
        )
        return list(self.session.scalars(stmt).all())

    def list_by_componentes(self, componente_id: int) -> list[ManutencoesModel]:
        """Lista as manutenções registradas para o componente informado."""
        stmt = sq.select(ManutencoesModel).where(
            ManutencoesModel.componente_id == componente_id
        )
        return list(self.session.scalars(stmt).all())

    def list_by_tecnicos(self, tecnico_id: int) -> list[ManutencoesModel]:
        """Lista as manutenções realizadas pelo técnico informado."""
        stmt = sq.select(ManutencoesModel).where(
            ManutencoesModel.tecnico_id == tecnico_id
        )
        return list(self.session.scalars(stmt).all())

    def list_by_operadores(self, operador_id: int) -> list[ManutencoesModel]:
        """Lista as manutenções associadas ao operador informado."""
        stmt = sq.select(ManutencoesModel).where(
            ManutencoesModel.operador_id == operador_id
        )
        return list(self.session.scalars(stmt).all())
