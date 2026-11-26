import sqlalchemy.orm as orm

from app.models.machine_model import MachineModel
from app.repository.machine_repository import MachineRepository


class MachineService:
    """Casos de uso de máquinas.

    Transação: os métodos atuais só leem, então não fazem ``commit``. A
    consulta abre uma transação (o SQLAlchemy 2.0 inicia uma automaticamente),
    que termina quando quem criou a sessão a fecha. Fazer ``commit`` aqui
    também expiraria os objetos devolvidos (``expire_on_commit``), e ler
    ``machine.name`` depois faria uma nova consulta.
    """

    def __init__(self, session: orm.Session) -> None:
        self.session = session
        self.machine_repository = MachineRepository(session)

    def list_machines(self) -> list[MachineModel]:
        """Lista todas as máquinas em ordem alfabética (``id``, ``name``).

        Não há regra de filtragem: todas as máquinas cadastradas são
        devolvidas. Sem máquinas, devolve a lista vazia.
        """
        return self.machine_repository.list_ordered_by_name()
