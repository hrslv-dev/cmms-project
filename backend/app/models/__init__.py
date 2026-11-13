"""Models SQLAlchemy do CMMS — um por tabela do banco.

Os relacionamentos referenciam as outras classes pelo nome (por exemplo,
``Mapped[list[SubsetModel]]``), e o SQLAlchemy só resolve esses nomes quando
configura os mappers, na primeira consulta. Se algum módulo de model ainda não
tiver sido importado nesse momento, ocorre ``InvalidRequestError`` ("failed to
locate a name").

Importar todos os models aqui resolve isso de forma central: o Python executa
este ``__init__`` antes de qualquer ``from app.models.<modulo> import ...``,
portanto as sete classes sempre estão registradas, não importa qual delas foi
importada primeiro.
"""

from app.models.machine_model import MachineModel
from app.models.maintenance_model import MaintenanceModel
from app.models.operator_model import OperatorModel
from app.models.subset_maintenance_model import SubsetMaintenanceModel
from app.models.subset_model import SubsetModel
from app.models.technical_function_model import TechnicalFunctionModel
from app.models.technician_model import TechnicianModel

__all__ = [
    "MachineModel",
    "MaintenanceModel",
    "OperatorModel",
    "SubsetMaintenanceModel",
    "SubsetModel",
    "TechnicalFunctionModel",
    "TechnicianModel",
]
