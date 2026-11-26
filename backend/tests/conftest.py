"""Itens comuns às duas camadas de teste.

- ``unit/``: sem banco de dados. Roda em qualquer máquina: ``pytest tests/unit``.
- ``integration/``: PostgreSQL descartável (ver ``integration/conftest.py``).
"""

import os

# Trava: precisa vir ANTES de qualquer import de ``app``. ``load_dotenv`` não
# sobrescreve variáveis já definidas, então o ``.env`` real é ignorado. Se algo
# usar a engine da aplicação por engano, a conexão falha (porta 1).
os.environ.update(
    DB_HOST="127.0.0.1", DB_PORT="1", DB_NAME="blocked_by_tests",
    DB_USER="blocked", DB_PASSWORD="blocked",
)

import asyncio
import json
from dataclasses import dataclass

import pytest


@dataclass
class Response:
    status: int
    body: object
    headers: dict[str, str]
    raised: Exception | None  # exceção relançada ao servidor (erro 500)


@pytest.fixture
def request_app():
    """Função que chama um app ASGI direto, sem servidor HTTP."""

    def call(app, method, path, body=None) -> Response:
        raw = body if body is None or isinstance(body, bytes) else json.dumps(body).encode()
        scope = {
            "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
            "method": method, "path": path, "raw_path": path.encode(),
            "root_path": "", "scheme": "http", "query_string": b"",
            "headers": [(b"content-type", b"application/json")],
            "server": ("test", 80), "client": ("test", 1),
        }
        sent, raised = [], None

        async def receive():
            return {"type": "http.request", "body": raw or b"", "more_body": False}

        async def send(message):
            sent.append(message)

        try:
            asyncio.run(app(scope, receive, send))
        except Exception as exc:  # o Starlette relança o erro 500 após responder
            raised = exc
            if not sent:
                raise
        content = b"".join(m.get("body", b"") for m in sent)
        headers = {k.decode(): v.decode() for k, v in sent[0]["headers"]}
        return Response(sent[0]["status"], json.loads(content or b"null"), headers, raised)

    return call
