from sqlalchemy.engine import Engine as SqlAlchemyEngine
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy.orm import sessionmaker


class Session:
    """Helpers for creating SQLAlchemy session factories and sessions."""

    @staticmethod
    def create_session_factory(
        engine: SqlAlchemyEngine | None = None,
    ) -> sessionmaker[OrmSession]:
        """Create a reusable factory that produces independent ORM sessions.

        An engine can be supplied directly, which keeps this function easy to
        test without opening a connection to the application's database.
        """
        if engine is None:
            from .engine import Engine

            engine = Engine.engine_factory()

        return sessionmaker(bind=engine, autoflush=False,autocommit=False)

    @staticmethod
    def create_new_session(
        session_factory: sessionmaker[OrmSession],
    ) -> OrmSession:
        """Create and return a new session from a SQLAlchemy sessionmaker.

        The caller owns the returned session and must close it when finished.
        """
        return session_factory()
