"""Estrutura e regras garantidas pelo próprio PostgreSQL."""

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
from app.services.enums import MaintenanceType, ServiceCategory
from tests.integration.conftest import MISSING_ID

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
            (r.table_name, r.column_name): r._asdict()
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


def test_models_match_database_structure(engine, create_database):
    """Models e SQL do banco só podem divergir no NOT NULL pendente.

    A pendência (docs/pendencia-alinhamento-banco.md) deixa o model mais
    restrito que o banco. Quando ela for aplicada, este teste continua válido.
    """
    from_models = create_database("from_models")
    Base.metadata.create_all(from_models)
    (db_cols, db_cons, db_idx), (m_cols, m_cons, m_idx) = catalog(engine), catalog(from_models)

    assert db_cols.keys() == m_cols.keys()
    pending = {("maintenance", "finished_at"), ("maintenance", "elapsed_time")}
    for key in db_cols:
        db, model = dict(db_cols[key]), dict(m_cols[key])
        if key in pending and (db["is_nullable"], model["is_nullable"]) == ("YES", "NO"):
            db.pop("is_nullable"), model.pop("is_nullable")
        assert db == model, key
    assert db_cons == m_cons
    assert db_idx == m_idx


@pytest.mark.parametrize(
    "duration",
    [timedelta(0), timedelta(hours=3), timedelta(hours=26), timedelta(days=4, minutes=5)],
    ids=["zero", "cruza-meia-noite", "26h", "varios-dias"],
)
def test_elapsed_time_is_computed_by_the_database(session, data, duration):
    maintenance = new_maintenance(data, finished_at=START + duration)
    session.add(maintenance)
    session.flush()
    assert maintenance.elapsed_time == duration


def test_elapsed_time_follows_finished_at_changes(session, data):
    maintenance = new_maintenance(data)
    session.add(maintenance)
    session.flush()
    maintenance.finished_at = START + timedelta(hours=5)
    session.flush()
    assert maintenance.elapsed_time == timedelta(hours=5)


@pytest.mark.parametrize("value", list(ServiceCategory))
def test_every_service_option_is_accepted_by_the_check(session, data, value):
    """Enum da aplicação e CHECK do banco não podem divergir."""
    session.add(new_maintenance(data, service=value.value))
    session.flush()


@pytest.mark.parametrize("value", list(MaintenanceType))
def test_every_type_is_accepted_by_the_check(session, data, value):
    session.add(new_maintenance(data, maintenance_type=value.value))
    session.flush()


@pytest.mark.parametrize(
    ("changes", "constraint"),
    [
        ({"maintenance_type": "Preditiva"}, "ck_maintenance_type"),
        ({"service": "Pintura"}, "ck_maintenance_service"),
        ({"problem": None}, "ck_maintenance_problem_corrective"),
        ({"finished_at": START - timedelta(seconds=1)}, "ck_maintenance_finished_after_started"),
        ({"machine_id": MISSING_ID}, "fk_maintenance_machine"),
        ({"technician_id": MISSING_ID}, "fk_maintenance_technician"),
        ({"operator_id": MISSING_ID}, "fk_maintenance_operator"),
    ],
)
def test_database_rejects_invalid_maintenance(session, data, changes, constraint):
    session.add(new_maintenance(data, **changes))
    with pytest.raises(IntegrityError, match=constraint):
        session.flush()


def test_preventive_without_problem_is_accepted(session, data):
    session.add(new_maintenance(data, maintenance_type="Preventiva", problem=None))
    session.flush()


def test_subset_link_pair_is_unique(session, data):
    maintenance = new_maintenance(data)
    session.add(maintenance)
    session.flush()
    pair = dict(maintenance_id=maintenance.id, subset_id=data.subsets[0])
    session.add(SubsetMaintenanceModel(**pair))
    session.flush()
    session.add(SubsetMaintenanceModel(**pair))
    with pytest.raises(IntegrityError, match="uq_maintenance_subset"):
        session.flush()


@pytest.mark.parametrize("model", [TechnicalFunctionModel, TechnicianModel, MachineModel])
def test_rows_with_history_cannot_be_deleted(session, data, model):
    session.add(new_maintenance(data))
    session.flush()
    ids = {TechnicalFunctionModel: data.function, TechnicianModel: data.technician,
           MachineModel: data.machine}
    session.delete(session.get(model, ids[model]))
    with pytest.raises(IntegrityError):
        session.flush()


@pytest.mark.parametrize("name", ["Mecânica", "   "], ids=["repetido", "em-branco"])
def test_technical_function_name_rules(session, data, name):
    session.add(TechnicalFunctionModel(name=name))
    with pytest.raises(IntegrityError):
        session.flush()


def test_new_technical_function_is_active_by_default(session):
    function = TechnicalFunctionModel(name="Nova função")
    session.add(function)
    session.flush()
    assert function.active is True


def test_id_is_always_generated_by_the_database(session):
    session.add(MachineModel(id=123, name="X"))
    with pytest.raises(DatabaseError):
        session.flush()
