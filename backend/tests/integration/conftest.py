"""PostgreSQL descartável, sessão isolada por teste, dados e cliente da API.

Um servidor novo é criado em pasta temporária, só em 127.0.0.1, com a
estrutura de ``docs/sql/02-criar-estrutura-testes.sql`` (cópia da do ``cmms``),
e apagado no fim. Nenhum teste usa o banco real.
"""

import os
import secrets
import shutil
import socket
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest
import sqlalchemy as sq
import sqlalchemy.orm as orm

from app.api.dependencies import get_session
from app.models import (
    MachineModel,
    OperatorModel,
    SubsetModel,
    TechnicalFunctionModel,
    TechnicianModel,
)

DOCS = Path(__file__).parents[3] / "docs"
TABLES = (
    "machines", "subsets", "operators", "technical_functions",
    "technicians", "maintenance", "subsets_maintenance",
)
MISSING_ID = 999_999


def _postgres_bin() -> Path:
    """Pasta com ``initdb`` e ``pg_ctl``; ``CMMS_PG_BIN`` tem prioridade."""
    candidates = [Path(os.environ["CMMS_PG_BIN"])] if "CMMS_PG_BIN" in os.environ else []
    candidates.append(Path("/usr/lib/postgresql/15/bin"))
    if found := shutil.which("initdb"):
        candidates.append(Path(found).parent)
    for path in candidates:
        if (path / "initdb").exists() and (path / "pg_ctl").exists():
            return path
    pytest.exit("initdb/pg_ctl não encontrados. Defina CMMS_PG_BIN.", returncode=3)


@pytest.fixture(scope="session")
def pg_url():
    """Sobe o servidor descartável e devolve uma função ``nome do banco -> URL``."""
    binaries, password = _postgres_bin(), secrets.token_hex(12)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    with tempfile.TemporaryDirectory(prefix="cmms-tests-") as tmp:
        data, pwfile = Path(tmp, "data"), Path(tmp, "pw")
        pwfile.write_text(password)
        # Locale e fuso fixos: ordem alfabética e datas iguais em qualquer máquina.
        subprocess.run(
            [binaries / "initdb", "-D", data, "-U", "tester", "--pwfile", pwfile,
             "-A", "scram-sha-256", "-E", "UTF8", "--locale=pt_BR.UTF-8"],
            check=True, stdout=subprocess.DEVNULL,
        )
        options = (
            f"-p {port} -c listen_addresses=127.0.0.1 -c unix_socket_directories='' "
            "-c timezone=America/Sao_Paulo -c fsync=off"
        )
        subprocess.run(
            [binaries / "pg_ctl", "-D", data, "-w", "-o", options,
             "-l", Path(tmp, "log"), "start"],
            check=True, stdout=subprocess.DEVNULL,
        )
        try:
            yield lambda database: sq.URL.create(
                "postgresql+psycopg2", "tester", password, "127.0.0.1", port, database
            )
        finally:
            subprocess.run(
                [binaries / "pg_ctl", "-D", data, "-m", "immediate", "stop"],
                check=True, stdout=subprocess.DEVNULL,
            )


@pytest.fixture(scope="session")
def create_database(pg_url):
    """Função que cria um banco vazio no servidor descartável e devolve a engine."""
    engines = []

    def create(name: str) -> sq.Engine:
        admin = sq.create_engine(pg_url("postgres"), isolation_level="AUTOCOMMIT")
        with admin.connect() as connection:
            connection.execute(sq.text(f'CREATE DATABASE "{name}" TEMPLATE template0'))
        admin.dispose()
        engines.append(sq.create_engine(pg_url(name)))
        return engines[-1]

    yield create
    for engine in engines:
        engine.dispose()


def run_sql_file(connection, path: Path, keep_transaction: bool = False) -> None:
    """Executa um arquivo de ``docs/sql`` pelo cursor do driver (vários comandos).

    Com ``keep_transaction``, remove o BEGIN/COMMIT do arquivo para que ele
    rode dentro da transação do teste e seja desfeito no rollback.
    """
    script = path.read_text(encoding="utf-8")
    if keep_transaction:
        script = "\n".join(
            line for line in script.splitlines() if line.strip() not in ("BEGIN;", "COMMIT;")
        )
    connection.cursor().execute(script)


