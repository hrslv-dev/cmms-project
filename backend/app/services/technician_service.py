import sqlalchemy.orm as orm

from app.models.technical_function_model import TechnicalFunctionModel
from app.models.technician_model import TechnicianModel
from app.repository.technical_function_repository import TechnicalFunctionRepository
from app.repository.technician_repository import TechnicianRepository
from app.services.exceptions import InactiveFunctionError, NotFoundError


class TechnicianService:
    """Casos de uso de técnicos.

    Regra aplicada: um técnico só pode RECEBER uma função técnica ativa, tanto
    no cadastro quanto na troca de função. A foreign key do banco só garante
    que a função existe; ela não olha a coluna ``active``.

    Técnicos que já estavam em uma função depois desativada continuam válidos:
    a regra vale apenas no momento de atribuir a função.

    Transação: cada método público é uma unidade de trabalho. Os repositories
    só fazem ``flush``; o ``commit`` (ou ``rollback`` em caso de erro) é feito
    aqui, no fim do caso de uso.
    """

    def __init__(self, session: orm.Session) -> None:
        self.session = session
        self.technician_repository = TechnicianRepository(session)
        self.function_repository = TechnicalFunctionRepository(session)

    def create_technician(self, name: str, function_id: int) -> TechnicianModel:
        """Cadastra um técnico em uma função existente e ativa."""
        try:
            function = self._get_active_function(function_id)
            technician = self.technician_repository.add(
                TechnicianModel(name=name, function_id=function.id)
            )
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        return technician

    def change_function(self, technician_id: int, function_id: int) -> TechnicianModel:
        """Move um técnico existente para outra função, que deve estar ativa."""
        try:
            technician = self.technician_repository.search_by_id(technician_id)
            if technician is None:
                raise NotFoundError("Técnico", technician_id)
            function = self._get_active_function(function_id)
            technician.function_id = function.id
            self.session.flush()
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        return technician

    def _get_active_function(self, function_id: int) -> TechnicalFunctionModel:
        """Retorna a função, garantindo que existe e está ativa."""
        function = self.function_repository.search_by_id(function_id)
        if function is None:
            raise NotFoundError("Função técnica", function_id)
        if not function.active:
            raise InactiveFunctionError(function.id, function.name)
        return function
