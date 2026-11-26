"""Casos de ``docs/tests.json`` executados contra ``POST /maintenances``.

O JSON usa os ids dos dados fictícios (``docs/sql/04-dados-ficticios-testes.sql``).
Para eles valerem aqui, cada teste reinicia as numerações e carrega esses
dados dentro da transação do teste; o rollback final desfaz as duas coisas.
"""

import json
import re
from pathlib import Path

import pytest
import sqlalchemy as sq

from app.api import dependencies
from app.main import app
from app.models import MaintenanceModel, SubsetMaintenanceModel

DOCS = Path(__file__).parents[2] / "docs"
CASES = json.loads((DOCS / "tests.json").read_text(encoding="utf-8"))["casos"]
TABLES = [
    "machines", "subsets", "operators", "technical_functions",
    "technicians", "maintenance", "subsets_maintenance",
]


@pytest.fixture
def fictitious_data(session):
    # ALTER TABLE é transacional no PostgreSQL: o rollback devolve a numeração.
    for table in TABLES:
        session.execute(sq.text(f"ALTER TABLE {table} ALTER COLUMN id RESTART"))
    # O arquivo tem BEGIN/COMMIT próprios; aqui a transação é a do teste.
    script = (DOCS / "sql/04-dados-ficticios-testes.sql").read_text(encoding="utf-8")
    script = re.sub(r"^(BEGIN|COMMIT);$", "", script, flags=re.MULTILINE)
    # Cursor do driver sem parâmetros: executa vários comandos de uma vez.
    session.connection().connection.cursor().execute(script)


@pytest.fixture
def post(session, request_app, fictitious_data):
    app.dependency_overrides[dependencies.get_session] = lambda: session
    yield lambda body: request_app(app, "POST", "/maintenances", body)
    app.dependency_overrides.clear()


def count(session, model):
    return session.scalar(sq.select(sq.func.count()).select_from(model))


@pytest.mark.parametrize("case", CASES, ids=[c["caso"] for c in CASES])
def test_case(post, session, case):
    response = post(case["body"])
    expected = case["esperado"]
    assert response.status == expected["status"], response.body

    if expected["status"] == 201:
        assert count(session, MaintenanceModel) == 1
        assert count(session, SubsetMaintenanceModel) == len(response.body["subset_ids"])
    else:
        assert response.body["code"] == expected["code"]
        assert set(response.body) == {"code", "message", "details"}
        # Nenhum erro deixa manutenção ou vínculo gravado pela metade.
        assert count(session, MaintenanceModel) == 0
        assert count(session, SubsetMaintenanceModel) == 0


def test_case_names_are_unique():
    names = [c["caso"] for c in CASES]
    assert len(names) == len(set(names))