@pytest.fixture(scope="session")
def engine(create_database) -> sq.Engine:
    """Banco com a estrutura real (a trava do SQL exige o nome ``cmms_test``)."""
    engine = create_database("cmms_test")
    raw = engine.raw_connection()
    try:
        raw.driver_connection.autocommit = True
        run_sql_file(raw, DOCS / "sql/02-criar-estrutura-testes.sql")
    finally:
        raw.driver_connection.autocommit = False
        raw.close()
    return engine


@pytest.fixture
def session(engine):
    """Sessão cujos efeitos são todos desfeitos no fim do teste.

    Os Services fazem ``commit``. Com ``create_savepoint``, esse commit só
    libera um SAVEPOINT dentro da transação externa, que termina em rollback.
    As sequências de id não voltam: nunca compare com ids fixos.
    """
    with engine.connect() as connection:
        outer = connection.begin()
        session = orm.Session(connection, join_transaction_mode="create_savepoint")
        yield session
        session.close()
        outer.rollback()


@pytest.fixture
def table_counts(session):
    """Função que devolve a quantidade de linhas de cada tabela."""

    def counts() -> dict[str, int]:
        return {
            table: session.scalar(sq.text(f"SELECT count(*) FROM {table}"))
            for table in TABLES
        }

    return counts


@pytest.fixture
def data(session):
    """Cadastro base com casos que importam para as regras.

    - nomes com acento, para conferir a ordem alfabética do locale pt_BR;
    - um técnico cuja função foi desativada DEPOIS do cadastro;
    - uma máquina sem subconjuntos e um subconjunto de outra máquina.
    """
    active = TechnicalFunctionModel(name="Mecânica")
    inactive = TechnicalFunctionModel(name="Desativada")
    nova = MachineModel(name="Nova Bloc")
    other = MachineModel(name="Máquina 2")
    empty = MachineModel(name="Área Externa")
    session.add_all([active, inactive, nova, other, empty])
    session.flush()

    carlos = TechnicianModel(name="Carlos Lima", function_id=active.id)
    alvaro = TechnicianModel(name="Álvaro Souza", function_id=active.id)
    beatriz = TechnicianModel(name="Beatriz Rocha", function_id=inactive.id)
    joao = OperatorModel(name="João Pereira")
    ana = OperatorModel(name="Ana Silva")
    motor = SubsetModel(name="Motor", machine_id=nova.id)
    esteira = SubsetModel(name="Esteira", machine_id=nova.id)
    prensa = SubsetModel(name="Prensa", machine_id=other.id)
    session.add_all([carlos, alvaro, beatriz, joao, ana, motor, esteira, prensa])
    session.flush()
    inactive.active = False  # desativada depois de Beatriz já estar nela
    session.commit()

    return SimpleNamespace(
        function=active.id, inactive_function=inactive.id,
        machine=nova.id, other_machine=other.id, empty_machine=empty.id,
        technician=carlos.id, technician_in_inactive_function=beatriz.id,
        technicians=[alvaro.id, beatriz.id, carlos.id],  # ordem alfabética
        operator=ana.id, operators=[ana.id, joao.id],
        subsets=[esteira.id, motor.id],  # ordem alfabética, máquina Nova Bloc
        foreign_subset=prensa.id,
    )


@pytest.fixture
def payload(data):
    """Função que monta o JSON de uma manutenção válida, com alterações."""

    def build(**changes):
        return {
            "machine_id": data.machine,
            "technician_id": data.technician,
            "started_at": "2026-11-20T08:00:00-03:00",
            "finished_at": "2026-11-20T10:30:00-03:00",
            "service": "Reparo",
            "maintenance_type": "Corretiva",
            "problem": "Mecânico",
        } | changes

    return build


@pytest.fixture
def api(session, request_app):
    """Cliente da API real, com a sessão de cada requisição trocada pela do teste."""
    from app.main import app

    app.dependency_overrides[get_session] = lambda: session
    yield lambda method, path, body=None: request_app(app, method, path, body)
    app.dependency_overrides.clear()
