"""Criação da engine SQLAlchemy para o dialeto Excel."""

from importlib import import_module

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import NullPool

from .excel_config import ExcelConnectionConfig
from .excel_plugin import ExcelDialectConfig


class ExcelEngineFactory:
    """Monta uma engine Excel independente da engine PostgreSQL do CMMS.

    Recebe configurações por injeção ou carrega os padrões do ambiente. A engine
    retornada pode ser passada a serviços e repositórios que precisem do workbook.
    """

    def __init__(
        self,
        connection_config: ExcelConnectionConfig | None = None,
        dialect_config: ExcelDialectConfig | None = None,
    ) -> None:
        """Guarda configurações injetadas ou carrega cada configuração do ambiente.

        A construção da factory não abre conexão nem cria o arquivo Excel.
        """
        self.connection_config = connection_config or ExcelConnectionConfig.from_env()
        self.dialect_config = dialect_config or ExcelDialectConfig.from_env()

    def create_engine(self) -> Engine:
        """Importa o dialeto, prepara a pasta e retorna uma engine SQLAlchemy.

        Se sqlalchemy-excel não estiver instalado, lança `RuntimeError` com
        instrução de instalação. Cria os diretórios pais do workbook, mas não
        conecta nem cria o arquivo nesse ponto. Usa `NullPool` para não manter
        conexões abertas no pool; o chamador deve chamar `dispose()` ao terminar.
        """
        try:
            # O pacote instalado registra o dialeto `excel` via entry point.
            # Importá-lo também mantém compatibilidade com uso a partir do source checkout.
            import_module("sqlalchemy_excel")
        except ModuleNotFoundError as exc:
            if exc.name == "sqlalchemy_excel":
                raise RuntimeError(
                    "O dialeto Excel não está instalado. Instale as dependências de "
                    "backend/requirements.txt."
                ) from exc
            raise

        workbook_path = self.connection_config.workbook_path
        workbook_path.parent.mkdir(parents=True, exist_ok=True)

        return create_engine(
            self.dialect_config.build_url(str(workbook_path)),
            connect_args=self.dialect_config.build_connect_args(),
            echo=self.connection_config.echo,
            # Fecha a conexão ao sair do context manager e evita manter o arquivo aberto.
            poolclass=NullPool,
        )
