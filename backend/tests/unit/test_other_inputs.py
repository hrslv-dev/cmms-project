"""``OperatorCreate`` e ``TechnicianCreate``."""

import pytest
from pydantic import ValidationError

from app.schemas.operator_schema import OperatorCreate
from app.schemas.technician_schema import TechnicianCreate


def test_operator_name_is_passed_unchanged_to_the_service():
    """As regras do nome (normalização incluída) são do ``OperatorService``."""
    assert OperatorCreate(name="  ana   SILVA ").name == "  ana   SILVA "


@pytest.mark.parametrize("body", [{}, {"name": None}, {"name": 5}, {"name": "Ana Silva", "id": 1}])
def test_operator_invalid_body(body):
    with pytest.raises(ValidationError):
        OperatorCreate.model_validate(body)


def test_technician_name_is_trimmed():
    assert TechnicianCreate(name="  João Souza  ", function_id=1).name == "João Souza"


@pytest.mark.parametrize(
    "changes",
    [{"name": "x" * 101}, {"name": "      "}, {"function_id": 0}, {"function_id": "x"}, {"id": 1}],
    ids=str,
)
def test_technician_invalid_body(changes):
    with pytest.raises(ValidationError):
        TechnicianCreate.model_validate({"name": "João Souza", "function_id": 1} | changes)


def test_technician_name_limit_is_counted_after_trimming():
    """O limite é o da coluna ``technicians.name VARCHAR(100)``."""
    assert len(TechnicianCreate(name=" " + "x" * 100 + " ", function_id=1).name) == 100
