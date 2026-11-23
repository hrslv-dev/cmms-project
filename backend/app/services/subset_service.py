import sqlalchemy.orm as orm

from app.models.subset_model import SubsetModel
from app.repository.machine_repository import MachineRepository
from app.repository.subset_repository import SubsetRepository
from app.services.exceptions import NotFoundError


class SubsetService:
    """Casos de uso de subconjuntos.

    Transação: os métodos atuais só leem, então não fazem ``commit``. Ver a
    explicação em ``MachineService``.
    """

    def __init__(self, session: orm.Session) -> None:
        self.session = session
        self.subset_repository = SubsetRepository(session)
        self.machine_repository = MachineRepository(session)

    def list_subsets_by_machine(self, machine_id: int) -> list[SubsetModel]:
        """Lista os subconjuntos da máquina em ordem alfabética.

        Cada item tem ``id``, ``name`` e ``machine_id``.

        A consulta de subconjuntos, sozinha, devolve ``[]`` tanto para uma
        máquina sem subconjuntos quanto para um ``machine_id`` que não existe.
        Por isso a máquina é verificada primeiro:

        - máquina inexistente: levanta ``NotFoundError``;
        - máquina sem subconjuntos: devolve ``[]``.
        """
        if self.machine_repository.search_by_id(machine_id) is None:
            raise NotFoundError("Máquina", machine_id)
        return self.subset_repository.list_by_machine_id(machine_id)
