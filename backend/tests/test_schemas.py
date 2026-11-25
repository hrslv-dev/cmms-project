"""Validação de entrada e formato de saída dos schemas."""

import json

import pytest
from pydantic import ValidationError

from app.models import MachineModel, OperatorModel, SubsetModel, TechnicianModel
from app.schemas.machine_schema import MachineRead
from app.schemas.maintenance_schema import MaintenanceCreate, MaintenanceRead
from app.schemas.operator_schema import OperatorCreate, OperatorRead
from app.schemas.subset_schema import SubsetRead
from app.schemas.technician_schema import TechnicianCreate, TechnicianRead
from app.services.maintenance_service import MaintenanceService

VALID = {
    "machine_id": 1,
    "technician_id": 1,
    "started_at": "2026-11-20T08:00:00-03:00",
    "finished_at": "2026-11-20T10:30:00-03:00",
    "service": "Reparo",
    "maintenance_type": "Corretiva",
    "problem": "Mecânico",
}


@pytest.mark.parametrize(
    "field",
    ["machine_id", "technician_id", "started_at", "finished_at", "service", "maintenance_type"],
)
def test_required_fields(field):
    with pytest.raises(ValidationError) as error:
        MaintenanceCreate.model_validate({k: v for k, v in VALID.items() if k != field})
    assert [(e["loc"], e["type"]) for e in error.value.errors()] == [((field,), "missing")]


@pytest.mark.parametrize(
    "changes",
    [
        {"machine_id": 0}, {"technician_id": -1}, {"operator_id": 0}, {"subset_ids": [1, 0]},
        {"service": "reparo"}, {"maintenance_type": "Preditiva"}, {"problem": "Hidráulico"},
        {"problem": None}, {"id": 1}, {"elapsed_time": "PT1H"}, {"description": 5},
        {"finished_at": "2026-11-20T07:59:59-03:00"}, {"finished_at": None},
    ],
    ids=str,
)
def test_rejects_invalid_maintenance(changes):
    with pytest.raises(ValidationError):
        MaintenanceCreate.model_validate(VALID | changes)


@pytest.mark.parametrize(
    "value",
    [0, "0", 1763625600, "1763625600", 1.5, "-1", True, "", "abc", "2026-11-20",
     "2026-11-20T08:00:00", "20261120T080000Z", "2026-02-30T08:00:00Z"],
    ids=repr,
)
def test_datetime_must_be_text_with_offset(value):
    with pytest.raises(ValidationError):
        MaintenanceCreate.model_validate(VALID | {"started_at": value})


@pytest.mark.parametrize(
    ("changes", "field", "expected"),
    [
        ({"description": "  troca  "}, "description", "troca"),
        ({"description": "   "}, "description", None),
        ({"subset_ids": [3, 1, 3]}, "subset_ids", [3, 1]),
        ({}, "subset_ids", []),
        ({"maintenance_type": "Preventiva", "problem": None}, "problem", None),
    ],
)
def test_normalizes_maintenance(changes, field, expected):
    assert getattr(MaintenanceCreate.model_validate(VALID | changes), field) == expected


def test_end_in_another_offset_is_compared_as_instant():
    MaintenanceCreate.model_validate(VALID | {"finished_at": "2026-11-20T11:00:00Z"})


def test_operator_create_only_accepts_name():
    with pytest.raises(ValidationError):
        OperatorCreate.model_validate({"name": "Ana Silva", "id": 1})


def test_technician_create():
    assert TechnicianCreate(name="  João Souza ", function_id=1).name == "João Souza"
    for invalid in ({"name": "x" * 101}, {"name": "      "}, {"function_id": 0}):
        with pytest.raises(ValidationError):
            TechnicianCreate.model_validate({"name": "João Souza", "function_id": 1} | invalid)


@pytest.mark.parametrize(
    ("schema", "model", "key"),
    [
        (MachineRead, MachineModel, "machine"),
        (OperatorRead, OperatorModel, "operator"),
        (TechnicianRead, TechnicianModel, "technician"),
        (SubsetRead, SubsetModel, "foreign_subset"),
    ],
)
def test_simple_reads_expose_only_id_and_name(session, data, schema, model, key):
    row = session.get(model, getattr(data, key))
    assert schema.model_validate(row).model_dump() == {"id": row.id, "name": row.name}


def test_maintenance_read(session, data, payload):
    body = payload(operator_id=data.operator, subset_ids=data.subsets[::-1], description="x")
    values = MaintenanceCreate.model_validate(body).model_dump()
    maintenance = MaintenanceService(session).create_maintenance(**values)
    result = json.loads(MaintenanceRead.model_validate(maintenance).model_dump_json())
    assert result == body | {
        "id": maintenance.id, "elapsed_time": "PT2H30M", "subset_ids": sorted(data.subsets),
    }


def test_maintenance_read_tolerates_free_text_problem(session, data, payload):
    values = MaintenanceCreate.model_validate(payload()).model_dump()
    maintenance = MaintenanceService(session).create_maintenance(**values)
    maintenance.problem = "texto antigo"
    session.flush()
    assert MaintenanceRead.model_validate(maintenance).problem == "texto antigo"
