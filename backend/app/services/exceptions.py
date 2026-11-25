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
    """Período inválido.

    ``started_at``/``finished_at`` ausentes ou sem fuso, fim antes do início,
    início antes de ``EARLIEST_START`` ou fim no futuro.
    """


class InvalidDescriptionError(DomainError):
    """``description`` informada, mas vazia, só com espaços ou que não é texto."""


class InvalidServiceError(DomainError):
    """O serviço informado não está entre as 10 opções de ``ServiceCategory``."""


class InvalidOperatorNameError(DomainError):
    """O nome do operador não atende às regras de cadastro."""


class DuplicateOperatorError(DomainError):
    """Já existe um operador com o mesmo nome.

    ``existing_id`` permite que quem chamou (por exemplo, a futura API)
    aponte para o cadastro existente em vez de só recusar.
    """

    def __init__(self, existing_id: int, existing_name: str) -> None:
        self.existing_id = existing_id
        self.existing_name = existing_name
        super().__init__(
            f"Já existe o operador '{existing_name}' (id {existing_id})."
        )
