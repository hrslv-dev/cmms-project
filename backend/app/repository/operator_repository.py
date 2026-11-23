import sqlalchemy as sq
import sqlalchemy.orm as orm

from app.infrastructure.base.base_repository import GenericRepository
from app.models.operator_model import OperatorModel


class OperatorRepository(GenericRepository[OperatorModel]):
    def __init__(self, session: orm.Session) -> None:
        super().__init__(session, OperatorModel)

    def list_ordered_by_name(self) -> list[OperatorModel]:
        """Lista todos os operadores em ordem alfabética.

        O ``id`` desempata nomes iguais. A ordem segue a collation do banco.
        """
        stmt = sq.select(OperatorModel).order_by(OperatorModel.name, OperatorModel.id)
        return list(self.session.scalars(stmt).all())

    def search_by_name_ignore_case(self, name: str) -> OperatorModel | None:
        """Busca um operador pelo nome, sem diferenciar maiúsculas de minúsculas.

        Os dois lados passam pelo ``lower()`` do PostgreSQL. Assim a comparação
        usa a mesma regra de conversão nos dois lados. Misturar o
        ``str.lower()`` do Python com o ``lower()`` do banco poderia dar
        resultados diferentes para letras acentuadas, conforme o locale do banco.

        ``operators.name`` não tem ``UNIQUE``, então pode haver mais de uma
        linha (por exemplo, gravada fora do Service). Nesse caso, devolve a
        mais antiga (menor ``id``) em vez de levantar ``MultipleResultsFound``.
        """
        stmt = (
            sq.select(OperatorModel)
            .where(sq.func.lower(OperatorModel.name) == sq.func.lower(name))
            .order_by(OperatorModel.id)
            .limit(1)
        )
        return self.session.scalars(stmt).first()
