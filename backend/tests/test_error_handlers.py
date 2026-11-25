"""Formato ``code``/``message``/``details`` das respostas de erro.

As rotas daqui são só de teste. Quando as rotas reais existirem, os casos de
uso passam a ser testados por elas.
"""

import re

import pytest
from fastapi import FastAPI

from app.api.error_handlers import register_error_handlers
from app.schemas.maintenance_schema import MaintenanceCreate, MaintenanceRead
from app.schemas.operator_schema import OperatorCreate, OperatorRead
from app.services import exceptions
from app.services.maintenance_service import MaintenanceService
from app.services.operator_service import OperatorService
from app.services.subset_service import SubsetService
from app.services.technician_service import TechnicianService

MISSING_ID = 999_999


@pytest.fixture
def call(session, request_app):
    app = FastAPI()
    register_error_handlers(app)

    @app.post("/maintenances", status_code=201, response_model=MaintenanceRead)
    def create_maintenance(body: MaintenanceCreate):
        return MaintenanceService(session).create_maintenance(**body.model_dump())

    @app.post("/operators", status_code=201, response_model=OperatorRead)
    def create_operator(body: OperatorCreate):
        return OperatorService(session).create_operator(**body.model_dump())

    @app.get("/machines/{machine_id}/subsets")
    def list_subsets(machine_id: int):
        SubsetService(session).list_subsets_by_machine(machine_id)

    @app.post("/technicians/{function_id}")
    def create_technician(function_id: int):
        TechnicianService(session).create_technician("Maria Lima", function_id)

    @app.get("/unexpected")
    def unexpected():
        raise RuntimeError("SEGREDO: SELECT * FROM operators")

    return lambda method, path, body=None: request_app(app, method, path, body)


def assert_error(response, status, code, details=None):
    assert response.status == status
    assert set(response.body) == {"code", "message", "details"}
    assert response.body["code"] == code
    if details is not None:
        assert response.body["details"] == details


def test_success_is_not_affected(call, payload):
    assert call("POST", "/maintenances", payload()).status == 201


def test_not_found_by_url(call):
    response = call("GET", f"/machines/{MISSING_ID}/subsets")
    assert_error(response, 404, "not_found", {"resource": "machine", "id": MISSING_ID})


@pytest.mark.parametrize("resource", ["machine", "technician", "operator"])
def test_not_found_by_body(call, payload, resource):
    response = call("POST", "/maintenances", payload(**{f"{resource}_id": MISSING_ID}))
    assert_error(response, 404, "not_found", {"resource": resource, "id": MISSING_ID})


def test_subset_of_another_machine(call, payload, data):
    response = call("POST", "/maintenances", payload(subset_ids=[data.foreign_subset]))
    assert_error(response, 422, "subset_machine_mismatch", {
        "subset_id": data.foreign_subset,
        "subset_machine_id": data.other_machine,
        "maintenance_machine_id": data.machine,
    })


def test_inactive_function(call, data):
    response = call("POST", f"/technicians/{data.inactive_function}")
    assert_error(response, 422, "inactive_function", {
        "function_id": data.inactive_function, "function_name": "Desativada",
    })


def test_duplicate_operator(call, data):
    response = call("POST", "/operators", {"name": "ana silva"})
    assert_error(response, 409, "duplicate_operator", {
        "existing_id": data.operator, "existing_name": "Ana Silva",
    })


def test_future_period(call, payload):
    response = call("POST", "/maintenances", payload(finished_at="2099-01-01T00:00:00Z"))
    assert_error(response, 422, "invalid_maintenance_period", {})


@pytest.mark.parametrize(
    ("changes", "field", "message"),
    [
        ({"machine_id": "x"}, "machine_id", "Deve ser um número inteiro."),
        ({"subset_ids": [1, 0]}, "subset_ids.1", "Deve ser maior que 0."),
        ({"problem": "x"}, "problem", "Valor inválido. Use: 'Mecânico', 'Elétrico' ou 'Outro'."),
        ({"extra": 1}, "extra", "Campo não permitido."),
        ({"problem": None}, None, "problem é obrigatório em manutenção corretiva"),
        ({"started_at": "2026-11-20T08:00:00"}, "started_at",
         "Informe o fuso horário, por exemplo 2026-09-14T11:30:00-03:00."),
    ],
)
def test_validation_error(call, payload, changes, field, message):
    response = call("POST", "/maintenances", payload(**changes))
    assert_error(response, 422, "validation_error",
                 {"errors": [{"field": field, "message": message}]})


@pytest.mark.parametrize(
    ("body", "message"),
    [
        (b'{"a":', "O corpo da requisição não é um JSON válido."),
        (b"[1]", "Deve ser um objeto JSON."),
        (None, "Campo obrigatório."),
    ],
    ids=["json-malformado", "lista", "vazio"],
)
def test_invalid_body(call, body, message):
    response = call("POST", "/operators", body)
    assert_error(response, 422, "validation_error",
                 {"errors": [{"field": None, "message": message}]})


def test_unknown_route_and_method(call):
    assert_error(call("GET", "/nope"), 404, "route_not_found", {})
    response = call("DELETE", "/operators")
    assert_error(response, 405, "method_not_allowed", {})
    assert response.headers["allow"] == "POST"


def test_unexpected_error_hides_cause(call):
    response = call("GET", "/unexpected")
    assert_error(response, 500, "internal_error", {})
    assert "SEGREDO" not in str(response.body)
    assert isinstance(response.raised, RuntimeError)  # chega ao log do servidor


@pytest.mark.xfail(reason="Revisão de 25/11/2026: NUL em description vira erro 500")
def test_nul_character_in_description(call, payload):
    assert call("POST", "/maintenances", payload(description="a\x00b")).status == 422


def test_every_domain_error_has_its_own_code():
    classes = exceptions.DomainError.__subclasses__()
    for cls in classes:
        name = cls.__name__.removesuffix("Error")
        assert vars(cls)["code"] == re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
    assert len({cls.code for cls in classes}) == len(classes)
