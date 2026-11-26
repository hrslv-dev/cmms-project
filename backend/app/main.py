"""Ponto de entrada da API. Executar em ``backend/``: ``uvicorn app.main:app``.

Também serve o frontend: ``GET /`` devolve a página e ``/static`` os arquivos
(CSS, JS, fontes, imagens). Montar o frontend na raiz faria um método errado
numa rota da API (``GET /maintenances``) responder 404 em vez de 405.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.error_handlers import register_error_handlers
from app.api.routes import machines, maintenances, operators, technicians

FRONTEND = Path(__file__).resolve().parents[2] / "frontend"

app = FastAPI(title="CMMS API")
register_error_handlers(app)

for module in (machines, technicians, operators, maintenances):
    app.include_router(module.router)


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    """Página da Tela 1 (Registrar manutenção)."""
    return FileResponse(FRONTEND / "index.html")


app.mount("/static", StaticFiles(directory=FRONTEND / "static"), name="static")
