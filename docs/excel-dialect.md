# Persistência auxiliar em planilhas Excel

O projeto usa o pacote [`sqlalchemy-excel`](https://pypi.org/project/sqlalchemy-excel/) para abrir workbooks `.xlsx` como tabelas através do dialeto `excel` do SQLAlchemy. Essa integração é opcional e independente da conexão PostgreSQL existente. O requisito está limitado à linha 0.4.x do dialeto, cuja passagem de opções ao DB-API está refletida nesta implementação.

## Configuração

As variáveis podem ser definidas no ambiente do processo ou no arquivo `.env` de `backend/app/infrastructure/persistence/`:

| Variável | Padrão | Finalidade |
|---|---|---|
| `CMMS_EXCEL_WORKBOOK_PATH` | `var/spreadsheets/cmms.xlsx` | Caminho do workbook. Caminhos relativos são resolvidos a partir da raiz do repositório. |
| `CMMS_EXCEL_SQL_ECHO` | `false` | Exibe o SQL emitido pelo SQLAlchemy. |
| `CMMS_EXCEL_DBAPI_ENGINE` | `openpyxl` | Implementação local do driver `excel-dbapi`. |
| `CMMS_EXCEL_CREATE_IF_MISSING` | `true` | Permite ao driver criar o arquivo se ainda não existir. |
| `CMMS_EXCEL_DATA_ONLY` | `false` | Controla a leitura de valores calculados versus fórmulas. |
| `CMMS_EXCEL_SANITIZE_FORMULAS` | `true` | Ativa a sanitização de fórmulas configurada no driver. |
| `CMMS_EXCEL_FILE_LOCKING` | `true` | Ativa o bloqueio de arquivo do driver para gravações locais. |

Os módulos `excel_config.py` e `excel_plugin.py` mantêm separadas as opções do arquivo e as opções específicas do dialeto. As opções que o dialeto 0.4.x não lê da URL são passadas diretamente ao DB-API por `connect_args`. `ExcelEngineFactory`, em `excel_engine.py`, compõe as duas configurações e entrega uma `sqlalchemy.engine.Engine` que pode ser injetada em um repositório ou serviço.

## Uso

Instale as dependências a partir da pasta `backend`:

```bash
pip install -r requirements.txt
```

Crie a engine onde a integração for usada; a conexão é aberta sob demanda pelo SQLAlchemy:

```python
from backend.app.infrastructure.persistence.excel_engine import ExcelEngineFactory

engine = ExcelEngineFactory().create_engine()
try:
    with engine.connect() as connection:
        # Use tabelas/abas e operações SQL compatíveis com sqlalchemy-excel.
        ...
finally:
    engine.dispose()
```

O caminho do workbook também pode ser injetado diretamente, o que facilita testes e jobs com arquivos diferentes:

```python
from pathlib import Path

from backend.app.infrastructure.persistence.excel_config import ExcelConnectionConfig
from backend.app.infrastructure.persistence.excel_engine import ExcelEngineFactory

factory = ExcelEngineFactory(
    connection_config=ExcelConnectionConfig(Path("/dados/importacao.xlsx"))
)
```

## Limites de uso

Excel deve ser tratado como origem/destino auxiliar para importação, exportação ou relatórios pequenos; o PostgreSQL continua sendo a persistência principal do CMMS. O dialeto não oferece garantias equivalentes a um banco relacional em concorrência, integridade referencial ou transações. O suporte a expressões SQL e tipos também é limitado; por exemplo, blobs, arrays e JSON não são suportados. Para detalhes atualizados, consulte a [documentação do pacote](https://github.com/yeongseon/sqlalchemy-excel).
