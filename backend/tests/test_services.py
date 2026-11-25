"""Regras de negócio dos Services, chamados sem passar pelos schemas."""

from datetime import datetime, timedelta, timezone

import pytest
import sqlalchemy as sq

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
from app.services.machine_service import MachineService
from app.services.maintenance_service import EARLIEST_START, MaintenanceService
from app.services.operator_service import OperatorService
from app.services.subset_service import SubsetService
from app.services.technician_service import TechnicianService

MISSING_ID = 999_999
BRT = timezone(timedelta(hours=-3))
START = datetime(2026, 11, 20, 8, 0, tzinfo=BRT)


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


def count(session, model):
    return session.scalar(sq.select(sq.func.count()).select_from(model))


# ------------------------------------------------------------ manutenção


def test_creates_maintenance_with_subsets(create, data):
    maintenance = create(operator_id=data.operator, subset_ids=data.subsets)
    assert {link.subset_id for link in maintenance.subset_links} == set(data.subsets)
    assert maintenance.elapsed_time == timedelta(hours=1)


def test_operator_and_subsets_are_optional(create):
    maintenance = create()
    assert maintenance.operator_id is None
    assert maintenance.subset_links == []


@pytest.mark.parametrize("field", ["machine_id", "technician_id", "operator_id"])
def test_missing_reference(create, field):
    with pytest.raises(NotFoundError) as error:
        create(**{field: MISSING_ID})
    assert error.value.details == {"resource": field.removesuffix("_id"), "id": MISSING_ID}


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
        ({"started_at": datetime(2026, 11, 20, 8)}, InvalidMaintenancePeriodError),
        ({"started_at": EARLIEST_START - timedelta(seconds=1)}, InvalidMaintenancePeriodError),
        # Datas que o PostgreSQL grava, mas o Python não lê de volta.
        ({"started_at": datetime(1, 1, 1, tzinfo=timezone.utc)}, InvalidMaintenancePeriodError),
        (
            {"finished_at": datetime(9999, 12, 31, 23, 59, tzinfo=timezone(timedelta(hours=-14)))},
            InvalidMaintenancePeriodError,
        ),
    ],
)
def test_rejects_invalid_maintenance(create, session, changes, error):
    with pytest.raises(error):
        create(**changes)
    assert count(session, MaintenanceModel) == 0


def test_period_limits_are_inclusive(create):
    create(started_at=EARLIEST_START)
    create(finished_at=START)  # fim igual ao início


@pytest.mark.parametrize(("minutes", "accepted"), [(4, True), (6, False)])
def test_clock_tolerance(create, minutes, accepted):
    finished_at = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    if accepted:
        create(finished_at=finished_at)
    else:
        with pytest.raises(InvalidMaintenancePeriodError):
            create(finished_at=finished_at)


def test_preventive_without_problem(create):
    assert create(maintenance_type="Preventiva", problem=None).problem is None


@pytest.mark.parametrize("invalid", ["foreign", "missing", "repeated"])
def test_invalid_subset_undoes_everything(create, session, data, invalid):
    second, error = {
        "foreign": (data.foreign_subset, SubsetMachineMismatchError),
        "missing": (MISSING_ID, NotFoundError),
        "repeated": (data.subsets[0], DuplicateSubsetLinkError),
    }[invalid]
    with pytest.raises(error):
        create(subset_ids=[data.subsets[0], second])
    assert count(session, MaintenanceModel) == 0
    assert count(session, SubsetMaintenanceModel) == 0


def test_link_subset(create, session, data):
    service = MaintenanceService(session)
    maintenance_id = create().id
    service.link_subset(maintenance_id, data.subsets[0])
    with pytest.raises(DuplicateSubsetLinkError):
        service.link_subset(maintenance_id, data.subsets[0])
    with pytest.raises(SubsetMachineMismatchError):
        service.link_subset(maintenance_id, data.foreign_subset)
    with pytest.raises(NotFoundError):
        service.link_subset(MISSING_ID, data.subsets[0])
    assert count(session, SubsetMaintenanceModel) == 1


# ------------------------------------------------------------- operador


def test_operator_name_is_normalized(session, data):
    operator = OperatorService(session).create_operator("  José   D'Ávila-Lima ")
    assert operator.name == "José D'Ávila-Lima"


@pytest.mark.parametrize(
    "name",
    ["", "   ", "Ana", "Ana 2", "Ana -", "Ana Lima-", "Ana\x00 Lima", "Ana " + "x" * 97, None],
)
def test_invalid_operator_name(session, name):
    with pytest.raises(InvalidOperatorNameError):
        OperatorService(session).create_operator(name)


def test_duplicate_operator_ignores_case_and_spaces(session, data):
    with pytest.raises(DuplicateOperatorError) as error:
        OperatorService(session).create_operator(" ana   SILVA ")
    assert error.value.details == {"existing_id": data.operator, "existing_name": "Ana Silva"}


# -------------------------------------------------------------- técnico


def test_technician_requires_existing_active_function(session, data):
    service = TechnicianService(session)
    assert service.create_technician("Maria Lima", data.function).function_id == data.function
    with pytest.raises(NotFoundError):
        service.create_technician("Maria Lima", MISSING_ID)
    with pytest.raises(InactiveFunctionError):
        service.create_technician("Maria Lima", data.inactive_function)


def test_change_function(session, data):
    service = TechnicianService(session)
    with pytest.raises(InactiveFunctionError):
        service.change_function(data.technician, data.inactive_function)
    with pytest.raises(NotFoundError):
        service.change_function(MISSING_ID, data.function)
    assert session.get(TechnicianModel, data.technician).function_id == data.function


@pytest.mark.xfail(
    reason="Revisão de 25/11/2026: TechnicianService não valida o nome", raises=pytest.fail.Exception
)
def test_technician_blank_name_is_rejected(session, data):
    with pytest.raises(DomainError):
        TechnicianService(session).create_technician("   ", data.function)


# ------------------------------------------------------------- listagens


def test_lists_in_alphabetical_order(session, data):
    assert [m.name for m in MachineService(session).list_machines()] == ["Nova Bloc", "Outra Máquina"]
    assert [o.name for o in OperatorService(session).list_operators()] == ["Ana Silva"]
    assert [t.name for t in TechnicianService(session).list_technicians()] == ["João Souza"]
    subsets = SubsetService(session).list_subsets_by_machine(data.machine)
    assert [s.name for s in subsets] == ["Esteira", "Motor"]


def test_subsets_of_missing_machine(session):
    with pytest.raises(NotFoundError):
        SubsetService(session).list_subsets_by_machine(MISSING_ID)
