"""Ponto de entrada da aplicação FastAPI."""

from fastapi import FastAPI

from backend.app.api.manutencoes import router as manutencoes_router


app = FastAPI(title="CMMS API")
app.include_router(manutencoes_router)
