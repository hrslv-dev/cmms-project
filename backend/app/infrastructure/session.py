"""Criação de sessões SQLAlchemy para uso nos repositories e models."""

from sqlalchemy.orm import Session, sessionmaker

from .conf.engine import Engine_factory


engine = Engine_factory.create_db_engine()
SessionLocal = sessionmaker(bind=engine)


def create_session() -> Session:
    """Cria uma sessão; quem a utiliza controla commit, rollback e fechamento."""
    return SessionLocal()
