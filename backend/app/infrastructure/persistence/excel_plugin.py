"""Opções específicas do dialeto SQLAlchemy para arquivos Excel."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized not in {"1", "true", "yes", "on", "0", "false", "no", "off"}:
        raise ValueError(f"{name} deve ser um valor booleano, recebido: {value!r}")
    return normalized in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class ExcelDialectConfig:
    """Configuração do driver DB-API e das opções encaminhadas pelo dialeto."""

    dbapi_engine: str = "openpyxl"
    create_if_missing: bool = True
    data_only: bool = False
    sanitize_formulas: bool = True
    file_locking: bool = True

    @classmethod
    def from_env(cls) -> "ExcelDialectConfig":
        load_dotenv(dotenv_path=Path(__file__).with_name(".env"))
        return cls(
            dbapi_engine=os.getenv("CMMS_EXCEL_DBAPI_ENGINE", "openpyxl"),
            create_if_missing=_env_bool("CMMS_EXCEL_CREATE_IF_MISSING", True),
            data_only=_env_bool("CMMS_EXCEL_DATA_ONLY", False),
            sanitize_formulas=_env_bool("CMMS_EXCEL_SANITIZE_FORMULAS", True),
            file_locking=_env_bool("CMMS_EXCEL_FILE_LOCKING", True),
        )

    def build_url(self, workbook_path: str) -> URL:
        return URL.create(
            drivername="excel",
            database=workbook_path,
            query={
                "engine": self.dbapi_engine,
                "autocommit": "false",
            },
        )

    def build_connect_args(self) -> dict[str, bool]:
        # excel-dbapi recebe essas opções diretamente; sqlalchemy-excel 0.4.x
        # não encaminha esses parâmetros da query string do URL.
        return {
            "create": self.create_if_missing,
            "data_only": self.data_only,
            "sanitize_formulas": self.sanitize_formulas,
            "file_locking": self.file_locking,
        }
