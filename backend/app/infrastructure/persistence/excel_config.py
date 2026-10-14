"""Configuração do arquivo Excel usado como fonte ou destino auxiliar."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[4]


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized not in {"1", "true", "yes", "on", "0", "false", "no", "off"}:
        raise ValueError(f"{name} deve ser um valor booleano, recebido: {value!r}")
    return normalized in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class ExcelConnectionConfig:
    """Localização e opções de conexão do workbook, sem dependência do dialeto."""

    workbook_path: Path
    echo: bool = False

    @classmethod
    def from_env(cls) -> "ExcelConnectionConfig":
        env_file = Path(__file__).with_name(".env")
        load_dotenv(dotenv_path=env_file)

        configured_path = os.getenv(
            "CMMS_EXCEL_WORKBOOK_PATH", "var/spreadsheets/cmms.xlsx"
        )
        workbook_path = Path(configured_path).expanduser()
        if not workbook_path.is_absolute():
            workbook_path = PROJECT_ROOT / workbook_path

        workbook_path = workbook_path.resolve()
        if workbook_path.suffix.lower() != ".xlsx":
            raise ValueError("CMMS_EXCEL_WORKBOOK_PATH deve apontar para um arquivo .xlsx")

        return cls(
            workbook_path=workbook_path,
            echo=_env_bool("CMMS_EXCEL_SQL_ECHO", False),
        )
