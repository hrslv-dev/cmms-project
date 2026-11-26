from collections.abc import Iterable
from datetime import datetime, timedelta, timezone

import sqlalchemy.orm as orm

from app.models.maintenance_model import MaintenanceModel
from app.models.subset_maintenance_model import SubsetMaintenanceModel
from app.repository.machine_repository import MachineRepository
from app.repository.maintenance_repository import MaintenanceRepository
from app.repository.operator_repository import OperatorRepository
from app.repository.subset_maintenance_repository import SubsetMaintenanceRepository
from app.repository.subset_repository import SubsetRepository
from app.repository.technician_repository import TechnicianRepository
from app.services.enums import MaintenanceType, ProblemCategory, ServiceCategory
from app.services.exceptions import (
    DuplicateSubsetLinkError,
    InvalidDescriptionError,
    InvalidMaintenancePeriodError,
    InvalidMaintenanceTypeError,
    InvalidProblemError,
    InvalidServiceError,
    NotFoundError,
    SubsetMachineMismatchError,
)

# Início mais antigo aceito. Barra erros de digitação ("0226") e datas extremas
# que o PostgreSQL grava, mas o ``datetime`` do Python não consegue ler de volta.
EARLIEST_START = datetime(2000, 1, 1, tzinfo=timezone.utc)

