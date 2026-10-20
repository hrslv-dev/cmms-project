"""Executa os testes de CRUD com uma saída explicativa no terminal.

Na raiz do projeto, rode:

    backend/venv/bin/python tests/run_repositories_crud.py

O script reutiliza os casos de ``test_repositories_crud.py``. Os testes se
conectam ao PostgreSQL configurado no backend e revertem a transação de cada
caso ao final.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = PROJECT_ROOT / "tests"

# Permite executar este arquivo diretamente da raiz do projeto ou de outra
# pasta, sem transformar ``tests`` em pacote Python.
for import_path in (PROJECT_ROOT, TESTS_DIR):
    path_string = str(import_path)
    if path_string not in sys.path:
        sys.path.insert(0, path_string)

from test_repositories_crud import RepositoryCrudIntegrationTests  # noqa: E402


SCENARIOS: dict[str, tuple[str, tuple[str, ...]]] = {
    "test_maquina_crud_e_consultas_por_nome": (
        "Máquinas",
        (
            "incluir e reler uma máquina no PostgreSQL",
            "listar e buscar por nome e ID, incluindo os métodos de compatibilidade",
            "atualizar e excluir; conferir também o comportamento para ID inexistente",
        ),
    ),
    "test_componente_crud_e_consultas": (
        "Componentes",
        (
            "incluir um componente associado a uma máquina",
            "consultar por máquina e por nome",
            "atualizar e excluir o componente",
        ),
    ),
    "test_tecnico_crud_e_consultas": (
        "Técnicos",
        (
            "incluir e reler um técnico",
            "consultar por nome e função",
            "alterar a função e excluir o técnico",
        ),
    ),
    "test_operador_crud_e_consulta_por_nome": (
        "Operadores",
        (
            "incluir e reler um operador",
            "listar e consultar por nome",
            "atualizar e excluir o operador",
        ),
    ),
    "test_historico_crud_e_consultas": (
        "Histórico de manutenção",
        (
            "incluir uma manutenção ligada à máquina, componente, técnico e operador",
            "confirmar hora de início, hora de fim e duração calculada pelo banco",
            "filtrar por cada vínculo, período e tipo de manutenção",
            "atualizar e excluir o registro",
        ),
    ),
}


class DidacticTextResult(unittest.TextTestResult):
    """Mostra o objetivo de cada caso junto com seu resultado."""

    def startTest(self, test: unittest.case.TestCase) -> None:
        name = test.id().rsplit(".", 1)[-1]
        title, checks = SCENARIOS.get(name, (name, ()))
        self.stream.writeln(f"\n[{self.testsRun + 1}] {title}")
        for check in checks:
            self.stream.writeln(f"    • {check}")
        super().startTest(test)

    def addSuccess(self, test: unittest.case.TestCase) -> None:
        super().addSuccess(test)
        self.stream.writeln("    Resultado: OK")

    def addFailure(self, test: unittest.case.TestCase, err: tuple) -> None:
        super().addFailure(test, err)
        self.stream.writeln("    Resultado: FALHOU (assertion)")

    def addError(self, test: unittest.case.TestCase, err: tuple) -> None:
        super().addError(test, err)
        self.stream.writeln("    Resultado: ERRO (exceção durante o teste)")

    def addSkip(self, test: unittest.case.TestCase, reason: str) -> None:
        super().addSkip(test, reason)
        self.stream.writeln(f"    Resultado: IGNORADO ({reason})")


class DidacticTextRunner(unittest.TextTestRunner):
    resultclass = DidacticTextResult


def main() -> int:
    print("=" * 72)
    print("TESTE DE INTEGRAÇÃO — REPOSITORIES CRUD")
    print("Banco: PostgreSQL configurado no .env do backend")
    print("Limpeza: cada caso termina com rollback da própria transação")
    print("=" * 72)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        RepositoryCrudIntegrationTests
    )
    result = DidacticTextRunner(stream=sys.stdout, verbosity=0).run(suite)

    print()
    if result.wasSuccessful():
        print(f"Conclusão: todos os {result.testsRun} cenários passaram.")
        return 0

    failed = len(result.failures) + len(result.errors)
    print(
        f"Conclusão: {result.testsRun - failed} de {result.testsRun} cenários passaram; "
        f"{failed} precisam de atenção."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
