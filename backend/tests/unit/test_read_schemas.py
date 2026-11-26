"""Fichas de saída montadas a partir de objetos com atributos, como os Models."""

import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.schemas.machine_schema import MachineRead
from app.schemas.maintenance_schema import MaintenanceRead
from app.schemas.operator_schema import OperatorRead
from app.schemas.subset_schema import SubsetRead
from app.schemas.technician_schema import TechnicianRead

BRT = timezone(timedelta(hours=-3))


@pytest.mark.parametrize("schema", [MachineRead, OperatorRead, SubsetRead, TechnicianRead])
def test_simple_read_exposes_id_and_name(schema):
    """Atributos internos (função, máquina, relações) não vão para a resposta."""
    row = SimpleNamespace(id=7, name="Nome", function_id=2, machine_id=3, maintenances=[])
    assert schema.model_validate(row).model_dump() == {"id": 7, "name": "Nome"}


def maintenance_row(**changes):
    values = dict(
        id=1, machine_id=2, technician_id=3, operator_id=None,
        started_at=datetime(2026, 11, 20, 8, tzinfo=BRT),
        finished_at=datetime(2026, 11, 21, 10, 30, tzinfo=BRT),
        elapsed_time=timedelta(days=1, hours=2, minutes=30),
        service="Reparo", maintenance_type="Corretiva", problem="Mecânico",
        description=None,
        subset_links=[SimpleNamespace(id=9, subset_id=5), SimpleNamespace(id=8, subset_id=2)],
    )
    return SimpleNamespace(**(values | changes))


def test_maintenance_read_json():
    body = json.loads(MaintenanceRead.model_validate(maintenance_row()).model_dump_json())
    assert body["elapsed_time"] == "P1DT2H30M"                # duração ISO 8601
    assert body["started_at"] == "2026-11-20T08:00:00-03:00"  # fuso preservado
    assert body["subset_ids"] == [2, 5]                       # ids dos subconjuntos, crescentes
    assert "subset_links" not in body


def test_maintenance_read_tolerates_values_outside_the_enums():
    """``problem`` é texto livre no banco: uma linha antiga não pode impedir a leitura."""
    read = MaintenanceRead.model_validate(maintenance_row(problem="texto antigo"))
    assert read.problem == "texto antigo"
