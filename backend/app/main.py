"""Ponto de entrada da API. Executar em ``backend/``: ``uvicorn app.main:app``."""

from fastapi import FastAPI

from app.api.error_handlers import register_error_handlers
from app.api.routes import machines, maintenances, operators, technicians

app = FastAPI(title="CMMS API")
register_error_handlers(app)

for module in (machines, technicians, operators, maintenances):
    app.include_router(module.router)
