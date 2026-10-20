"""Testes de integração dos repositories CRUD com o PostgreSQL configurado.

Execute a partir da raiz do projeto com:

    python -m unittest discover -s tests -p 'test_repositories_crud.py'

Os testes usam o banco apontado pelo arquivo `.env` da persistência. Cada teste
abre uma transação e faz rollback no encerramento, para não deixar dados de
teste gravados permanentemente.
"""

import unittest
from datetime import date, time, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from backend.app.models.componentes import Components
from backend.app.models.manutencao import HistoricoManutencao
from backend.app.models.maquina import Maquina
from backend.app.models.operadores import Operador
from backend.app.models.tecnicos import Tecnico
from backend.app.infrastructure.persistence.engine import Engine_factory
from backend.app.repositories import (
    ComponentsRepository,
    HistoricoManutencaoRepository,
    MaquinaRepository,
    OperadorRepository,
    TecnicoRepository,
)


class RepositoryCrudIntegrationTests(unittest.TestCase):
    """Confere o CRUD comum e as consultas específicas de cada repository."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = Engine_factory.create_db_engine()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.engine.dispose()

    def setUp(self) -> None:
        self.connection = self.engine.connect()
        self.transaction = self.connection.begin()
        self.session = Session(bind=self.connection)

    def tearDown(self) -> None:
        self.session.close()
        if self.transaction.is_active:
            self.transaction.rollback()
        self.connection.close()

    def _reload(self, repository, entity_id: int):
        """Limpa o cache da sessão para confirmar a leitura no banco."""
        self.session.expire_all()
        return repository.get_by_id(entity_id)

    @staticmethod
    def _unique_name(label: str) -> str:
        """Evita colisões com registros existentes ou outros testes."""
        return f"{label}-{uuid4().hex}"

    def test_maquina_crud_e_consultas_por_nome(self) -> None:
        repository = MaquinaRepository(self.session)
        machine_name = self._unique_name("Teste CRUD máquina")
        machine = repository.add(Maquina(nome=machine_name))
        self.session.flush()
        self.assertIsNotNone(machine.id)

        saved = self._reload(repository, machine.id)
        self.assertIsNotNone(saved)
        self.assertEqual(saved.nome, machine_name)
        self.assertIn(machine.id, [item.id for item in repository.list_all(limit=None)])
        self.assertEqual(
            [item.id for item in repository.list_by_name(machine_name)],
            [machine.id],
        )
        self.assertEqual(repository.search_id(machine.id).id, machine.id)
        self.assertEqual(repository.search_name(machine_name).id, machine.id)
        self.assertIn(machine.id, [item.id for item in repository.see_all()])

        updated = repository.update_by_id(machine.id, nome="Máquina atualizada")
        self.assertIsNotNone(updated)
        self.session.flush()
        self.assertEqual(self._reload(repository, machine.id).nome, "Máquina atualizada")

        self.assertTrue(repository.delete_by_id(machine.id))
        self.session.flush()
        self.assertIsNone(self._reload(repository, machine.id))
        self.assertFalse(repository.delete_by_id(-1))
        self.assertIsNone(repository.update_by_id(-1, nome="Inexistente"))

    def test_componente_crud_e_consultas(self) -> None:
        machine = MaquinaRepository(self.session).add(
            Maquina(nome=self._unique_name("Máquina do componente"))
        )
        self.session.flush()

        repository = ComponentsRepository(self.session)
        component_name = self._unique_name("Componente de teste")
        component = repository.add(
            Components(maquina_id=machine.id, nome=component_name)
        )
        self.session.flush()
        self.assertIsNotNone(component.id)

        saved = self._reload(repository, component.id)
        self.assertIsNotNone(saved)
        self.assertEqual(saved.maquina_id, machine.id)
        self.assertIn(component.id, [item.id for item in repository.list_all(limit=None)])
        self.assertEqual(
            [item.id for item in repository.list_by_machine_id(machine.id)],
            [component.id],
        )
        self.assertEqual(
            [item.id for item in repository.list_by_name(component_name)],
            [component.id],
        )

        repository.update_by_id(component.id, nome="Componente atualizado")
        self.session.flush()
        self.assertEqual(
            self._reload(repository, component.id).nome, "Componente atualizado"
        )

        self.assertTrue(repository.delete_by_id(component.id))
        self.session.flush()
        self.assertIsNone(self._reload(repository, component.id))

    def test_tecnico_crud_e_consultas(self) -> None:
        repository = TecnicoRepository(self.session)
        technician_name = self._unique_name("Técnico de teste")
        technician = repository.add(
            Tecnico(nome=technician_name, funcao="Mecânico")
        )
        self.session.flush()
        self.assertIsNotNone(technician.id)

        saved = self._reload(repository, technician.id)
        self.assertIsNotNone(saved)
        self.assertEqual(saved.funcao, "Mecânico")
        self.assertIn(technician.id, [item.id for item in repository.list_all(limit=None)])
        self.assertEqual(
            [item.id for item in repository.list_by_name(technician_name)],
            [technician.id],
        )
        self.assertIn(
            technician.id,
            [item.id for item in repository.list_by_function("Mecânico")],
        )

        repository.update_by_id(technician.id, funcao="Eletricista")
        self.session.flush()
        self.assertEqual(
            self._reload(repository, technician.id).funcao, "Eletricista"
        )

        self.assertTrue(repository.delete_by_id(technician.id))
        self.session.flush()
        self.assertIsNone(self._reload(repository, technician.id))

    def test_operador_crud_e_consulta_por_nome(self) -> None:
        repository = OperadorRepository(self.session)
        operator_name = self._unique_name("Operador de teste")
        operator = repository.add(Operador(nome=operator_name))
        self.session.flush()
        self.assertIsNotNone(operator.id)

        saved = self._reload(repository, operator.id)
        self.assertIsNotNone(saved)
        self.assertEqual(saved.nome, operator_name)
        self.assertIn(operator.id, [item.id for item in repository.list_all(limit=None)])
        self.assertEqual(
            [item.id for item in repository.list_by_name(operator_name)],
            [operator.id],
        )

        repository.update_by_id(operator.id, nome="Operador atualizado")
        self.session.flush()
        self.assertEqual(
            self._reload(repository, operator.id).nome, "Operador atualizado"
        )

        self.assertTrue(repository.delete_by_id(operator.id))
        self.session.flush()
        self.assertIsNone(self._reload(repository, operator.id))

    def test_historico_crud_e_consultas(self) -> None:
        machine = MaquinaRepository(self.session).add(
            Maquina(nome=self._unique_name("Máquina do histórico"))
        )
        technician = TecnicoRepository(self.session).add(
            Tecnico(nome=self._unique_name("Técnico do histórico"), funcao="Mecânico")
        )
        operator = OperadorRepository(self.session).add(
            Operador(nome=self._unique_name("Operador do histórico"))
        )
        self.session.flush()

        component = ComponentsRepository(self.session).add(
            Components(
                maquina_id=machine.id,
                nome=self._unique_name("Componente do histórico"),
            )
        )
        self.session.flush()

        repository = HistoricoManutencaoRepository(self.session)
        maintenance_date = date(2025, 1, 15)
        maintenance = repository.add(
            HistoricoManutencao(
                maquina_id=machine.id,
                tecnico_id=technician.id,
                componente_id=component.id,
                operador_id=operator.id,
                tipo="Preventiva",
                problema=None,
                servico="Inspeção",
                descricao="Registro de teste",
                data_manutencao=maintenance_date,
                hora_inicio=time(9, 0),
                hora_fim=time(10, 0),
            )
        )
        self.session.flush()
        self.assertIsNotNone(maintenance.id)

        saved = self._reload(repository, maintenance.id)
        self.assertIsNotNone(saved)
        self.assertEqual(saved.descricao, "Registro de teste")
        self.assertEqual(saved.hora_inicio, time(9, 0))
        self.assertEqual(saved.hora_fim, time(10, 0))
        self.assertEqual(saved.tempo_manutencao, timedelta(hours=1))
        self.assertIn(maintenance.id, [item.id for item in repository.list_all(limit=None)])
        self.assertEqual(
            [item.id for item in repository.list_by_machine_id(machine.id)],
            [maintenance.id],
        )
        self.assertEqual(
            [item.id for item in repository.list_by_technician_id(technician.id)],
            [maintenance.id],
        )
        self.assertEqual(
            [item.id for item in repository.list_by_component_id(component.id)],
            [maintenance.id],
        )
        self.assertEqual(
            [item.id for item in repository.list_by_operator_id(operator.id)],
            [maintenance.id],
        )
        self.assertIn(
            maintenance.id,
            [
                item.id
                for item in repository.list_between_dates(
                    maintenance_date, maintenance_date
                )
            ],
        )
        self.assertIn(
            maintenance.id,
            [item.id for item in repository.list_by_type("Preventiva")],
        )

        repository.update_by_id(maintenance.id, descricao="Descrição atualizada")
        self.session.flush()
        self.assertEqual(
            self._reload(repository, maintenance.id).descricao, "Descrição atualizada"
        )

        self.assertTrue(repository.delete_by_id(maintenance.id))
        self.session.flush()
        self.assertIsNone(self._reload(repository, maintenance.id))


if __name__ == "__main__":
    unittest.main()
