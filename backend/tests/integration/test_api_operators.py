"""``POST /operators``: grava o nome normalizado e devolve o registro gravado."""

import pytest

from app.models import OperatorModel


def test_create_operator(api, session, table_counts):
    before = table_counts()
    response = api("POST", "/operators", {"name": "  Bia   Costa "})
    assert response.status == 201
    session.expire_all()
    stored = session.get(OperatorModel, response.body["id"])
    assert stored.name == response.body["name"] == "Bia Costa"
    assert table_counts() == before | {"operators": before["operators"] + 1}


def test_created_operator_appears_in_the_list(api):
    created = api("POST", "/operators", {"name": "Bia Costa"}).body
    assert created in api("GET", "/operators").body


@pytest.mark.parametrize(
    ("body", "status", "code"),
    [
        ({"name": "ana silva"}, 409, "duplicate_operator"),
        ({"name": "Ana"}, 422, "invalid_operator_name"),
        ({"name": None}, 422, "validation_error"),
        ({"name": "Bia Costa", "id": 5}, 422, "validation_error"),
    ],
    ids=["duplicado", "uma-palavra", "nulo", "campo-extra"],
)
def test_rejected_operator_is_not_written(api, data, table_counts, body, status, code):
    before = table_counts()
    response = api("POST", "/operators", body)
    assert (response.status, response.body["code"]) == (status, code)
    assert table_counts() == before


def test_duplicate_points_to_the_existing_operator(api, data):
    details = api("POST", "/operators", {"name": " ANA  silva"}).body["details"]
    assert details == {"existing_id": data.operator, "existing_name": "Ana Silva"}
