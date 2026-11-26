# Tela 1 — Registrar manutenção (contexto para o Claude Code)

> Estado: 26/11/2026. Protótipo visual da Tela 1, desenhado com o Claude no chat.
> Este arquivo descreve a tela e como cada campo vira o JSON da API.
> O backend de referência é o repositório `hrslv-dev/maintenance_software`, branch `develop`.
> Para as regras de trabalho e do banco, vale o `CLAUDE.md` do repositório.
> O arquivo `Main.dc.html` (enviado junto) é só referência visual: tokens de cor,
> textos e estrutura. Ele usa um formato de canvas de design e **não é a base do front real**.

## Objetivo da tela

O técnico registra a manutenção **depois** de concluir o serviço. Não existe
cronômetro nem manutenção "em andamento" na v1: início e fim são digitados e os dois
são obrigatórios. Web primeiro; depois a mesma tela vai para tablet, então os alvos de
toque são grandes e há modo claro e modo escuro.

## Estrutura da tela

Cabeçalho com logo Uni-Stein e menu (Manutenção, Técnicos, Indicadores), alternância
claro/escuro. À esquerda, o formulário em 7 blocos numerados; à direita, o resumo com o botão
Salvar. Campos obrigatórios têm asterisco vermelho.

| Bloco | Controle | Obrigatório | Campo da API (`MaintenanceCreate`) |
|---|---|---|---|
| 1. Tipo de manutenção | duas opções (Preventiva com ícone de calendário, Corretiva com triângulo de aviso) | sim | `maintenance_type`: `"Preventiva"` ou `"Corretiva"` |
| 2. Máquina | seleção de uma máquina | sim | `machine_id` |
| 3. Subconjuntos | seleção múltipla, só os da máquina escolhida | não | `subset_ids` (lista de ids; `[]` se nada) |
| 4. Problema | aparece **só em Corretiva** | sim, em Corretiva | `problem`: `"Mecânico"`, `"Elétrico"` ou `"Outro"` |
| 5. Quem | técnico (ícone de chave) e operador (ícone de capacete) | técnico sim, operador não | `technician_id`, `operator_id` (ou `null`) |
| 6. Horários | data e hora de início e de fim, com botão "Agora" | sim | `started_at`, `finished_at` |
| 7. Serviço realizado | 10 opções em chips, escolher uma | sim | `service` |
| Descrição | texto livre, recolhido ("Adicionar descrição") | não | `description` |

As 10 opções de serviço (texto exato, com acento): Inspeção, Lubrificação, Substituição,
Ajuste, Limpeza, Reparo, Instalação, Configuração, Calibração, Modificação.

### Regras de comportamento

- **Subconjuntos dependem da máquina.** Ao trocar a máquina, a seleção de subconjuntos é
  limpa e a lista é recarregada.
- **Problema só em Corretiva.** Ao trocar para Preventiva, o front **limpa** o problema e
  envia `null` ou omite o campo. Não enviar texto vazio (`""`): o Enum recusa com 422.
- **Operador novo na hora.** Em "Quem", o botão "Novo operador" abre um campo de nome
  (Adicionar / Cancelar). O novo operador é criado antes de salvar a manutenção, e o `id`
  devolvido preenche a seleção.
- **Horários: 4 inputs, 2 campos.** A tela tem data e hora de início e data e hora de fim. O
  front junta cada par em um único valor ISO 8601 **com fuso**, por exemplo
  `2026-11-24T14:10:00-03:00` (ou `Z`). Sem fuso, a API responde 422.
  O botão "Agora" preenche com o horário atual.
- **Tempo decorrido** é calculado só na tela, para conferência. Não é enviado.
- **Avisos na tela, sem chamar a API:** "O fim está antes do início. Confira as datas." e
  "A duração passa de 12 horas. Confira os horários." Só o primeiro é regra; o segundo é
  um alerta.
- **Resumo à direita** repete as escolhas e mostra "Falta preencher: ..." enquanto houver
  obrigatório vazio.
- **Salvar** mostra a confirmação "Manutenção registrada" com a ação "Registrar outra".

## Dados que a tela precisa ler da API

| Para que | Rota | Resposta |
|---|---|---|
| Seleção de máquina | `GET /machines` | 200, lista de `{id, name}` em ordem alfabética |
| Subconjuntos da máquina | `GET /machines/{machine_id}/subsets` | 200, lista de `{id, name}` só daquela máquina; `[]` se não tiver; 404 se a máquina não existe |
| Seleção de técnico | `GET /technicians` | 200, lista de `{id, name}`; inclui técnicos de função desativada depois do cadastro |
| Seleção de operador | `GET /operators` | 200, lista de `{id, name}` |
| Novo operador | `POST /operators` com `{"name": "..."}` | 201, `{id, name}` com o nome normalizado |
| Salvar | `POST /maintenances` com a ficha `MaintenanceCreate` | 201, a manutenção gravada (`MaintenanceRead`) |

A tela mostra **nomes**, e a ficha de entrada leva **ids**. As listas seguem a ordem
alfabética do banco (`pt_BR`), com desempate pelo `id`.

`MaintenanceRead` devolve `id`, os campos enviados (já normalizados), `elapsed_time` como
duração ISO 8601 (`PT2H30M`, `P1DT2H`) e `subset_ids` em ordem crescente. Datas voltam com
fuso (`2026-11-24T14:10:00-03:00`).

