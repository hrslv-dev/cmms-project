"""Caso de uso para registrar uma manutenção."""

import sqlalchemy.orm as orm

from backend.app.models.manutencao import HistoricoManutencao
from backend.app.repositories.historico_manutencao_repository import (
    HistoricoManutencaoRepository,
)
from backend.app.schemas.manutencao import ManutencaoCreate


class ManutencaoService:
    """Coordena validação de entrada, model, repository e transação.

    O schema já chega validado pela API. Este serviço transforma seus dados
    num model, pede ao repository para adicioná-lo e confirma a transação.
    """

    def __init__(self, session: orm.Session) -> None:
        """Recebe a sessão da requisição e compartilha-a com o repository."""
        self.session = session
        self.repository = HistoricoManutencaoRepository(session)

    def registrar(self, dados: ManutencaoCreate) -> HistoricoManutencao:
        """Cria e persiste uma manutenção a partir do schema de entrada."""
        # O nome dos campos do schema corresponde aos atributos do model.
        manutencao = HistoricoManutencao(**dados.model_dump())

        try:
            # O repository adiciona à sessão, mas deixa a transação para cá.
            self.repository.add(manutencao)
            self.session.flush()
            # Atualiza valores gerados pelo banco, como id e tempo_manutencao.
            self.session.refresh(manutencao)
            self.session.commit()
        except Exception:
            # Se a gravação falhar (por exemplo, uma FK inexistente), desfaz
            # tudo que esta operação adicionou à transação e propaga o erro.
            self.session.rollback()
            raise

        return manutencao
