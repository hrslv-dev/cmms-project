"""Repositories: consultas e operações de persistência, sem regras de negócio."""

from datetime import datetime, timedelta, timezone

import pytest

from app.models import MachineModel, MaintenanceModel, OperatorModel, SubsetMaintenanceModel
from app.repository.machine_repository import MachineRepository
from app.repository.maintenance_repository import MaintenanceRepository
from app.repository.operator_repository import OperatorRepository
from app.repository.subset_maintenance_repository import SubsetMaintenanceRepository
from app.repository.subset_repository import SubsetRepository
from app.repository.technical_function_repository import TechnicalFunctionRepository
from app.repository.technician_repository import TechnicianRepository
from tests.integration.conftest import MISSING_ID

START = datetime(2026, 11, 20, 8, tzinfo=timezone(timedelta(hours=-3)))


# ------------------------------------------------------- GenericRepository


def test_add_assigns_id_without_committing(session):
    repository = MachineRepository(session)
    machine = repository.add(MachineModel(name="Nova"))
    assert machine.id is not None
    assert repository.search_by_id(machine.id) is machine
    session.rollback()
    assert repository.search_by_id(machine.id) is None  # o repository não fez commit


def test_search_by_id_missing(session):
    assert MachineRepository(session).search_by_id(MISSING_ID) is None


def test_list_all_with_pagination(session, data):
    repository = MachineRepository(session)
    assert len(repository.list_all()) == 3
    assert len(repository.list_all(limit=2)) == 2
    assert len(repository.list_all(limit=10, offset=2)) == 1


def test_update_by_id(session, data):
    repository = MachineRepository(session)
    assert repository.update_by_id(data.machine, name="Renomeada").name == "Renomeada"
    session.expire_all()
    assert repository.search_by_id(data.machine).name == "Renomeada"


def test_update_by_id_missing_returns_none(session):
    assert MachineRepository(session).update_by_id(MISSING_ID, name="X") is None


@pytest.mark.parametrize("field", ["id", "inexistente"])
def test_update_by_id_refuses_id_and_unknown_fields(session, data, field):
    with pytest.raises(ValueError):
        MachineRepository(session).update_by_id(data.machine, **{field: 1})


def test_update_merges_a_detached_object(session, data):
    updated = MachineRepository(session).update(MachineModel(id=data.machine, name="Mesclada"))
    session.expire_all()
    assert session.get(MachineModel, data.machine).name == updated.name == "Mesclada"


def test_delete_by_id(session):
    repository = MachineRepository(session)
    machine_id = repository.add(MachineModel(name="Descartável")).id
    assert repository.delete_by_id(machine_id) is True
    assert repository.search_by_id(machine_id) is None
    assert repository.delete_by_id(machine_id) is False


# ------------------------------------------------ consultas específicas


def test_lists_ordered_by_name_use_portuguese_collation(session, data):
    assert [m.name for m in MachineRepository(session).list_ordered_by_name()] == [
        "Área Externa", "Máquina 2", "Nova Bloc",
    ]
    assert [t.id for t in TechnicianRepository(session).list_ordered_by_name()] == data.technicians
    assert [o.id for o in OperatorRepository(session).list_ordered_by_name()] == data.operators


def test_homonyms_are_ordered_by_id(session):
    repository = OperatorRepository(session)
    first = repository.add(OperatorModel(name="Zé Mesmo"))
    second = repository.add(OperatorModel(name="Zé Mesmo"))
    names = [o.id for o in repository.list_ordered_by_name() if o.name == "Zé Mesmo"]
    assert names == [first.id, second.id]


def test_operator_search_ignores_case_and_returns_the_oldest(session, data):
    repository = OperatorRepository(session)
    repository.add(OperatorModel(name="ANA SILVA"))  # homônimo gravado fora do Service
    assert repository.search_by_name_ignore_case("ana silva").id == data.operator
    assert repository.search_by_name_ignore_case("ÁNA SILVA") is None  # acento importa


def test_technical_function_queries(session, data):
    repository = TechnicalFunctionRepository(session)
    assert repository.search_by_name("Mecânica").id == data.function
    assert repository.search_by_name("mecânica") is None
    assert [f.id for f in repository.list_active()] == [data.function]


def test_technicians_by_function(session, data):
    found = TechnicianRepository(session).list_by_function(data.inactive_function)
    assert [t.id for t in found] == [data.technician_in_inactive_function]


def test_subsets_by_machine(session, data):
    repository = SubsetRepository(session)
    assert [s.id for s in repository.list_by_machine_id(data.machine)] == data.subsets
    assert repository.list_by_machine_id(data.empty_machine) == []


@pytest.fixture
def two_maintenances(session, data):
    """Primeira: dois subconjuntos e operador. Segunda: um subconjunto, sem operador."""
    def create(**changes):
        values = dict(machine_id=data.machine, technician_id=data.technician, service="Reparo",
                      maintenance_type="Preventiva", started_at=START, finished_at=START)
        return MaintenanceModel(**(values | changes))

    first, second = create(operator_id=data.operator), create(technician_id=data.technicians[0])
    session.add_all([first, second])
    session.flush()
    a, b = data.subsets
    session.add_all(SubsetMaintenanceModel(maintenance_id=m, subset_id=s)
                    for m, s in [(first.id, a), (first.id, b), (second.id, a)])
    session.flush()
    return first.id, second.id


def test_maintenance_queries(session, data, two_maintenances):
    first, second = two_maintenances
    repository = MaintenanceRepository(session)
    ids = lambda rows: {m.id for m in rows}  # noqa: E731
    assert ids(repository.list_by_machine(data.machine)) == {first, second}
    assert ids(repository.list_by_machine(data.other_machine)) == set()
    assert ids(repository.list_by_technician(data.technician)) == {first}
    assert ids(repository.list_by_operator(data.operator)) == {first}
    assert ids(repository.list_by_subset(data.subsets[0])) == {first, second}
    assert ids(repository.list_by_subset(data.subsets[1])) == {first}


def test_subsets_of_a_maintenance(session, data, two_maintenances):
    first, second = two_maintenances
    repository = SubsetRepository(session)
    assert {s.id for s in repository.list_by_maintenance_id(first)} == set(data.subsets)
    assert {s.id for s in repository.list_by_maintenance_id(second)} == {data.subsets[0]}


def test_search_link_by_pair(session, data, two_maintenances):
    first, second = two_maintenances
    repository = SubsetMaintenanceRepository(session)
    link = repository.search_by_pair(first, data.subsets[1])
    assert (link.maintenance_id, link.subset_id) == (first, data.subsets[1])
    assert repository.search_by_pair(second, data.subsets[1]) is None
