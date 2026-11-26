"""Tradução de exceções em respostas ``code``/``message``/``details``, sem banco."""

import pytest
from fastapi import FastAPI
from pydantic import BaseModel, field_validator

from app.api.error_handlers import register_error_handlers
from app.schemas.maintenance_schema import MaintenanceCreate
from app.services import exceptions as ex

OWN_MESSAGE = "mensagem do validador do projeto"


class NewRuleError(ex.DomainError):
    """Exceção criada depois: deve responder 422 sem mudar a API."""

    code = "new_rule"


class Body(BaseModel):
    value: int

    @field_validator("value")
    @classmethod
    def positive(cls, value):
        if value < 0:
            raise ValueError(OWN_MESSAGE)
        return value


@pytest.fixture
def call(request_app):
    app = FastAPI()
    register_error_handlers(app)
    current = {}

    @app.get("/raise")
    def raise_error():
        raise current["error"]

    @app.post("/body")
    def body(payload: Body):
        return payload

    @app.post("/maintenance")
    def maintenance(payload: MaintenanceCreate):
        return {}

    @app.get("/items/{item_id}")
    def item(item_id: int):
        return {}

    def run(method, path, body=None, error=None):
        current["error"] = error
        return request_app(app, method, path, body)

    return run


def assert_format(response, status, code):
    assert response.status == status
    assert set(response.body) == {"code", "message", "details"}
    assert response.body["code"] == code
    assert isinstance(response.body["message"], str) and response.body["message"]
    assert isinstance(response.body["details"], dict)


@pytest.mark.parametrize(
    ("error", "status"),
    [
        (ex.NotFoundError("machine", 9), 404),
        (ex.DuplicateOperatorError(1, "Ana Silva"), 409),
        (ex.DuplicateSubsetLinkError(1, 2), 409),
        (ex.SubsetMachineMismatchError(5, 2, 1), 422),
        (ex.InactiveFunctionError(2, "Antiga"), 422),
        (ex.InvalidMaintenancePeriodError("msg"), 422),
        (NewRuleError("msg"), 422),
    ],
    ids=lambda v: type(v).__name__ if isinstance(v, Exception) else str(v),
)
def test_domain_error(call, error, status):
    response = call("GET", "/raise", error=error)
    assert_format(response, status, error.code)
    assert response.body["message"] == str(error)
    assert response.body["details"] == error.details


def test_validation_errors_point_to_each_field(call):
    response = call("POST", "/maintenance", {"machine_id": 0, "subset_ids": [1, -1], "extra": 1})
    assert_format(response, 422, "validation_error")
    fields = {e["field"] for e in response.body["details"]["errors"]}
    assert {"machine_id", "subset_ids.1", "extra", "technician_id"} <= fields
    assert all(isinstance(e["message"], str) and e["message"]
               for e in response.body["details"]["errors"])


def test_project_validator_message_is_kept(call):
    """``ValueError`` dos validators chega à tela sem o prefixo do Pydantic."""
    response = call("POST", "/body", {"value": -1})
    assert response.body["details"]["errors"] == [{"field": "value", "message": OWN_MESSAGE}]


def test_rule_between_fields_has_no_field(call):
    body = {
        "machine_id": 1, "technician_id": 1, "service": "Reparo",
        "maintenance_type": "Corretiva", "started_at": "2026-11-20T08:00:00-03:00",
        "finished_at": "2026-11-20T09:00:00-03:00",
    }
    errors = call("POST", "/maintenance", body).body["details"]["errors"]
    assert [e["field"] for e in errors] == [None]


@pytest.mark.parametrize("body", [b'{"value":', b"[1]", None, b"null"],
                         ids=["malformado", "lista", "vazio", "null"])
def test_invalid_body_is_not_attributed_to_a_field(call, body):
    response = call("POST", "/body", body)
    assert_format(response, 422, "validation_error")
    assert [e["field"] for e in response.body["details"]["errors"]] == [None]


def test_invalid_path_parameter(call):
    response = call("GET", "/items/abc")
    assert_format(response, 422, "validation_error")
    assert response.body["details"]["errors"][0]["field"] == "item_id"


def test_unknown_route(call):
    assert_format(call("GET", "/nope"), 404, "route_not_found")


def test_method_not_allowed_keeps_allow_header(call):
    response = call("DELETE", "/body")
    assert_format(response, 405, "method_not_allowed")
    assert response.headers["allow"] == "POST"


def test_unexpected_error_hides_the_cause_and_reaches_the_log(call):
    response = call("GET", "/raise", error=RuntimeError("SEGREDO: SELECT * FROM operators"))
    assert_format(response, 500, "internal_error")
    assert "SEGREDO" not in str(response.body)
    assert isinstance(response.raised, RuntimeError)  # relançada ao servidor