# Folga para o relógio de quem envia estar adiantado em relação ao do servidor.
CLOCK_TOLERANCE = timedelta(minutes=5)


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

    3. Período: ``started_at`` e ``finished_at`` são obrigatórios e precisam
       ter fuso, e o fim não pode ser anterior ao início. No banco,
       ``finished_at`` ainda aceita NULL. A ordem também é garantida pelo CHECK
       ``ck_maintenance_finished_after_started``; checar aqui antes dá uma
       mensagem clara em vez de um ``IntegrityError``. O período também deve
       caber na faixa ``EARLIEST_START <= started_at <= finished_at <= agora +
       CLOCK_TOLERANCE`` (só da aplicação; o banco não tem esses limites).
    4. ``service`` deve ser um valor de ``ServiceCategory`` (as 10 opções do
       CHECK ``ck_maintenance_service``). Pelo mesmo motivo da regra 3, a
       checagem vem antes de o banco recusar a linha.
    5. ``description`` é opcional (``None``), mas, se informada, não pode ser
       vazia nem só espaços. Aqui o valor em branco é RECUSADO; convertê-lo em
       ``None`` é papel do schema.

    Transação: cada método público é uma unidade de trabalho; em qualquer
    erro, ``rollback`` desfaz tudo o que o caso de uso já havia enviado.
    """

    def __init__(self, session: orm.Session) -> None:
        self.session = session
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
        started_at: datetime,
        finished_at: datetime,
        service: ServiceCategory | str,
        maintenance_type: MaintenanceType | str,
        operator_id: int | None = None,
        problem: ProblemCategory | str | None = None,
        description: str | None = None,
        subset_ids: Iterable[int] = (),
    ) -> MaintenanceModel:
        """Registra uma manutenção e, opcionalmente, vincula subconjuntos.

        ``started_at``/``finished_at`` são ``datetime`` com fuso, por exemplo
        ``datetime(2026, 9, 14, 11, 30, tzinfo=ZoneInfo("America/Sao_Paulo"))``.
        Ambos são obrigatórios: só se registra manutenção já encerrada.

        Tudo acontece em UMA transação: se qualquer subconjunto for inválido,
        nem a manutenção nem os vínculos anteriores ficam gravados.
        """
        try:
            self._validate_period(started_at, finished_at)
            self._validate_description(description)
            self._ensure_exists(self.machine_repository, "machine", machine_id)
            self._ensure_exists(self.technician_repository, "technician", technician_id)
            if operator_id is not None:
                self._ensure_exists(self.operator_repository, "operator", operator_id)

            service_ = self._parse_service(service)
            type_ = self._parse_type(maintenance_type)
            problem_value = self._validate_problem(type_, problem)

            maintenance = self.maintenance_repository.add(
                MaintenanceModel(
                    machine_id=machine_id,
                    technician_id=technician_id,
                    operator_id=operator_id,
                    started_at=started_at,
                    finished_at=finished_at,
                    service=service_.value,
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
                raise NotFoundError("maintenance", maintenance_id)
            link = self._link_subset(maintenance, subset_id)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        return link

    # ------------------------------------------------------------------ regras

    def _link_subset(
        self, maintenance: MaintenanceModel, subset_id: int
    ) -> SubsetMaintenanceModel:
        """Aplica a regra da mesma máquina e grava o vínculo (sem commit)."""
        subset = self.subset_repository.search_by_id(subset_id)
        if subset is None:
            raise NotFoundError("subset", subset_id)
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
    def _parse_service(value: ServiceCategory | str) -> ServiceCategory:
        """Converte para ``ServiceCategory`` ou levanta ``InvalidServiceError``.

        Mesmo padrão de ``_parse_type``: a comparação é exata, diferencia
        maiúsculas/minúsculas e acentos ("reparo" e "Inspecao" são recusados).
        ``None`` e ``""`` também são recusados, pois a coluna é ``NOT NULL``.
        """
        try:
            return ServiceCategory(value)
        except ValueError:
            allowed = ", ".join(s.value for s in ServiceCategory)
            raise InvalidServiceError(
                f"Serviço inválido: {value!r}. Use: {allowed}."
            ) from None

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
    def _validate_description(description: str | None) -> None:
        """Recusa ``description`` em branco, sem alterar o valor recebido."""
        if description is None:
            return
        if not isinstance(description, str) or not description.strip():
            raise InvalidDescriptionError(
                "description deve ser um texto não vazio ou None, "
                f"recebido: {description!r}."
            )

    @staticmethod
    def _validate_period(started_at: datetime, finished_at: datetime) -> None:
        """Exige início e fim (``datetime`` com fuso), em ordem e na faixa aceita.

        Por que exigir o fuso: o PostgreSQL interpreta um horário SEM fuso no
        fuso da sessão do banco. O mesmo "08:00" viraria instantes diferentes
        conforme a configuração da conexão, sem nenhum erro. Recusar é mais
        seguro do que adivinhar.

        Entre ``datetime`` com fuso, o Python compara instantes: os limites
        estão em UTC, mas valem para qualquer fuso recebido. Basta um piso
        para o início e um teto para o fim, porque o fim não pode ser
        anterior ao início.
        """
        to_check = {"started_at": started_at, "finished_at": finished_at}
        for label, value in to_check.items():
            if not isinstance(value, datetime):
                raise InvalidMaintenancePeriodError(
                    f"{label} deve ser data e hora (datetime), recebido: {value!r}."
                )
            if value.utcoffset() is None:
                raise InvalidMaintenancePeriodError(
                    f"{label} precisa de fuso horário, "
                    "por exemplo 2026-09-14T11:30:00-03:00."
                )
        if finished_at < started_at:
            raise InvalidMaintenancePeriodError(
                "finished_at não pode ser anterior a started_at."
            )
        if started_at < EARLIEST_START:
            raise InvalidMaintenancePeriodError(
                "started_at não pode ser anterior a "
                f"{EARLIEST_START.isoformat()}, recebido: {started_at.isoformat()}."
            )
        if finished_at > datetime.now(timezone.utc) + CLOCK_TOLERANCE:
            raise InvalidMaintenancePeriodError(
                "finished_at não pode estar no futuro, "
                f"recebido: {finished_at.isoformat()}."
            )

    @staticmethod
    def _ensure_exists(repository, resource: str, entity_id: int) -> None:
        if repository.search_by_id(entity_id) is None:
            raise NotFoundError(resource, entity_id)
