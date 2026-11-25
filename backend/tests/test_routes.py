"""Rotas reais da Tela 1, com a sessão trocada pela do banco descartável."""

import pytest

from app.api import dependencies
from app.main import app

MISSING_ID = 999_999


@pytest.fixture
def call(session, request_app):
    app.dependency_overrides[dependencies.get_session] = lambda: session
    yield lambda method, path, body=None: request_app(app, method, path, body)
    app.dependency_overrides.clear()


def test_lists(call, data):
    assert [m["name"] for m in call("GET", "/machines").body] == ["Nova Bloc", "Outra Máquina"]
    assert call("GET", "/technicians").body == [{"id": data.technician, "name": "João Souza"}]
    assert call("GET", "/operators").body == [{"id": data.operator, "name": "Ana Silva"}]


@pytest.mark.parametrize("path", ["/machines", "/technicians", "/operators"])
def test_empty_lists(call, path):
    response = call("GET", path)
    assert (response.status, response.body) == (200, [])


def test_subsets_of_machine(call, data):
    response = call("GET", f"/machines/{data.machine}/subsets")
    assert response.body == [
        {"id": data.subsets[0], "name": "Esteira"}, {"id": data.subsets[1], "name": "Motor"},
    ]
    missing = call("GET", f"/machines/{MISSING_ID}/subsets")
    assert (missing.status, missing.body["code"]) == (404, "not_found")
    assert call("GET", "/machines/abc/subsets").status == 422


def test_screen_flow_new_operator_then_maintenance(call, data, payload):
    """Operador criado na hora e usado no registro, como na Tela 1."""
    operator = call("POST", "/operators", {"name": " Bia   Costa "})
    assert (operator.status, operator.body["name"]) == (201, "Bia Costa")
    body = payload(operator_id=operator.body["id"], subset_ids=data.subsets)
    response = call("POST", "/maintenances", body)
    assert response.status == 201
    assert response.body == body | {
        "id": response.body["id"], "elapsed_time": "PT2H30M", "description": None,
    }


def test_errors_use_standard_format(call, data, payload):
    cases = [
        (call("POST", "/operators", {"name": "ana silva"}), 409, "duplicate_operator"),
        (call("POST", "/operators", {"name": "Ana"}), 422, "invalid_operator_name"),
        (call("POST", "/maintenances", payload(machine_id=MISSING_ID)), 404, "not_found"),
        (call("POST", "/maintenances", payload(subset_ids=[data.foreign_subset])), 422,
         "subset_machine_mismatch"),
        (call("POST", "/maintenances", payload(problem="")), 422, "validation_error"),
    ]
    for response, status, code in cases:
        assert (response.status, response.body["code"]) == (status, code)
        assert set(response.body) == {"code", "message", "details"}


@pytest.mark.parametrize("fails", [False, True], ids=["sucesso", "erro"])
def test_session_is_closed_after_request(monkeypatch, fails):
    class FakeSession:
        closed = False

        def close(self):
            self.closed = True

    session = FakeSession()
    monkeypatch.setattr(dependencies, "create_session", lambda: session)
    generator = dependencies.get_session()
    assert next(generator) is session and not session.closed
    if fails:
        with pytest.raises(RuntimeError):
            generator.throw(RuntimeError())
    else:
        with pytest.raises(StopIteration):
            next(generator)
    assert session.closed
