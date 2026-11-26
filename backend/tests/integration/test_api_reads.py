"""Endpoints GET: devolvem o que está no banco, completo e na ordem da regra.

Cada lista é comparada com uma consulta SQL independente do código da
aplicação, sobre os registros gravados pela fixture ``data``.
"""

import pytest
import sqlalchemy as sq

from tests.integration.conftest import MISSING_ID


def rows(session, sql, **params):
    return [dict(r._mapping) for r in session.execute(sq.text(sql), params)]


@pytest.mark.parametrize(
    ("path", "table"),
    [("/machines", "machines"), ("/technicians", "technicians"), ("/operators", "operators")],
)
def test_list_returns_every_row_of_the_table(api, session, data, path, table):
    response = api("GET", path)
    assert response.status == 200
    expected = rows(session, f"SELECT id, name FROM {table} ORDER BY name, id")
    assert [{"id": r["id"], "name": r["name"]} for r in response.body] == expected


def test_lists_follow_alphabetical_order_with_accents(api, data):
    assert [m["name"] for m in api("GET", "/machines").body] == [
        "Área Externa", "Máquina 2", "Nova Bloc",
    ]
    assert [t["id"] for t in api("GET", "/technicians").body] == data.technicians
    assert [o["id"] for o in api("GET", "/operators").body] == data.operators


def test_technician_of_a_deactivated_function_is_still_listed(api, data):
    """A regra de função ativa vale só ao atribuir a função."""
    ids = [t["id"] for t in api("GET", "/technicians").body]
    assert data.technician_in_inactive_function in ids


@pytest.mark.parametrize("path", ["/machines", "/technicians", "/operators"])
def test_empty_list(api, path):
    response = api("GET", path)
    assert (response.status, response.body) == (200, [])


def test_subsets_of_a_machine_are_only_its_own(api, session, data):
    response = api("GET", f"/machines/{data.machine}/subsets")
    assert response.status == 200
    expected = rows(session, "SELECT id, name FROM subsets WHERE machine_id = :m ORDER BY name, id",
                    m=data.machine)
    assert [{"id": s["id"], "name": s["name"]} for s in response.body] == expected
    assert data.foreign_subset not in [s["id"] for s in response.body]


def test_machine_without_subsets(api, data):
    response = api("GET", f"/machines/{data.empty_machine}/subsets")
    assert (response.status, response.body) == (200, [])


def test_subsets_of_a_missing_machine(api):
    response = api("GET", f"/machines/{MISSING_ID}/subsets")
    assert response.status == 404
    assert response.body["code"] == "not_found"
    assert response.body["details"] == {"resource": "machine", "id": MISSING_ID}


def test_reads_do_not_write(api, data, table_counts):
    before = table_counts()
    for path in ["/machines", "/technicians", "/operators", f"/machines/{data.machine}/subsets"]:
        api("GET", path)
    assert table_counts() == before
