"""Repositories de consulta e gravação das entidades persistidas do CMMS."""

from backend.app.repositories.componentes_repository import ComponentsRepository
from backend.app.repositories.historico_manutencao_repository import (
    HistoricoManutencaoRepository,
)
from backend.app.repositories.maquinas_repository import MaquinaRepository
from backend.app.repositories.operadores_repository import OperadorRepository
from backend.app.repositories.tecnicos_repository import TecnicoRepository

__all__ = [
    "ComponentsRepository",
    "HistoricoManutencaoRepository",
    "MaquinaRepository",
    "OperadorRepository",
    "TecnicoRepository",
]
