"""``POST /maintenances``: o que é gravado no banco e o que é devolvido.

Os casos de entrada (um por regra) ficam em ``docs/tests.json`` e
``test_maintenance_cases.py``. Aqui se confere a gravação em detalhe.
"""

from datetime import datetime, timedelta

import pytest

from app.models import MaintenanceModel
from tests.integration.conftest import MISSING_ID


def stored(session, maintenance_id):
    session.expire_all()
    return session.get(MaintenanceModel, maintenance_id)


def test_every_field_is_written(api, session, data, payload):
    body = payload(operator_id=data.operator, subset_ids=list(reversed(data.subsets)),
                   description="  Troca do rolamento  ")
    response = api("POST", "/maintenances", body)
    assert response.status == 201
    row = stored(session, response.body["id"])

    assert (row.machine_id, row.technician_id, row.operator_id) == (
        data.machine, data.technician, data.operator,
    )
    assert row.started_at == datetime.fromisoformat(body["started_at"])  # mesmo instante
    assert row.finished_at == datetime.fromisoformat(body["finished_at"])
    assert (row.service, row.maintenance_type, row.problem) == ("Reparo", "Corretiva", "Mecânico")
    assert row.description == "Troca do rolamento"
    assert row.elapsed_time == timedelta(hours=2, minutes=30)
    assert sorted(link.subset_id for link in row.subset_links) == sorted(data.subsets)


def test_response_matches_the_stored_row(api, session, data, payload):
    response = api("POST", "/maintenances", payload(subset_ids=data.subsets))
    row = stored(session, response.body["id"])
    body = response.body
    assert body["id"] == row.id
    for field in ("machine_id", "technician_id", "operator_id", "service",
                  "maintenance_type", "problem", "description"):
        assert body[field] == getattr(row, field), field
    assert datetime.fromisoformat(body["started_at"]) == row.started_at
    assert datetime.fromisoformat(body["finished_at"]) == row.finished_at
    assert body["elapsed_time"] == "PT2H30M"
    assert body["subset_ids"] == sorted(link.subset_id for link in row.subset_links)


def test_optional_fields_are_written_as_null(api, session, payload):
    body = payload(maintenance_type="Preventiva", problem=None)
    response = api("POST", "/maintenances", body)
    row = stored(session, response.body["id"])
    assert (row.operator_id, row.problem, row.description, row.subset_links) == (
        None, None, None, [],
    )


def test_only_one_maintenance_and_its_links_are_written(api, data, payload, table_counts):
    before = table_counts()
    api("POST", "/maintenances", payload(subset_ids=data.subsets + data.subsets[:1]))
    assert table_counts() == before | {
        "maintenance": before["maintenance"] + 1,
        "subsets_maintenance": before["subsets_maintenance"] + len(data.subsets),
    }


def test_timestamps_keep_the_instant_regardless_of_offset(api, session, payload):
    """Início em -03:00 e fim em UTC: o banco grava os instantes, não os textos."""
    body = payload(started_at="2026-11-20T08:00:00-03:00", finished_at="2026-11-20T11:30:00Z")
    row = stored(session, api("POST", "/maintenances", body).body["id"])
    assert row.elapsed_time == timedelta(minutes=30)


@pytest.mark.parametrize(
    ("changes", "status", "code"),
    [
        ({"machine_id": MISSING_ID}, 404, "not_found"),
        ({"subset_ids": "foreign"}, 422, "subset_machine_mismatch"),
        ({"subset_ids": [MISSING_ID]}, 404, "not_found"),
        ({"finished_at": "2099-01-01T00:00:00Z"}, 422, "invalid_maintenance_period"),
        ({"problem": None}, 422, "validation_error"),
    ],
    ids=["maquina-inexistente", "subconjunto-de-outra-maquina", "subconjunto-inexistente",
         "fim-no-futuro", "corretiva-sem-problema"],
)
def test_rejected_maintenance_writes_nothing(api, data, payload, table_counts,
                                             changes, status, code):
    if changes.get("subset_ids") == "foreign":
        changes = {"subset_ids": [data.subsets[0], data.foreign_subset]}
    before = table_counts()
    response = api("POST", "/maintenances", payload(**changes))
    assert (response.status, response.body["code"]) == (status, code)
    assert table_counts() == before


@pytest.mark.xfail(reason="Revisão de 25/11/2026: NUL em description vira erro 500")
def test_nul_character_in_description_is_a_validation_error(api, payload):
    assert api("POST", "/maintenances", payload(description="a\x00b")).status == 422
