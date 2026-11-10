"""Demonstra operações CRUD dos repositories contra o PostgreSQL configurado.

Os registros principais permanecem no banco. O nome inclui um sufixo único
para permitir executar o roteiro várias vezes sem sobrescrever dados prévios.
"""

from datetime import date, time
from uuid import uuid4

from sqlalchemy import inspect

from app.infrastructure.conf.session import SessionLocal
# Importa todos os models para registrá-los antes da configuração dos mappers.
from app.models import componentes_model, manutencoes_model, operadores_model, tecnico_model
from app.models.componentes_model import ComponentesModel
from app.models.manutencoes_model import ManutencoesModel
from app.models.maquinas_model import MaquinasModel
from app.models.operadores_model import OperadorModel
from app.models.tecnico_model import TecnicoModel
from app.repository.componentes_repository import Componentes_Repository
from app.repository.manutencoes_repository import ManutencoesRepository
from app.repository.maquina_repository import MaquinaRepository
from app.repository.operador_repository import OperadorRepository
from app.repository.tecnico_repository import TecnicoRepository


def require(condition: bool, message: str) -> None:
    """Interrompe o roteiro se uma operação não produzir o resultado esperado."""
    if not condition:
        raise AssertionError(message)


def main() -> None:
    tag = uuid4().hex[:8]
    print(f"Iniciando demonstração CRUD (identificador {tag})")

    with SessionLocal() as session:
        try:
            # Falha antes de inserir qualquer linha se o banco estiver incompleto.
            tabelas = set(inspect(session.get_bind()).get_table_names())
            requeridas = {
                "maquinas", "componentes", "historico_manutencao", "tecnicos", "operadores"
            }
            faltantes = sorted(requeridas - tabelas)
            if faltantes:
                raise RuntimeError(
                    "O banco conectado não possui as tabelas necessárias: "
                    + ", ".join(faltantes)
                    + ". Aplique/crie o esquema do projeto e execute novamente. "
                    "O roteiro não cria nem altera tabelas automaticamente."
                )

            maquinas = MaquinaRepository(session)
            componentes = Componentes_Repository(session)
            manutencoes = ManutencoesRepository(session)
            tecnicos = TecnicoRepository(session)
            operadores = OperadorRepository(session)

            # Cria uma máquina e seus componentes pela relação ORM.
            maquina = MaquinasModel(
                nome=f"Máquina de demonstração {tag}",
                componentes=[
                    ComponentesModel(nome=f"Motor {tag}"),
                    ComponentesModel(nome=f"Bomba {tag}"),
                ],
            )
            maquinas.add(maquina)
            session.flush()
            require(maquina.id is not None, "A máquina não recebeu ID após add/flush.")
            require(len(maquina.componentes) == 2, "Os componentes não foram associados.")
            print(f"ADD máquina: id={maquina.id}, componentes=2")

            tecnico = TecnicoModel(nome=f"Técnico {tag}", funcao="Mecânico")
            tecnicos.add(tecnico)
            operador = OperadorModel(nome=f"Operador {tag}")
            operadores.add(operador)
            session.flush()

            manutencao = ManutencoesModel(
                maquina=maquina,
                componente=maquina.componentes[0],
                tecnico=tecnico,
                operador=operador,
                tipo="Preventiva",
                problema="Verificação de rotina",
                servico="Inspeção",
                descricao="Registro criado pelo roteiro de demonstração",
                data_manutencao=date.today(),
                hora_inicio=time(9, 0),
                hora_fim=time(9, 30),
            )
            manutencoes.add(manutencao)
            session.commit()
            print(
                "ADD e COMMIT: técnico, operador e manutenção; "
                f"manutenção id={manutencao.id} persistida."
            )

            # Leitura por ID, listagens e paginação.
            require(maquinas.search_by_id(maquina.id) is not None, "search_by_id da máquina falhou.")
            require(componentes.search_by_id(maquina.componentes[0].id) is not None, "Busca do componente falhou.")
            require(tecnicos.search_by_id(tecnico.id) is not None, "Busca do técnico falhou.")
            require(operadores.search_by_id(operador.id) is not None, "Busca do operador falhou.")
            require(manutencoes.search_by_id(manutencao.id) is not None, "Busca da manutenção falhou.")
            require(maquinas.search_by_id(-1) is None, "Busca inexistente deveria retornar None.")
            require(len(maquinas.list_all(limit=1)) == 1, "list_all com limit falhou.")
            require(len(maquinas.list_all(offset=1)) >= 0, "list_all com offset falhou.")
            require(len(componentes.list_by_maquinas_id(maquina.id)) == 2, "Filtro de componentes falhou.")
            require(len(manutencoes.list_by_maquinas(maquina.id)) == 1, "Filtro de manutenções por máquina falhou.")
            require(len(manutencoes.list_by_componentes(maquina.componentes[0].id)) == 1, "Filtro por componente falhou.")
            require(len(manutencoes.list_by_tecnicos(tecnico.id)) == 1, "Filtro por técnico falhou.")
            require(len(manutencoes.list_by_operadores(operador.id)) == 1, "Filtro por operador falhou.")
            require(len(tecnicos.list_all()) >= 1, "Listagem de técnicos falhou.")
            require(len(operadores.list_all()) >= 1, "Listagem de operadores falhou.")
            print("READ: buscas por ID, list_all/paginação e filtros específicos passaram.")

            # update_by_id testa validação; update testa merge de objeto detached.
            atualizado = maquinas.update_by_id(maquina.id, nome=f"Máquina revisada {tag}")
            require(atualizado is not None and atualizado.nome.endswith(tag), "update_by_id falhou.")
            require(maquinas.update_by_id(-1, nome="não existe") is None, "Atualização inexistente deveria retornar None.")
            try:
                maquinas.update_by_id(maquina.id, campo_inexistente="valor")
            except ValueError:
                pass
            else:
                raise AssertionError("update_by_id deveria rejeitar campo inexistente.")
            try:
                maquinas.update_by_id(maquina.id, id=123)
            except ValueError:
                pass
            else:
                raise AssertionError("update_by_id deveria rejeitar alteração do ID.")
            session.commit()

            detached = MaquinasModel(id=maquina.id, nome=f"Máquina via merge {tag}")
            merged = maquinas.update(detached)
            require(merged.nome.endswith(tag), "update/merge falhou.")
            session.commit()
            require(maquinas.search_by_id(maquina.id).nome == f"Máquina via merge {tag}", "Update não persistiu.")
            print("UPDATE: update_by_id, validações e update (merge) passaram e foram confirmados.")

            # Exclusão individual e por ID são demonstradas com linhas descartáveis.
            descartavel = MaquinasModel(nome=f"Excluir via delete {tag}")
            maquinas.add(descartavel)
            session.commit()
            maquinas.delete(descartavel)
            session.commit()
            require(maquinas.search_by_id(descartavel.id) is None, "delete não removeu a máquina.")

            descartavel_id = maquinas.add(MaquinasModel(nome=f"Excluir via ID {tag}")).id
            session.commit()
            require(maquinas.delete_by_id(descartavel_id), "delete_by_id deveria retornar True.")
            session.commit()
            require(not maquinas.delete_by_id(descartavel_id), "delete_by_id deveria retornar False após exclusão.")
            session.commit()
            print("DELETE: delete, delete_by_id (True/False) e confirmação no banco passaram.")

            print("Concluído. O conjunto principal de demonstração permanece persistido no banco.")
            print(
                f"IDs: máquina={maquina.id}, componentes="
                f"{maquina.componentes[0].id}/{maquina.componentes[1].id}, "
                f"técnico={tecnico.id}, operador={operador.id}, manutenção={manutencao.id}"
            )
        except Exception:
            session.rollback()
            raise


if __name__ == "__main__":
    main()
