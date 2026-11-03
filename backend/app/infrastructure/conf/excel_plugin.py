"""Opções específicas do dialeto SQLAlchemy para arquivos Excel."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL


def _env_bool(name: str, default: bool) -> bool:
    """Converte texto de ambiente em booleano; lança `ValueError` se inválido.

    Considera verdadeiros `1/true/yes/on` e falsos `0/false/no/off`, ignorando
    maiúsculas e espaços externos. Usa `default` quando a variável não existe.
    """
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized not in {"1", "true", "yes", "on", "0", "false", "no", "off"}:
        raise ValueError(f"{name} deve ser um valor booleano, recebido: {value!r}")
    return normalized in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class ExcelDialectConfig:
    """Agrupa o driver `excel-dbapi` e opções do dialeto para o workbook local.

    Os valores padrão selecionam openpyxl, permitem criar arquivo ausente,
    leem fórmulas, sanitizam fórmulas e habilitam bloqueio local do arquivo.
    A instância é imutável.
    """

    dbapi_engine: str = "openpyxl"
    create_if_missing: bool = True
    data_only: bool = False
    sanitize_formulas: bool = True
    file_locking: bool = True

    @classmethod
    def from_env(cls) -> "ExcelDialectConfig":
        """Carrega as opções do dialeto a partir do ambiente e do `.env` vizinho.

        Usa `CMMS_EXCEL_DBAPI_ENGINE` e as variáveis `CMMS_EXCEL_*` booleanas.
        Um valor booleano fora dos formatos aceitos causa `ValueError`.
        """
        load_dotenv(dotenv_path=Path(__file__).with_name(".env"))
        return cls(
            dbapi_engine=os.getenv("CMMS_EXCEL_DBAPI_ENGINE", "openpyxl"),
            create_if_missing=_env_bool("CMMS_EXCEL_CREATE_IF_MISSING", True),
            data_only=_env_bool("CMMS_EXCEL_DATA_ONLY", False),
            sanitize_formulas=_env_bool("CMMS_EXCEL_SANITIZE_FORMULAS", True),
            file_locking=_env_bool("CMMS_EXCEL_FILE_LOCKING", True),
        )

    def build_url(self, workbook_path: str) -> URL:
        """Monta a URL SQLAlchemy `excel` para o arquivo informado.

        Inclui o caminho, o nome do backend DB-API e `autocommit=false`, para
        que alterações sejam confirmadas explicitamente. Não abre o arquivo.
        """
        return URL.create(
            drivername="excel",
            database=workbook_path,
            query={
                "engine": self.dbapi_engine,
                "autocommit": "false",
            },
        )

    def build_connect_args(self) -> dict[str, bool]:
        """Retorna opções de criação, leitura, sanitização e locking para o DB-API.

        Esses parâmetros são passados por `create_engine(connect_args=...)`,
        pois o dialeto sqlalchemy-excel 0.4.x não os encaminha a partir da URL.
        """
        # excel-dbapi recebe essas opções diretamente; sqlalchemy-excel 0.4.x
        # não encaminha esses parâmetros da query string do URL.
        return {
            "create": self.create_if_missing,
            "data_only": self.data_only,
            "sanitize_formulas": self.sanitize_formulas,
            "file_locking": self.file_locking,
        }
