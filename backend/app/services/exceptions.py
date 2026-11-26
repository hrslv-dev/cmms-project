"""Erros de domínio levantados pelos Services.

Todos herdam de ``DomainError``. Assim, a futura camada de API pode capturar
uma única classe base e traduzir cada subclasse para uma resposta HTTP,
sem conhecer detalhes do banco (``IntegrityError``) nem do ORM.
"""

from typing import Any


class DomainError(Exception):
    """Base de todas as violações de regra de negócio.

    ``code`` identifica o erro para quem consome a API e não deve mudar depois
    de publicado. ``details`` leva dados extras. O status HTTP não fica aqui:
    quem o define é ``app/api/error_handlers.py``.
    """

    code = "domain_error"

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.details = details or {}
        super().__init__(message)


# Nome do recurso (usado em ``details``) e rótulo mostrado na mensagem.
_RESOURCE_LABELS = {
    "machine": "Máquina",
    "technician": "Técnico",
    "operator": "Operador",
    "subset": "Subconjunto",
    "maintenance": "Manutenção",
    "technical_function": "Função técnica",
}


class NotFoundError(DomainError):
    """A entidade referenciada não existe."""

    code = "not_found"

    def __init__(self, resource: str, entity_id: int) -> None:
        self.resource = resource
        self.entity = _RESOURCE_LABELS[resource]
        self.entity_id = entity_id
        super().__init__(
            f"{self.entity} {entity_id} não encontrado(a).",
            {"resource": resource, "id": entity_id},
        )


class InactiveFunctionError(DomainError):
    """Tentativa de atribuir uma função técnica inativa a um técnico."""

    code = "inactive_function"

    def __init__(self, function_id: int, function_name: str) -> None:
        self.function_id = function_id
        super().__init__(
            f"A função técnica '{function_name}' (id {function_id}) está inativa "
            "e não pode ser atribuída a técnicos.",
            {"function_id": function_id, "function_name": function_name},
        )


class SubsetMachineMismatchError(DomainError):
    """O subconjunto pertence a uma máquina diferente da manutenção."""

    code = "subset_machine_mismatch"

    def __init__(
        self, subset_id: int, subset_machine_id: int, maintenance_machine_id: int
    ) -> None:
        self.subset_id = subset_id
        super().__init__(
            f"O subconjunto {subset_id} pertence à máquina {subset_machine_id}, "
            f"mas a manutenção é da máquina {maintenance_machine_id}.",
            {
                "subset_id": subset_id,
                "subset_machine_id": subset_machine_id,
                "maintenance_machine_id": maintenance_machine_id,
            },
        )


class DuplicateSubsetLinkError(DomainError):
    """O subconjunto já está vinculado a esta manutenção."""

    code = "duplicate_subset_link"

    def __init__(self, maintenance_id: int, subset_id: int) -> None:
        super().__init__(
            f"O subconjunto {subset_id} já está vinculado à manutenção {maintenance_id}.",
            {"maintenance_id": maintenance_id, "subset_id": subset_id},
        )


class InvalidMaintenanceTypeError(DomainError):
    """O tipo informado não é ``Corretiva`` nem ``Preventiva``."""

    code = "invalid_maintenance_type"


class InvalidProblemError(DomainError):
    """``problem`` ausente em corretiva ou fora das categorias permitidas."""

    code = "invalid_problem"


class InvalidMaintenancePeriodError(DomainError):
    """Período inválido.

    ``started_at``/``finished_at`` ausentes ou sem fuso, fim antes do início,
    início antes de ``EARLIEST_START`` ou fim no futuro.
    """

    code = "invalid_maintenance_period"


class InvalidDescriptionError(DomainError):
    """``description`` informada, mas vazia, só com espaços ou que não é texto."""

    code = "invalid_description"


class InvalidServiceError(DomainError):
    """O serviço informado não está entre as 10 opções de ``ServiceCategory``."""

    code = "invalid_service"


class InvalidOperatorNameError(DomainError):
    """O nome do operador não atende às regras de cadastro."""

    code = "invalid_operator_name"


class DuplicateOperatorError(DomainError):
    """Já existe um operador com o mesmo nome.

    ``existing_id`` permite que quem chamou (por exemplo, a futura API)
    aponte para o cadastro existente em vez de só recusar.
    """

    code = "duplicate_operator"

    def __init__(self, existing_id: int, existing_name: str) -> None:
        self.existing_id = existing_id
        self.existing_name = existing_name
        super().__init__(
            f"Já existe o operador '{existing_name}' (id {existing_id}).",
            {"existing_id": existing_id, "existing_name": existing_name},
        )
