"""Valores fechados usados pelas regras de negócio.

``StrEnum`` (Python 3.11+) faz cada membro ser também uma ``str``:
``ProblemCategory.MECHANICAL == "Mecânico"`` é verdadeiro, e o valor pode ser
gravado diretamente em uma coluna de texto.
"""

from enum import StrEnum


class MaintenanceType(StrEnum):
    """Tipos aceitos em ``maintenance.type``.

    Espelha o ``CHECK ck_maintenance_type`` do banco. Existe na aplicação
    porque a regra de ``problem`` depende do tipo, e comparar com o literal
    ``"Corretiva"`` espalhado pelo código seria frágil.
    """

    CORRECTIVE = "Corretiva"
    PREVENTIVE = "Preventiva"


class ProblemCategory(StrEnum):
    """Valores aceitos em ``maintenance.problem``.

    Regra SÓ da aplicação: no banco a coluna continua ``TEXT`` livre, então uma
    escrita direta (fora do Service) ainda aceita qualquer texto.
    """

    MECHANICAL = "Mecânico"
    ELECTRICAL = "Elétrico"
    OTHER = "Outro"
