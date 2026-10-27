# Resumo do projeto CMMS

**Revisão do repositório:** 26/10/2026

Este documento resume o que está registrado na documentação, no código e no histórico Git até a revisão. Ele distingue funcionalidades implementadas de requisitos que ainda estão planejados. Nenhum teste foi executado durante esta revisão.

## Objetivo e escopo definido

O CMMS pretende apoiar o cadastro de máquinas, componentes, técnicos e operadores, o registro e a consulta de manutenções e, futuramente, a apresentação de indicadores em um painel. Os requisitos da V1 estão consolidados em [`requirements.md`](requirements.md) e cobrem:

- cadastro e consulta de máquinas, componentes e técnicos;
- registro de manutenção ligado a máquina, componente e técnico, com tipo, problema, serviço, data, horários e observações;
- histórico consultável e filtrável por máquina, componente, técnico, tipo e período;
- indicadores de volume, tipo, máquina, componente e evolução mensal;
- integridade dos dados, persistência, usabilidade e possibilidade de expansão.

## Evolução registrada

O histórico do Git mostra o desenvolvimento em etapas:

1. **Conexão e persistência:** configuração de variáveis de ambiente, exclusão de credenciais do Git, conexão PostgreSQL com `psycopg2` e criação de engines SQLAlchemy.
2. **Organização do backend:** separação do código em infraestrutura de persistência, modelos, repositories, serviços, schemas e API.
3. **Mapeamento do domínio:** modelos SQLAlchemy para máquinas, componentes, técnicos, operadores e histórico de manutenção, com chaves, relacionamentos e restrições compatíveis com o esquema PostgreSQL usado pelo projeto.
4. **Acesso a dados:** CRUD compartilhado em `BaseRepository` e consultas próprias para cada entidade, incluindo filtros do histórico.
5. **Verificação dos repositories:** criação de testes de integração PostgreSQL que verificam inclusão, leitura, atualização, remoção e consultas específicas. Os casos fazem rollback ao terminar.
6. **Persistência auxiliar Excel:** configuração separada para abrir workbooks `.xlsx` pelo dialeto SQLAlchemy, documentada como apoio a importações, exportações ou relatórios pequenos.
7. **Primeiro fluxo HTTP:** adição de uma API FastAPI para registrar uma manutenção, com validação Pydantic, service, sessão por requisição e persistência.

## O que existe hoje

### Backend e persistência

- **FastAPI** é inicializado em `backend/app/main.py` com o título `CMMS API`.
- **PostgreSQL** é o banco principal. As credenciais vêm de variáveis de ambiente ou do arquivo `.env` local, que está ignorado pelo Git.
- A engine SQLAlchemy configura pool e verificação de conexão. A dependência `get_db_session` fornece uma sessão por requisição e a fecha ao final.
- Os modelos representam as tabelas `maquinas`, `componentes`, `tecnicos`, `operadores` e `historico_manutencao`. IDs são gerados pelo banco; há chaves estrangeiras e restrições para categorias e horários.
- O histórico guarda máquina, técnico, componente, operador, tipo, problema, serviço, descrição, data e horas. A duração é uma coluna calculada no banco a partir dos horários.
- `BaseRepository` reúne inclusão, busca por ID, listagem paginada, atualização e exclusão. Os repositories concretos acrescentam consultas por nome, função, máquina, vínculos do histórico, período e tipo.
- Os repositories não confirmam transações: o serviço chamador controla `commit` e `rollback`.

### API de manutenção

O único endpoint HTTP implementado é:

| Método e caminho | Comportamento |
|---|---|
| `POST /manutencoes/` | Valida os dados, registra a manutenção e responde com HTTP 201 e os dados persistidos, incluindo ID e duração calculada. |

O schema de entrada restringe tipo a `Corretiva` ou `Preventiva`, serviço a uma lista de dez categorias e IDs a números positivos. Também rejeita campos extras e verifica que a hora final, quando informada, seja posterior à hora inicial. Em caso de erro de persistência, o service reverte a transação e propaga a exceção.

### Excel

A integração Excel é independente da engine PostgreSQL e ainda não aparece conectada aos fluxos de negócio. As opções incluem caminho do workbook, leitura de fórmulas, sanitização e bloqueio de arquivo. A documentação ressalta que Excel é armazenamento auxiliar e não oferece as garantias de concorrência e integridade de um banco relacional.

### Testes e documentação

- `tests/test_repositories_crud.py` contém cinco testes de integração: máquinas, componentes, técnicos, operadores e histórico de manutenção.
- `tests/run_repositories_crud.py` oferece uma saída explicativa para executar essa suíte.
- A suíte depende de um PostgreSQL configurado no ambiente. O histórico de commits registra CRUD como testado; a suíte não foi reexecutada nesta revisão.
- `docs/requirements.md`, `ESTRUTURA.md` e `docs/excel-dialect.md` descrevem requisitos, organização e integração Excel.
- O `README.md` está vazio. A pasta `frontend/` existe, mas não contém arquivos de implementação no repositório.

## Lacunas e diferenças em relação aos requisitos

- **API ainda parcial:** não há endpoints de CRUD para máquinas, componentes, técnicos ou operadores; nem leitura, edição, remoção, listagem ou filtros de manutenções.
- **Interface e indicadores:** o frontend e o painel de indicadores continuam como requisitos, sem implementação localizada.
- **Vínculo componente-máquina:** a regra RN08 exige que o componente da manutenção pertença à máquina selecionada. O fluxo atual valida IDs positivos e as chaves estrangeiras confirmam que cada registro existe, mas não há validação de que o componente pertence àquela máquina.
- **Componente opcional:** os requisitos descrevem o componente como aplicável quando necessário; o modelo PostgreSQL mapeado e o schema atual exigem `componente_id`.
- **Operador obrigatório no endpoint:** o schema exige `operador_id` e o modelo do histórico o associa à manutenção, embora esse campo não apareça entre os dados listados no RF11.
- **Esquema do banco:** não foi localizada uma ferramenta de migração ou rotina de criação/atualização do esquema. O código mapeia as tabelas existentes e pressupõe que o PostgreSQL esteja preparado.
- **Cobertura da API:** os testes presentes cobrem repositories; não foi localizado teste automatizado para o endpoint, schemas ou service recém-adicionados.
- **Requisitos não funcionais:** autenticação e autorização, entre outros itens citados como possíveis expansões, não estão implementados.

## Estado do repositório na revisão

O branch local `main` estava um commit à frente de `origin/main`, com a árvore de trabalho limpa antes da criação deste resumo. Esse commit mais recente adiciona a sessão por requisição, schemas, service e endpoint de criação de manutenção.

## Próximos passos sugeridos

1. Definir se componente e operador serão obrigatórios no registro de manutenção e alinhar requisitos, banco e API.
2. Implementar e testar a validação de que o componente selecionado pertence à máquina informada.
3. Adicionar testes automatizados para schema, service e endpoint de criação.
4. Completar os endpoints de consulta e os CRUDs previstos para a V1.
5. Decidir e iniciar a interface e os indicadores previstos.
6. Documentar como preparar o banco e como iniciar o backend; preencher o `README.md`.
