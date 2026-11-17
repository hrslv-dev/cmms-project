from collections.abc import Iterable
from datetime import date, time

import sqlalchemy.orm as orm

from app.models.maintenance_model import MaintenanceModel
from app.models.subset_maintenance_model import SubsetMaintenanceModel
from app.repository.machine_repository import MachineRepository
from app.repository.maintenance_repository import MaintenanceRepository
from app.repository.operator_repository import OperatorRepository
from app.repository.subset_maintenance_repository import SubsetMaintenanceRepository
from app.repository.subset_repository import SubsetRepository
from app.repository.technician_repository import TechnicianRepository
from app.services.enums import MaintenanceType, ProblemCategory
from app.services.exceptions import (
    DuplicateSubsetLinkError,
    InvalidMaintenanceTypeError,
    InvalidProblemError,
    NotFoundError,
    SubsetMachineMismatchError,
    TimerStateError,
)
from app.services.maintenance_timer import MaintenanceTimer


class MaintenanceService:
    """Casos de uso de manutenções e do vínculo com subconjuntos.

    Regras aplicadas aqui (o banco não as garante):

    1. Um subconjunto só pode ser vinculado a uma manutenção da MESMA máquina.
       Ressalva: a checagem é "ler, comparar, gravar". Ela não protege contra
       escrita direta no banco nem contra outra transação que altere
       ``maintenance.machine_id`` ao mesmo tempo. A proteção completa exigiria
       trigger ou FK composta no PostgreSQL — decisão de esquema do usuário.
    2. ``problem`` deve ser um valor de ``ProblemCategory``. Em corretiva é
       obrigatório (vazio ou só espaços é recusado); em preventiva é opcional.
       No banco a coluna continua ``TEXT`` livre.

    Horário: NÃO há validação. Um ``time_end`` menor que ``time_start`` é
    aceito e o banco o trata como passagem pela meia-noite (14:00 → 13:00
    resulta em 23 horas). Essa foi uma decisão explícita de negócio.

    Transação: cada método público é uma unidade de trabalho; em qualquer
    erro, ``rollback`` desfaz tudo o que o caso de uso já havia enviado.
    """

    def __init__(
        self, session: orm.Session, timer: MaintenanceTimer | None = None
    ) -> None:
        self.session = session
        # O cronômetro só é criado (a partir do .env) quando um método de
        # cronômetro é usado; create_maintenance funciona sem a chave.
        self._timer = timer
        self.maintenance_repository = MaintenanceRepository(session)
        self.machine_repository = MachineRepository(session)
        self.technician_repository = TechnicianRepository(session)
        self.operator_repository = OperatorRepository(session)
        self.subset_repository = SubsetRepository(session)
        self.link_repository = SubsetMaintenanceRepository(session)

    def create_maintenance(
        self,
        *,
        machine_id: int,
        technician_id: int,
        maintenance_date: date,
        time_start: time,
        service: str,
        maintenance_type: MaintenanceType | str,
        operator_id: int | None = None,
        time_end: time | None = None,
        problem: ProblemCategory | str | None = None,
        description: str | None = None,
        subset_ids: Iterable[int] = (),
    ) -> MaintenanceModel:
        """Registra uma manutenção e, opcionalmente, vincula subconjuntos.

        Tudo acontece em UMA transação: se qualquer subconjunto for inválido,
        nem a manutenção nem os vínculos anteriores ficam gravados.
        """
        try:
            self._ensure_exists(self.machine_repository, "Máquina", machine_id)
            self._ensure_exists(self.technician_repository, "Técnico", technician_id)
            if operator_id is not None:
                self._ensure_exists(self.operator_repository, "Operador", operator_id)

            type_ = self._parse_type(maintenance_type)
            problem_value = self._validate_problem(type_, problem)

            maintenance = self.maintenance_repository.add(
                MaintenanceModel(
                    machine_id=machine_id,
                    technician_id=technician_id,
                    operator_id=operator_id,
                    maintenance_date=maintenance_date,
                    time_start=time_start,
                    time_end=time_end,
                    service=service,
                    maintenance_type=type_.value,
                    problem=problem_value,
                    description=description,
                )
            )
            for subset_id in subset_ids:
                self._link_subset(maintenance, subset_id)

            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        return maintenance

    def link_subset(self, maintenance_id: int, subset_id: int) -> SubsetMaintenanceModel:
        """Vincula um subconjunto a uma manutenção já existente."""
        try:
            maintenance = self.maintenance_repository.search_by_id(maintenance_id)
            if maintenance is None:
                raise NotFoundError("Manutenção", maintenance_id)
            link = self._link_subset(maintenance, subset_id)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        return link

    # -------------------------------------------------------------- cronômetro

    @property
    def timer(self) -> MaintenanceTimer:
        if self._timer is None:
            self._timer = MaintenanceTimer.from_env()
        return self._timer

    def start_timer(self) -> str:
        """Botão "Iniciar manutenção": devolve o token com a hora de início.

        Não grava nada no banco (ver limitações em ``maintenance_timer``).
        """
        return self.timer.start()

    def finish_timer(self, token: str) -> str:
        """Botão "Encerrar manutenção": devolve o token com início e fim."""
        return self.timer.finish(token)

    def create_maintenance_from_timer(
        self,
        token: str,
        *,
        machine_id: int,
        technician_id: int,
        service: str,
        maintenance_type: MaintenanceType | str,
        operator_id: int | None = None,
        problem: ProblemCategory | str | None = None,
        description: str | None = None,
        subset_ids: Iterable[int] = (),
    ) -> MaintenanceModel:
        """Cadastro final: data e horários saem do token, não do cliente.

        ``maintenance_date`` é a data do INÍCIO. Se a manutenção cruzar a
        meia-noite, o banco soma 24 h ao calcular ``elapsed_time``. Uma duração
        de 24 h ou mais não cabe em dois campos TIME e seria registrada errada;
        não há validação para isso, conforme decidido para os horários.
        """
        data = self.timer.read(token)
        if data.end is None:
            raise TimerStateError(
                "A manutenção precisa ser encerrada antes do cadastro."
            )
        return self.create_maintenance(
            machine_id=machine_id,
            technician_id=technician_id,
            operator_id=operator_id,
            maintenance_date=data.start.date(),
            time_start=data.start.time().replace(tzinfo=None),
            time_end=data.end.time().replace(tzinfo=None),
            service=service,
            maintenance_type=maintenance_type,
            problem=problem,
            description=description,
            subset_ids=subset_ids,
        )

    # ------------------------------------------------------------------ regras

    def _link_subset(
        self, maintenance: MaintenanceModel, subset_id: int
    ) -> SubsetMaintenanceModel:
        """Aplica a regra da mesma máquina e grava o vínculo (sem commit)."""
        subset = self.subset_repository.search_by_id(subset_id)
        if subset is None:
            raise NotFoundError("Subconjunto", subset_id)
        if subset.machine_id != maintenance.machine_id:
            raise SubsetMachineMismatchError(
                subset.id, subset.machine_id, maintenance.machine_id
            )
        # O UNIQUE do banco também barraria; checar antes dá um erro claro e
        # evita invalidar a transação com um IntegrityError.
        if self.link_repository.search_by_pair(maintenance.id, subset.id) is not None:
            raise DuplicateSubsetLinkError(maintenance.id, subset.id)
        return self.link_repository.add(
            SubsetMaintenanceModel(maintenance_id=maintenance.id, subset_id=subset.id)
        )

    @staticmethod
    def _parse_type(value: MaintenanceType | str) -> MaintenanceType:
        try:
            return MaintenanceType(value)
        except ValueError:
            allowed = ", ".join(t.value for t in MaintenanceType)
            raise InvalidMaintenanceTypeError(
                f"Tipo de manutenção inválido: {value!r}. Use: {allowed}."
            ) from None

    @staticmethod
    def _validate_problem(
        maintenance_type: MaintenanceType, problem: ProblemCategory | str | None
    ) -> str | None:
        """Retorna o valor a gravar em ``problem`` ou levanta ``InvalidProblemError``.

        Espaços nas pontas são removidos. A comparação diferencia maiúsculas e
        minúsculas: "mecânico" é recusado.
        """
        normalized = problem.strip() if isinstance(problem, str) else problem
        if not normalized:  # None, "" ou só espaços
            if maintenance_type is MaintenanceType.CORRECTIVE:
                raise InvalidProblemError(
                    "Manutenção corretiva exige o campo problem."
                )
            return None
        try:
            return ProblemCategory(normalized).value
        except ValueError:
            allowed = ", ".join(p.value for p in ProblemCategory)
            raise InvalidProblemError(
                f"Problema inválido: {problem!r}. Use: {allowed}."
            ) from None

    @staticmethod
    def _ensure_exists(repository, entity: str, entity_id: int) -> None:
        if repository.search_by_id(entity_id) is None:
            raise NotFoundError(entity, entity_id)
