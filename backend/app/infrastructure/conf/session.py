"""Criação de sessões SQLAlchemy para uso nos repositories e models."""

import sqlalchemy.orm as orm

from .engine import Engine_factory


engine = Engine_factory.create_db_engine()
SessionLocal = orm.sessionmaker(bind=engine)


def create_session() -> orm.Session:
    """Cria uma sessão; quem a utiliza controla commit, rollback e fechamento."""
    return SessionLocal()
 