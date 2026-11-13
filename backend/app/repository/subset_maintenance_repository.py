import sqlalchemy as sq
import sqlalchemy.orm as orm

from app.infrastructure.base.base_repository import GenericRepository
from app.models.subset_maintenance_model import SubsetMaintenanceModel


class SubsetMaintenanceRepository(GenericRepository[SubsetMaintenanceModel]):
    """Persistência dos vínculos entre manutenções e subconjuntos.

    Vincular é ``add(SubsetMaintenanceModel(maintenance_id=..., subset_id=...))``
    e desvincular é ``delete(vinculo)``, ambos herdados do repository genérico.
    Este repository não valida se o subconjunto pertence à máquina da
    manutenção; quem chama (o Service) decide isso antes de vincular.
    """

    def __init__(self, session: orm.Session) -> None:
        super().__init__(session, SubsetMaintenanceModel)

    def search_by_pair(
        self, maintenance_id: int, subset_id: int
    ) -> SubsetMaintenanceModel | None:
        """Busca o vínculo entre a manutenção e o subconjunto, se existir.

        O par é único no banco, então há no máximo um resultado.
        """
        stmt = sq.select(SubsetMaintenanceModel).where(
            SubsetMaintenanceModel.maintenance_id == maintenance_id,
            SubsetMaintenanceModel.subset_id == subset_id,
        )
        return self.session.scalars(stmt).one_or_none()
