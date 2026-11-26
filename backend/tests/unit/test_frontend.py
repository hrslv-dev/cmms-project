"""Entrega do frontend pela API e listas fixas repetidas no frontend."""

import json
import re

import pytest

from app.main import FRONTEND, app
from app.services.enums import MaintenanceType, ProblemCategory, ServiceCategory


@pytest.fixture
def call(request_app):
    return lambda method, path: request_app(app, method, path)


def test_root_serves_the_page(call):
    response = call("GET", "/")
    assert response.status == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "<main" in response.body


@pytest.mark.parametrize("path", ["/static/styles.css", "/static/js/app.js"])
def test_static_files_are_served(call, path):
    assert call("GET", path).status == 200


def test_files_outside_static_are_not_served(call):
    assert call("GET", "/static/../tests/form-logic.test.mjs").status == 404


def test_api_method_errors_are_unchanged(call):
    """Servir o front não pode trocar o 405 das rotas da API por 404."""
    response = call("GET", "/maintenances")
    assert (response.status, response.body["code"]) == (405, "method_not_allowed")
    assert response.headers["allow"] == "POST"


def test_unknown_path_keeps_the_error_format(call):
    response = call("GET", "/nao-existe")
    assert (response.status, response.body["code"]) == (404, "route_not_found")


def frontend_list(name: str) -> list[str]:
    """Lê ``export const NAME = [...]`` de ``options.js`` (lista em formato JSON)."""
    source = (FRONTEND / "static/js/options.js").read_text(encoding="utf-8")
    match = re.search(rf"export const {name} = (\[.*?\]);", source, re.DOTALL)
    assert match, f"{name} não encontrado em options.js"
    return json.loads(match.group(1))


@pytest.mark.parametrize(
    ("name", "enum"),
    [("SERVICES", ServiceCategory), ("PROBLEMS", ProblemCategory),
     ("MAINTENANCE_TYPES", MaintenanceType)],
)
def test_frontend_options_match_backend_enums(name, enum):
    """Se alguém mudar um lado só, este teste avisa."""
    assert frontend_list(name) == [member.value for member in enum]
