"""``MaintenanceCreate``: formato da entrada de ``POST /maintenances``.

Cada caso parte de um corpo válido e muda uma coisa só. Assim, a recusa só
pode vir daquela mudança, e o teste afirma o campo apontado, não o texto da
mensagem (que pode ser melhorado sem mudar a regra).
"""

import pytest
from pydantic import ValidationError

from app.schemas.maintenance_schema import MaintenanceCreate
from app.services.enums import MaintenanceType, ProblemCategory, ServiceCategory

VALID = {
    "machine_id": 1,
    "technician_id": 1,
    "started_at": "2026-11-20T08:00:00-03:00",
    "finished_at": "2026-11-20T10:30:00-03:00",
    "service": "Reparo",
    "maintenance_type": "Corretiva",
    "problem": "Mecânico",
}
REQUIRED = ("machine_id", "technician_id", "started_at", "finished_at", "service",
            "maintenance_type")


def error_fields(body) -> list:
    """Campos apontados pelos erros; ``None`` para regra entre campos."""
    with pytest.raises(ValidationError) as error:
        MaintenanceCreate.model_validate(body)
    return [e["loc"][0] if e["loc"] else None for e in error.value.errors()]


def test_valid_body_is_converted_to_enums():
    maintenance = MaintenanceCreate.model_validate(VALID)
    assert maintenance.service is ServiceCategory.REPAIR
    assert maintenance.maintenance_type is MaintenanceType.CORRECTIVE
    assert maintenance.problem is ProblemCategory.MECHANICAL


def test_optional_fields_have_safe_defaults():
    maintenance = MaintenanceCreate.model_validate(VALID)
    assert (maintenance.operator_id, maintenance.description, maintenance.subset_ids) == (
        None, None, [],
    )


@pytest.mark.parametrize("field", REQUIRED)
def test_required_field(field):
    body = {k: v for k, v in VALID.items() if k != field}
    assert error_fields(body) == [field]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("machine_id", 0), ("technician_id", -1), ("operator_id", 0),
        ("machine_id", "abc"), ("subset_ids", [1, 0]), ("subset_ids", None),
        ("service", "reparo"), ("service", "Inspecao"),
        ("maintenance_type", "Preditiva"),
        ("problem", "Hidráulico"), ("problem", ""),
        ("description", 5),
    ],
    ids=lambda v: repr(v),
)
def test_invalid_field(field, value):
    assert error_fields(VALID | {field: value}) == [field]


@pytest.mark.parametrize("field", ["id", "elapsed_time", "type"])
def test_unknown_field_is_rejected(field):
    """Id e duração são gerados pelo banco; ``type`` é ``maintenance_type`` na API."""
    assert field in error_fields(VALID | {field: "x"})


@pytest.mark.parametrize(
    "value",
    [
        0, 1763625600, "1763625600", "-1", True, None, "",
        "2026-11-20", "2026-11-20T08:00:00", "20261120T080000Z",
        "2026-02-30T08:00:00Z", "abc",
    ],
    ids=repr,
)
@pytest.mark.parametrize("field", ["started_at", "finished_at"])
def test_datetime_must_be_text_with_date_time_and_offset(field, value):
    assert error_fields(VALID | {field: value}) == [field]


@pytest.mark.parametrize(
    "value",
    ["2026-11-20T07:00:00-03:00", "2026-11-20T10:00:00Z", "2026-11-20 07:00:00-03:00"],
)
def test_accepted_datetime_formats(value):
    MaintenanceCreate.model_validate(VALID | {"started_at": value})


def test_problem_is_required_only_in_corrective():
    body = {k: v for k, v in VALID.items() if k != "problem"}
    assert error_fields(body) == [None]
    preventive = MaintenanceCreate.model_validate(body | {"maintenance_type": "Preventiva"})
    assert preventive.problem is None


def test_preventive_accepts_problem_from_the_list():
    body = VALID | {"maintenance_type": "Preventiva", "problem": "Elétrico"}
    assert MaintenanceCreate.model_validate(body).problem is ProblemCategory.ELECTRICAL


@pytest.mark.parametrize(
    ("finished_at", "accepted"),
    [
        ("2026-11-20T08:00:00-03:00", True),   # igual ao início
        ("2026-11-20T11:00:00Z", True),        # mesmo instante, outro fuso
        ("2026-11-20T10:59:59Z", False),       # 1 s antes do início
        ("2026-11-20T07:59:59-03:00", False),
    ],
)
def test_period_order_compares_instants(finished_at, accepted):
    body = VALID | {"finished_at": finished_at}
    if accepted:
        MaintenanceCreate.model_validate(body)
    else:
        assert error_fields(body) == [None]


@pytest.mark.parametrize(
    ("description", "expected"),
    [("  Troca do rolamento  ", "Troca do rolamento"), ("   ", None), ("", None), (None, None)],
)
def test_description_is_trimmed_and_blank_becomes_none(description, expected):
    assert MaintenanceCreate.model_validate(VALID | {"description": description}).description == expected


def test_repeated_subset_ids_are_removed_keeping_order():
    assert MaintenanceCreate.model_validate(VALID | {"subset_ids": [3, 1, 3, 1]}).subset_ids == [3, 1]


@pytest.mark.xfail(reason="Revisão de 25/11/2026: true é convertido em id 1")
def test_boolean_is_not_an_id():
    assert error_fields(VALID | {"machine_id": True}) == ["machine_id"]