### Erros

Todo erro tem o mesmo formato. O front decide pelo `code`, nunca pelo texto de `message`:

```json
{"code": "not_found", "message": "Máquina 99 não encontrado(a).",
 "details": {"resource": "machine", "id": 99}}
```

| Situação | Status | `code` | `details` |
|---|---|---|---|
| Id inexistente (na URL ou no corpo) | 404 | `not_found` | `resource`, `id` |
| Operador com nome já cadastrado (ignora maiúsculas e espaços) | 409 | `duplicate_operator` | `existing_id`, `existing_name` |
| Subconjunto de outra máquina | 422 | `subset_machine_mismatch` | `subset_id`, `subset_machine_id`, `maintenance_machine_id` |
| Fim no futuro ou início antes de 01/01/2000 | 422 | `invalid_maintenance_period` | `{}` |
| Nome de operador inválido | 422 | `invalid_operator_name` | `{}` |
| Formato da ficha | 422 | `validation_error` | `errors`: lista de `{field, message}` |
| Erro inesperado | 500 | `internal_error` | `{}` |

- Em `validation_error`, `field` aponta o campo (`subset_ids.1` para um item da lista).
  É `null` em regra entre campos (Corretiva sem problema, fim antes do início) e em JSON
  malformado: mostrar no topo do formulário.
- `duplicate_operator` permite oferecer "Usar este cadastro?" com `existing_id`.
- Fim no futuro tem tolerância de 5 minutos, para relógios levemente adiantados.
- Em qualquer erro, **nada é gravado**: nem a manutenção nem parte dos subconjuntos.

## Estado do backend (para o Claude Code situar-se)

Implementado e testado, camada por camada:

| Camada | Onde |
|---|---|
| Models, repositories e Services da Tela 1 | `app/models`, `app/repository`, `app/services` |
| Fichas de entrada: `MaintenanceCreate`, `OperatorCreate` | `app/schemas` |
| Fichas de saída: `MachineRead`, `SubsetRead`, `TechnicianRead`, `OperatorRead`, `MaintenanceRead` | `app/schemas` |
| Tradução de erros de domínio e de validação para HTTP | `app/api/error_handlers.py`, `app/schemas/error_schema.py` |
| Sessão de banco por requisição | `app/api/dependencies.py` |
| Rotas | `app/api/routes/` |
| Aplicação | `app/main.py` |

Executar em `backend/`, com o venv ativado: `uvicorn app.main:app --reload`. A
documentação interativa fica em `http://127.0.0.1:8000/docs`. Em desenvolvimento, o `.env`
aponta para o banco `cmms_test`, com dados fictícios (`docs/sql/04-dados-ficticios-testes.sql`).

Testes: `pytest` em `backend/` (unitários em `tests/unit`, sem banco; integração em
`tests/integration`, com PostgreSQL descartável). `docs/tests.json` reúne os casos de
`POST /maintenances`, também executados automaticamente.

Decisões fechadas em 25/11/2026: fichas `Read` simples só com `id` e `name`
(`TechnicianResponse` virou `TechnicianRead`); `MaintenanceRead` inclui `subset_ids`; erros
com `code`, `message` e `details`; id inexistente no corpo responde 404.

Ainda **não existe**: frontend, autenticação, CORS (necessário se o front rodar em outro
endereço ou porta) e rotas para cadastrar máquinas, subconjuntos e técnicos (a Tela 1 só
os lista).

## Identidade visual (tokens do protótipo)

Fonte Inter. Cores aproximadas, tiradas da logo da Uni-Stein:

| Token | Claro | Escuro |
|---|---|---|
| fundo | `#F1F4F7` | `#0E1720` |
| superfície | `#FFFFFF` | `#16222D` |
| texto | `#14202B` | `#EAF0F5` |
| primária | `#15446C` (azul-marinho) | `#45C2D2` |
| destaque | `#0A8798` (petróleo) | `#45C2D2` |
| aviso | fundo `#FFF1CC`, texto `#5C3F00` | fundo `#3D3000`, texto `#FFD875` |
| erro | fundo `#FDE9E7`, texto `#8F1D14` | fundo `#4A1D1A`, texto `#FFB4A9` |

No protótipo são placeholders: nomes de técnicos, operadores e subconjuntos, e "Máquina 2".
Os dados reais vêm do banco.

## Pontos conhecidos sem decisão

- `problem` é aceito em Preventiva (decisão de manter assim por ora).
- Model e banco divergem em `finished_at`/`elapsed_time` (NOT NULL no model; o banco ainda
  aceita NULL). Ver `docs/pendencia-alinhamento-banco.md`.
- Duplicidade de operador ignora maiúsculas e espaços, mas não acentos.
- Falhas conhecidas do backend, ainda abertas: `true` em um id é aceito como `1`; o
  caractere NUL na descrição causa erro 500. O front deve enviar ids numéricos e texto comum.
- Divergências entre o protótipo e o backend, adiadas: o protótipo recusa início igual ao
  fim (o backend aceita); o botão "Agora" só existe no fim; o protótipo abre com campos
  pré-preenchidos; ao trocar para Preventiva, o protótipo só esconde o problema (o front real
  deve limpá-lo); "Registrar outra" mantém técnico e horários.
- O protótipo não avisa fim no futuro; o backend recusa com `invalid_maintenance_period`.
