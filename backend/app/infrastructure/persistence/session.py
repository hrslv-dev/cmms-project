"""Dependência FastAPI que fornece sessões SQLAlchemy por requisição."""

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy.orm import Session, sessionmaker

from backend.app.infrastructure.persistence.engine import Engine_factory


@lru_cache(maxsize=1)
def _get_session_factory() -> sessionmaker[Session]:
    """Cria uma fábrica de sessões e reutiliza a engine no processo."""
    engine = Engine_factory.create_db_engine()
    return sessionmaker(bind=engine)


def get_db_session() -> Generator[Session, None, None]:
    """Abre uma sessão para a requisição e fecha-a ao terminar."""
    with _get_session_factory()() as session:
        yield session
