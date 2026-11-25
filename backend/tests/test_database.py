"""Estrutura, constraints e colunas geradas do PostgreSQL."""

from datetime import datetime, timedelta, timezone

import pytest
import sqlalchemy as sq
from sqlalchemy.exc import DatabaseError, IntegrityError

from app.infrastructure.base.base_model import Base
from app.models import (
    MachineModel,
    MaintenanceModel,
    SubsetMaintenanceModel,
    TechnicalFunctionModel,
    TechnicianModel,
)
from app.repository.maintenance_repository import MaintenanceRepository
from app.repository.subset_repository import SubsetRepository

START = datetime(2026, 11, 20, 22, 0, tzinfo=timezone(timedelta(hours=-3)))


def new_maintenance(data, **changes):
    values = dict(
        machine_id=data.machine, technician_id=data.technician, service="Reparo",
        maintenance_type="Corretiva", problem="Mecânico",
        started_at=START, finished_at=START + timedelta(hours=1),
    )
    return MaintenanceModel(**(values | changes))


def catalog(engine):
    with engine.connect() as connection:
        columns = {
            (r.table_name, r.column_name): tuple(r)
            for r in connection.execute(sq.text(
                "SELECT table_name, column_name, data_type, character_maximum_length,"
                " is_nullable, column_default, identity_generation, generation_expression"
                " FROM information_schema.columns WHERE table_schema = 'public'"
            ))
        }
        constraints = set(connection.scalars(sq.text(
            "SELECT concat_ws('|', conrelid::regclass, conname, pg_get_constraintdef(oid))"
            " FROM pg_constraint WHERE connamespace = 'public'::regnamespace"
        )))
        indexes = set(connection.scalars(sq.text(
            "SELECT indexdef FROM pg_indexes WHERE schemaname = 'public'"
        )))
    return columns, constraints, indexes


def test_models_match_database_except_known_gap(engine, create_database):
    """Models e SQL só divergem no que está em docs/pendencia-alinhamento-banco.md.

    Quando o SQL da pendência for aplicado, atualize o arquivo 02 e esvazie
    ``expected``.
    """
    from_models = create_database("from_models")
    Base.metadata.create_all(from_models)
    db, models = catalog(engine), catalog(from_models)

    assert db[0].keys() == models[0].keys()
    differences = {key for key in db[0] if db[0][key] != models[0][key]}
    expected = {("maintenance", "finished_at"), ("maintenance", "elapsed_time")}
    assert differences == expected
    assert db[1] == models[1]
    assert db[2] == models[2]


@pytest.mark.parametrize(
    "duration",
    [timedelta(0), timedelta(hours=3), timedelta(hours=26), timedelta(days=4, minutes=5)],
    ids=["zero", "cruza-meia-noite", "26h", "varios-dias"],
)
def test_elapsed_time_is_generated(session, data, duration):
    maintenance = new_maintenance(data, finished_at=START + duration)
    session.add(maintenance)
    session.flush()
    assert maintenance.elapsed_time == duration


def test_elapsed_time_is_recalculated_on_update(session, data):
    maintenance = new_maintenance(data)
    session.add(maintenance)
    session.flush()
    maintenance.finished_at = START + timedelta(hours=5)
    session.flush()
    assert maintenance.elapsed_time == timedelta(hours=5)


@pytest.mark.parametrize(
    ("changes", "constraint"),
    [
        ({"maintenance_type": "Preditiva"}, "ck_maintenance_type"),
        ({"service": "Pintura"}, "ck_maintenance_service"),
        ({"problem": None}, "ck_maintenance_problem_corrective"),
        ({"finished_at": START - timedelta(seconds=1)}, "ck_maintenance_finished_after_started"),
        ({"machine_id": 999_999}, "fk_maintenance_machine"),
        ({"technician_id": 999_999}, "fk_maintenance_technician"),
        ({"operator_id": 999_999}, "fk_maintenance_operator"),
    ],
)
def test_database_rejects_invalid_maintenance(session, data, changes, constraint):
    session.add(new_maintenance(data, **changes))
    with pytest.raises(IntegrityError, match=constraint):
        session.flush()


def test_preventive_accepts_null_problem_and_operator(session, data):
    session.add(new_maintenance(data, maintenance_type="Preventiva", problem=None))
    session.flush()


def test_subset_link_is_unique(session, data):
    maintenance = new_maintenance(data)
    session.add(maintenance)
    session.flush()
    pair = dict(maintenance_id=maintenance.id, subset_id=data.subsets[0])
    session.add(SubsetMaintenanceModel(**pair))
    session.flush()
    session.add(SubsetMaintenanceModel(**pair))
    with pytest.raises(IntegrityError, match="uq_maintenance_subset"):
        session.flush()


def test_subsets_and_maintenances_are_many_to_many(session, data):
    first, second = new_maintenance(data), new_maintenance(data)
    session.add_all([first, second])
    session.flush()
    a, b = data.subsets
    session.add_all(
        SubsetMaintenanceModel(maintenance_id=m, subset_id=s)
        for m, s in [(first.id, a), (first.id, b), (second.id, a)]
    )
    session.flush()
    assert {s.id for s in SubsetRepository(session).list_by_maintenance_id(first.id)} == {a, b}
    found = MaintenanceRepository(session).list_by_subset(a)
    assert {m.id for m in found} == {first.id, second.id}


@pytest.mark.parametrize("model", [TechnicalFunctionModel, TechnicianModel, MachineModel])
def test_referenced_rows_cannot_be_deleted(session, data, model):
    session.add(new_maintenance(data))
    session.flush()
    ids = {
        TechnicalFunctionModel: data.function,
        TechnicianModel: data.technician,
        MachineModel: data.machine,
    }
    session.delete(session.get(model, ids[model]))
    with pytest.raises(IntegrityError):
        session.flush()


@pytest.mark.parametrize("name", ["Mecânica", "   "], ids=["repetida", "em-branco"])
def test_technical_function_name_rules(session, data, name):
    session.add(TechnicalFunctionModel(name=name))
    with pytest.raises(IntegrityError):
        session.flush()


def test_id_cannot_be_set_manually(session):
    session.add(MachineModel(id=123, name="X"))
    with pytest.raises(DatabaseError, match="GENERATED ALWAYS|id"):
        session.flush()


def test_rollback_discards_flushed_rows(session):
    machine = MachineModel(name="Temporária")
    session.add(machine)
    session.flush()
    machine_id = machine.id
    session.rollback()
    assert session.get(MachineModel, machine_id) is None
