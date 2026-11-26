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


class ServiceCategory(StrEnum):
    """Serviços aceitos em ``maintenance.service``.

    Espelha o ``CHECK ck_maintenance_service`` do banco (as mesmas 10 opções,
    com a mesma grafia e acentuação). Validar na aplicação dá uma mensagem
    clara antes de o ``CHECK`` recusar a linha com um ``IntegrityError``.
    Se o ``CHECK`` mudar no banco, este Enum precisa mudar junto.
    """

    INSPECTION = "Inspeção"
    LUBRICATION = "Lubrificação"
    REPLACEMENT = "Substituição"
    ADJUSTMENT = "Ajuste"
    CLEANING = "Limpeza"
    REPAIR = "Reparo"
    INSTALLATION = "Instalação"
    CONFIGURATION = "Configuração"
    CALIBRATION = "Calibração"
    MODIFICATION = "Modificação"


class ProblemCategory(StrEnum):
    """Valores aceitos em ``maintenance.problem``.

    Regra SÓ da aplicação: no banco a coluna continua ``TEXT`` livre, então uma
    escrita direta (fora do Service) ainda aceita qualquer texto.
    """

    MECHANICAL = "Mecânico"
    ELECTRICAL = "Elétrico"
    OTHER = "Outro"
