"""Casos de ``docs/tests.json`` executados contra ``POST /maintenances``.

O JSON usa os ids dos dados fictícios (``docs/sql/04-dados-ficticios-testes.sql``).
Para eles valerem aqui, cada teste reinicia as numerações e carrega esses
dados dentro da transação do teste; o rollback final desfaz as duas coisas.
Casos com ``falha_conhecida`` descrevem o comportamento CORRETO e rodam como
``xfail``: quando a falha for corrigida, remova o campo do JSON.
"""

import json

import pytest
import sqlalchemy as sq

from tests.integration.conftest import DOCS, TABLES, run_sql_file

CASES = json.loads((DOCS / "tests.json").read_text(encoding="utf-8"))["casos"]


@pytest.fixture
def fictitious_data(session):
    # ALTER TABLE é transacional no PostgreSQL: o rollback devolve a numeração.
    for table in TABLES:
        session.execute(sq.text(f"ALTER TABLE {table} ALTER COLUMN id RESTART"))
    run_sql_file(session.connection().connection,
                 DOCS / "sql/04-dados-ficticios-testes.sql", keep_transaction=True)
    # Sem isto, o rollback de um caso recusado desfaria também os dados (savepoint).
    session.commit()


def params():
    for case in CASES:
        marks = [pytest.mark.xfail(reason=case["falha_conhecida"])] if "falha_conhecida" in case else []
        yield pytest.param(case, id=case["caso"], marks=marks)


@pytest.mark.parametrize("case", list(params()))
def test_case(api, fictitious_data, table_counts, case):
    before = table_counts()
    response = api("POST", "/maintenances", case["body"])
    expected = case["esperado"]
    assert response.status == expected["status"], response.body

    if expected["status"] == 201:
        assert table_counts() == before | {
            "maintenance": before["maintenance"] + 1,
            "subsets_maintenance": before["subsets_maintenance"] + len(response.body["subset_ids"]),
        }
    else:
        assert response.body["code"] == expected["code"]
        assert table_counts() == before  # nada gravado pela metade


def test_case_names_are_unique():
    names = [c["caso"] for c in CASES]
    assert len(names) == len(set(names))
