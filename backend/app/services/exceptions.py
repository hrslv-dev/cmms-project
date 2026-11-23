"""Erros de domínio levantados pelos Services.

Todos herdam de ``DomainError``. Assim, a futura camada de API pode capturar
uma única classe base e traduzir cada subclasse para uma resposta HTTP,
sem conhecer detalhes do banco (``IntegrityError``) nem do ORM.
"""


class DomainError(Exception):
    """Base de todas as violações de regra de negócio."""


class NotFoundError(DomainError):
    """A entidade referenciada não existe."""

    def __init__(self, entity: str, entity_id: int) -> None:
        self.entity = entity
        self.entity_id = entity_id
        super().__init__(f"{entity} {entity_id} não encontrado(a).")


class InactiveFunctionError(DomainError):
    """Tentativa de atribuir uma função técnica inativa a um técnico."""

    def __init__(self, function_id: int, function_name: str) -> None:
        self.function_id = function_id
        super().__init__(
            f"A função técnica '{function_name}' (id {function_id}) está inativa "
            "e não pode ser atribuída a técnicos."
        )


class SubsetMachineMismatchError(DomainError):
    """O subconjunto pertence a uma máquina diferente da manutenção."""

    def __init__(
        self, subset_id: int, subset_machine_id: int, maintenance_machine_id: int
    ) -> None:
        self.subset_id = subset_id
        super().__init__(
            f"O subconjunto {subset_id} pertence à máquina {subset_machine_id}, "
            f"mas a manutenção é da máquina {maintenance_machine_id}."
        )


class DuplicateSubsetLinkError(DomainError):
    """O subconjunto já está vinculado a esta manutenção."""

    def __init__(self, maintenance_id: int, subset_id: int) -> None:
        super().__init__(
            f"O subconjunto {subset_id} já está vinculado à manutenção {maintenance_id}."
        )


class InvalidMaintenanceTypeError(DomainError):
    """O tipo informado não é ``Corretiva`` nem ``Preventiva``."""


class InvalidProblemError(DomainError):
    """``problem`` ausente em corretiva ou fora das categorias permitidas."""


class InvalidMaintenancePeriodError(DomainError):
    """``started_at``/``finished_at`` sem fuso, ausentes ou fim antes do início."""
