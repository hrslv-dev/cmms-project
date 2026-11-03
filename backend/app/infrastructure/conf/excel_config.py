"""Configuração do arquivo Excel usado como fonte ou destino auxiliar."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


# Raiz do repositório, usada para resolver workbook configurado com caminho relativo.
PROJECT_ROOT = Path(__file__).resolve().parents[4]


def _env_bool(name: str, default: bool) -> bool:
    """Interpreta uma variável de ambiente como booleano ou retorna o padrão.

    Aceita `1/true/yes/on` e `0/false/no/off`, sem diferenciar maiúsculas.
    Lança `ValueError` para qualquer outro texto.
    """
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized not in {"1", "true", "yes", "on", "0", "false", "no", "off"}:
        raise ValueError(f"{name} deve ser um valor booleano, recebido: {value!r}")
    return normalized in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class ExcelConnectionConfig:
    """Agrupa o caminho `.xlsx` e o controle de log, sem depender do dialeto.

    A instância é imutável. `workbook_path` identifica o arquivo e `echo`
    controla se o SQLAlchemy imprime o SQL emitido.
    """

    workbook_path: Path
    echo: bool = False

    @classmethod
    def from_env(cls) -> "ExcelConnectionConfig":
        """Lê o `.env`, resolve e valida o caminho do workbook e cria a configuração.

        Usa `CMMS_EXCEL_WORKBOOK_PATH` ou `var/spreadsheets/cmms.xlsx`.
        Caminhos relativos são resolvidos a partir da raiz do projeto. A extensão
        precisa ser `.xlsx`; este método não cria nem abre o arquivo.
        """
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
