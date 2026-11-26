"""Regras de negócio dos Services, chamados diretamente (sem o schema).

Os Services se defendem sozinhos: a mesma regra vale para quem não passa
pela API. Os limites de data são derivados das constantes do Service, para
que o teste continue certo se elas mudarem.
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.models import MaintenanceModel, SubsetMaintenanceModel, TechnicianModel
from app.services.exceptions import (
    DomainError,
    DuplicateOperatorError,
    DuplicateSubsetLinkError,
    InactiveFunctionError,
    InvalidDescriptionError,
    InvalidMaintenancePeriodError,
    InvalidMaintenanceTypeError,
    InvalidOperatorNameError,
    InvalidProblemError,
    InvalidServiceError,
    NotFoundError,
    SubsetMachineMismatchError,
)
from app.services.maintenance_service import (
    CLOCK_TOLERANCE,
    EARLIEST_START,
    MaintenanceService,
)
from app.services.operator_service import OperatorService
from app.services.technician_service import TechnicianService
from tests.integration.conftest import MISSING_ID

BRT = timezone(timedelta(hours=-3))
START = datetime(2026, 11, 20, 8, 0, tzinfo=BRT)
MARGIN = timedelta(minutes=1)  # folga para o relógio andar durante o teste


@pytest.fixture
def create(session, data):
    def call(**changes):
        values = dict(
            machine_id=data.machine, technician_id=data.technician,
            started_at=START, finished_at=START + timedelta(hours=1),
            service="Reparo", maintenance_type="Corretiva", problem="Mecânico",
        )
        return MaintenanceService(session).create_maintenance(**(values | changes))

    return call


# ------------------------------------------------------------ manutenção


def test_create_maintenance_persists_and_links(create, session, data):
    maintenance = create(operator_id=data.operator, subset_ids=data.subsets)
    session.expire_all()
    stored = session.get(MaintenanceModel, maintenance.id)
    assert stored.operator_id == data.operator
    assert {link.subset_id for link in stored.subset_links} == set(data.subsets)


@pytest.mark.parametrize(
    ("field", "resource"),
    [("machine_id", "machine"), ("technician_id", "technician"), ("operator_id", "operator")],
)
def test_missing_reference(create, table_counts, field, resource):
    before = table_counts()
    with pytest.raises(NotFoundError) as error:
        create(**{field: MISSING_ID})
    assert error.value.details == {"resource": resource, "id": MISSING_ID}
    assert table_counts() == before


@pytest.mark.parametrize(
    ("changes", "error"),
    [
        ({"service": "reparo"}, InvalidServiceError),
        ({"maintenance_type": "Preditiva"}, InvalidMaintenanceTypeError),
        ({"problem": None}, InvalidProblemError),
        ({"problem": "   "}, InvalidProblemError),
        ({"problem": "Hidráulico"}, InvalidProblemError),
        ({"maintenance_type": "Preventiva", "problem": "Hidráulico"}, InvalidProblemError),
        ({"description": "  "}, InvalidDescriptionError),
        ({"finished_at": START - timedelta(seconds=1)}, InvalidMaintenancePeriodError),
        ({"finished_at": None}, InvalidMaintenancePeriodError),
        ({"started_at": START.replace(tzinfo=None)}, InvalidMaintenancePeriodError),
        ({"started_at": EARLIEST_START - timedelta(seconds=1)}, InvalidMaintenancePeriodError),
        # Datas que o PostgreSQL grava, mas o Python não lê de volta.
        ({"started_at": datetime(1, 1, 1, tzinfo=timezone.utc)}, InvalidMaintenancePeriodError),
        ({"finished_at": datetime(9999, 12, 31, 23, 59, tzinfo=timezone(timedelta(hours=-14)))},
         InvalidMaintenancePeriodError),
    ],
    ids=str,
)
def test_rejects_invalid_maintenance_without_writing(create, table_counts, changes, error):
    before = table_counts()
    with pytest.raises(error):
        create(**changes)
    assert table_counts() == before


def test_accepted_period_limits(create):
    create(started_at=EARLIEST_START, finished_at=EARLIEST_START)


def test_finished_at_within_clock_tolerance(create):
    finished = datetime.now(timezone.utc) + CLOCK_TOLERANCE - MARGIN
    create(started_at=finished - timedelta(hours=1), finished_at=finished)


def test_finished_at_beyond_clock_tolerance(create):
    finished = datetime.now(timezone.utc) + CLOCK_TOLERANCE + MARGIN
    with pytest.raises(InvalidMaintenancePeriodError):
        create(started_at=finished - timedelta(hours=1), finished_at=finished)


@pytest.mark.parametrize(
    "problem", [None, "Elétrico"], ids=["sem-problema", "com-problema"]
)
def test_preventive_problem_is_optional(create, problem):
    assert create(maintenance_type="Preventiva", problem=problem).problem == problem


@pytest.mark.parametrize(
    ("invalid", "error"),
    [("foreign", SubsetMachineMismatchError), ("missing", NotFoundError),
     ("repeated", DuplicateSubsetLinkError)],
)
def test_one_invalid_subset_undoes_everything(create, table_counts, data, invalid, error):
    second = {"foreign": data.foreign_subset, "missing": MISSING_ID,
              "repeated": data.subsets[0]}[invalid]
    before = table_counts()
    with pytest.raises(error):
        create(subset_ids=[data.subsets[0], second])
    assert table_counts() == before


def test_link_subset_rules(create, session, data):
    service = MaintenanceService(session)
    maintenance_id = create().id
    link = service.link_subset(maintenance_id, data.subsets[0])
    assert (link.maintenance_id, link.subset_id) == (maintenance_id, data.subsets[0])
    for args, error in [
        ((maintenance_id, data.subsets[0]), DuplicateSubsetLinkError),
        ((maintenance_id, data.foreign_subset), SubsetMachineMismatchError),
        ((MISSING_ID, data.subsets[0]), NotFoundError),
    ]:
        with pytest.raises(error):
            service.link_subset(*args)
    assert [l.subset_id for l in session.get(MaintenanceModel, maintenance_id).subset_links] == [
        data.subsets[0]
    ]


# ------------------------------------------------------------- operador


def test_operator_name_is_normalized(session, data):
    """Espaços reduzidos e acento decomposto (comum em texto colado) recomposto."""
    operator = OperatorService(session).create_operator("  José   D'Ávila-Lima ")
    assert operator.name == "José D'Ávila-Lima"


@pytest.mark.parametrize(
    "name",
    ["", "   ", "Ana", "Ana 2", "Ana -", "Ana Lima-", "Ana--Lima Souza", "Ana\x00 Lima",
     "Ana " + "x" * 97, None],
    ids=repr,
)
def test_invalid_operator_name(session, data, table_counts, name):
    before = table_counts()
    with pytest.raises(InvalidOperatorNameError):
        OperatorService(session).create_operator(name)
    assert table_counts() == before


def test_operator_name_limit(session):
    name = "Ana " + "x" * 96  # exatamente 100 caracteres
    assert OperatorService(session).create_operator(name).name == name


def test_duplicate_operator_ignores_case_and_spaces(session, data, table_counts):
    before = table_counts()
    with pytest.raises(DuplicateOperatorError) as error:
        OperatorService(session).create_operator(" ana   SILVA ")
    assert error.value.details == {"existing_id": data.operator, "existing_name": "Ana Silva"}
    assert table_counts() == before


# -------------------------------------------------------------- técnico


def test_technician_requires_existing_active_function(session, data, table_counts):
    service = TechnicianService(session)
    assert service.create_technician("Maria Lima", data.function).function_id == data.function
    before = table_counts()
    with pytest.raises(NotFoundError):
        service.create_technician("Maria Lima", MISSING_ID)
    with pytest.raises(InactiveFunctionError):
        service.create_technician("Maria Lima", data.inactive_function)
    assert table_counts() == before


def test_change_function(session, data):
    service = TechnicianService(session)
    service.change_function(data.technician_in_inactive_function, data.function)
    session.expire_all()
    assert session.get(TechnicianModel, data.technician_in_inactive_function).function_id == data.function


@pytest.mark.parametrize(
    ("technician", "function", "error"),
    [("technician", "inactive_function", InactiveFunctionError),
     (None, "function", NotFoundError), ("technician", None, NotFoundError)],
)
def test_change_function_rules(session, data, technician, function, error):
    technician_id = getattr(data, technician) if technician else MISSING_ID
    function_id = getattr(data, function) if function else MISSING_ID
    with pytest.raises(error):
        TechnicianService(session).change_function(technician_id, function_id)
    session.expire_all()
    assert session.get(TechnicianModel, data.technician).function_id == data.function


@pytest.mark.xfail(reason="Revisão de 25/11/2026: TechnicianService não valida o nome",
                   raises=pytest.fail.Exception)
def test_technician_blank_name_is_rejected(session, data):
    with pytest.raises(DomainError):
        TechnicianService(session).create_technician("   ", data.function)
