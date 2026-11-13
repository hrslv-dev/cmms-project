import sqlalchemy as sq
import sqlalchemy.orm as orm

from app.infrastructure.base.base_repository import GenericRepository
from app.models.maintenance_model import MaintenanceModel


class MaintenanceRepository(GenericRepository[MaintenanceModel]):
    def __init__(self, session: orm.Session) -> None:
        super().__init__(session, MaintenanceModel)

    def list_by_machine(self, machine_id: int) -> list[MaintenanceModel]:
        """Lista as manutenções registradas para a máquina informada."""
        stmt = sq.select(MaintenanceModel).where(
            MaintenanceModel.machine_id == machine_id
        )
        return list(self.session.scalars(stmt).all())

    def list_by_subset(self, subset_id: int) -> list[MaintenanceModel]:
        """Lista as manutenções registradas para o subconjunto informado."""
        stmt = sq.select(MaintenanceModel).where(
            MaintenanceModel.subset_id == subset_id
        )
        return list(self.session.scalars(stmt).all())

    def list_by_technician(self, technician_id: int) -> list[MaintenanceModel]:
        """Lista as manutenções realizadas pelo técnico informado."""
        stmt = sq.select(MaintenanceModel).where(
            MaintenanceModel.technician_id == technician_id
        )
        return list(self.session.scalars(stmt).all())

    def list_by_operator(self, operator_id: int) -> list[MaintenanceModel]:
        """Lista as manutenções associadas ao operador informado."""
        stmt = sq.select(MaintenanceModel).where(
            MaintenanceModel.operator_id == operator_id
        )
        return list(self.session.scalars(stmt).all())
