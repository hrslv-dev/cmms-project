"""Infraestrutura dos testes: PostgreSQL descartável, sessão isolada e cliente HTTP.

Os testes NUNCA usam o banco real. Um servidor PostgreSQL novo é criado em uma
pasta temporária, só em 127.0.0.1, e apagado no fim. A estrutura vem de
``docs/sql/02-criar-estrutura-testes.sql``, cópia da estrutura do ``cmms``.
"""

import os

# Trava: precisa vir ANTES de qualquer import de ``app``. ``load_dotenv`` não
# sobrescreve variáveis já definidas, então o ``.env`` real é ignorado. Se um
# teste usar a engine da aplicação por engano, a conexão falha (porta 1).
os.environ.update(
    DB_HOST="127.0.0.1", DB_PORT="1", DB_NAME="blocked_by_tests",
    DB_USER="blocked", DB_PASSWORD="blocked",
)

import asyncio
import json
import secrets
import shutil
import socket
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import pytest
import sqlalchemy as sq
import sqlalchemy.orm as orm

from app.models import (
    MachineModel,
    OperatorModel,
    SubsetModel,
    TechnicalFunctionModel,
    TechnicianModel,
)

SCHEMA_SQL = Path(__file__).parents[2] / "docs/sql/02-criar-estrutura-testes.sql"
PG_USER = "tester"


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
    binaries = _postgres_bin()
    password = secrets.token_hex(12)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    with tempfile.TemporaryDirectory(prefix="cmms-tests-") as tmp:
        data, pwfile = Path(tmp, "data"), Path(tmp, "pw")
        pwfile.write_text(password)  # a pasta temporária só é legível pelo dono
        subprocess.run(
            [binaries / "initdb", "-D", data, "-U", PG_USER, "--pwfile", pwfile,
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
                "postgresql+psycopg2", PG_USER, password, "127.0.0.1", port, database
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


@pytest.fixture(scope="session")
def engine(create_database) -> sq.Engine:
    """Banco com a estrutura real (a trava do SQL exige o nome ``cmms_test``)."""
    engine = create_database("cmms_test")
    raw = engine.raw_connection()
    try:
        raw.driver_connection.autocommit = True  # o arquivo já tem BEGIN/COMMIT
        raw.cursor().execute(SCHEMA_SQL.read_text(encoding="utf-8"))
        raw.driver_connection.autocommit = False
    finally:
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
def data(session):
    """Cadastro mínimo: duas máquinas, seus subconjuntos, técnico e operador."""
    function = TechnicalFunctionModel(name="Mecânica")
    inactive = TechnicalFunctionModel(name="Desativada", active=False)
    machine = MachineModel(name="Nova Bloc")
    other_machine = MachineModel(name="Outra Máquina")
    operator = OperatorModel(name="Ana Silva")
    session.add_all([function, inactive, machine, other_machine, operator])
    session.flush()
    technician = TechnicianModel(name="João Souza", function_id=function.id)
    subsets = [SubsetModel(name=n, machine_id=machine.id) for n in ("Esteira", "Motor")]
    foreign = SubsetModel(name="Prensa", machine_id=other_machine.id)
    session.add_all([technician, *subsets, foreign])
    session.commit()
    # Só ids: não dependem do estado da sessão.
    return SimpleNamespace(
        function=function.id, inactive_function=inactive.id,
        machine=machine.id, other_machine=other_machine.id,
        technician=technician.id, operator=operator.id,
        subsets=[s.id for s in subsets], foreign_subset=foreign.id,
    )


@pytest.fixture
def payload(data):
    """Função que monta o JSON de uma manutenção válida, com alterações opcionais."""

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


@dataclass
class Response:
    status: int
    body: object
    headers: dict[str, str]
    raised: Exception | None  # exceção relançada ao servidor (erro 500)


@pytest.fixture
def request_app():
    """Função que chama um app ASGI direto, sem servidor e sem dependência extra."""

    def call(app, method, path, body=None) -> Response:
        if body is None or isinstance(body, bytes):
            raw = body or b""
        else:
            raw = json.dumps(body).encode()
        scope = {
            "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
            "method": method, "path": path, "raw_path": path.encode(),
            "root_path": "", "scheme": "http", "query_string": b"",
            "headers": [(b"content-type", b"application/json")],
            "server": ("test", 80), "client": ("test", 1),
        }
        sent, raised = [], None

        async def receive():
            return {"type": "http.request", "body": raw, "more_body": False}

        async def send(message):
            sent.append(message)

        try:
            asyncio.run(app(scope, receive, send))
        except Exception as exc:
            raised = exc
            if not sent:
                raise
        content = b"".join(m.get("body", b"") for m in sent)
        headers = {k.decode(): v.decode() for k, v in sent[0]["headers"]}
        return Response(sent[0]["status"], json.loads(content or b"null"), headers, raised)

    return call
