# Estrutura de diretórios do CMMS

Este documento descreve a organização atual do projeto e a responsabilidade de cada diretório. A estrutura separa a aplicação web, as regras do domínio, o acesso a dados, a interface e a documentação.

```text
cmms-project/
├── backend/
│   └── app/
│       ├── api/
│       ├── domain/
│       ├── schemas/
│       ├── services/
│       ├── repositories/
│       ├── infrastructure/
│       │   └── persistence/
│       │       ├── config.py
│       │       └── engine.py
│       └── main.py
├── frontend/
├── docs/
│   └── requirements.md
├── tests/
└── ESTRUTURA.md
```

## Diretórios e arquivos

- **`backend/`**: código do servidor e da aplicação backend.
- **`backend/app/`**: pacote principal da aplicação Python.
- **`backend/app/api/`**: rotas HTTP e controladores que recebem requisições e encaminham operações aos serviços.
- **`backend/app/domain/`**: entidades e conceitos centrais do CMMS, como máquinas, componentes, técnicos e manutenções.
- **`backend/app/schemas/`**: formatos de entrada e saída da API, incluindo validação e serialização de dados.
- **`backend/app/services/`**: casos de uso e regras de aplicação que coordenam domínio e persistência.
- **`backend/app/repositories/`**: abstrações e implementações de consulta e gravação de entidades.
- **`backend/app/infrastructure/`**: integrações técnicas usadas pela aplicação, como banco de dados e serviços externos.
- **`backend/app/infrastructure/persistence/`**: configuração de conexão e criação da engine do banco de dados. O arquivo `.env` local fica neste diretório e não deve ser versionado.
- **`backend/app/infrastructure/persistence/excel_config.py`**: caminho e opções de conexão para o workbook Excel.
- **`backend/app/infrastructure/persistence/excel_plugin.py`**: parâmetros específicos do dialeto `sqlalchemy-excel`.
- **`backend/app/infrastructure/persistence/excel_engine.py`**: factory que compõe as configurações e cria a engine SQLAlchemy para Excel.
- **`backend/app/main.py`**: ponto de entrada para configurar e iniciar a aplicação backend.
- **`frontend/`**: código da interface web consumida pelos usuários.
- **`docs/`**: documentação funcional e técnica do projeto.
- **`docs/requirements.md`**: requisitos funcionais, não funcionais e regras de negócio do CMMS.
- **`docs/excel-dialect.md`**: configuração, exemplo de uso e limites da integração SQLAlchemy com Excel.
- **`backend/requirements.txt`**: dependências Python do backend, incluindo o dialeto Excel.
- **`tests/`**: testes automatizados do backend e do frontend. Os scripts atuais `os_test.py` e `persistence_wip.py` são rascunhos preservados durante a reorganização e ainda não constituem uma suíte automatizada.
- **`ESTRUTURA.md`**: referência para a finalidade dos diretórios do projeto.

## Organização do backend

O fluxo esperado é: `api` recebe a requisição, `schemas` valida os dados, `services` executa o caso de uso, `domain` representa conceitos e regras do negócio, e `repositories` acessa os dados por meio da infraestrutura em `infrastructure/persistence`.
