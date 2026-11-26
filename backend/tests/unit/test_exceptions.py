"""Erros de domínio: ``code`` e ``details`` formam o contrato com o frontend."""

import pytest

from app.services import exceptions as ex


def all_domain_errors(cls=ex.DomainError):
    for sub in cls.__subclasses__():
        yield sub
        yield from all_domain_errors(sub)


def test_each_domain_error_has_its_own_code():
    classes = list(all_domain_errors())
    assert all("code" in vars(cls) for cls in classes), "subclasse sem code próprio"
    assert len({cls.code for cls in classes}) == len(classes), "code repetido"


@pytest.mark.parametrize(
    ("error", "details"),
    [
        (ex.NotFoundError("machine", 9), {"resource": "machine", "id": 9}),
        (ex.InactiveFunctionError(2, "Antiga"), {"function_id": 2, "function_name": "Antiga"}),
        (ex.SubsetMachineMismatchError(5, 2, 1),
         {"subset_id": 5, "subset_machine_id": 2, "maintenance_machine_id": 1}),
        (ex.DuplicateSubsetLinkError(1, 5), {"maintenance_id": 1, "subset_id": 5}),
        (ex.DuplicateOperatorError(3, "Ana Silva"), {"existing_id": 3, "existing_name": "Ana Silva"}),
    ],
    ids=lambda v: type(v).__name__ if isinstance(v, Exception) else "",
)
def test_details(error, details):
    assert error.details == details
    assert str(error)  # há mensagem para exibir


def test_errors_without_data_have_empty_details():
    assert ex.InvalidProblemError("msg").details == {}


@pytest.mark.parametrize(
    "resource",
    ["machine", "technician", "operator", "subset", "maintenance", "technical_function"],
)
def test_not_found_knows_every_resource(resource):
    assert ex.NotFoundError(resource, 1).details["resource"] == resource
