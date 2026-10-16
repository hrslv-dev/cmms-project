"""Base declarativa comum às entidades persistidas do domínio."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base SQLAlchemy usada para registrar os modelos do CMMS."""

