# Tela 1 — Registrar manutenção (contexto para o Claude Code)

> Estado: 25/11/2026. Protótipo visual da Tela 1, desenhado com o Claude no chat.
> Este arquivo descreve a tela e como cada campo vira o JSON da API.
> O backend de referência é o repositório `hrslv-dev/cmms-project`, branch `develop`.
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

| Para que | O que devolve | Observação |
|---|---|---|
| Seleção de máquina | lista de `{id, name}` | `MachineService.list_machines()` |
| Subconjuntos da máquina | lista de `{id, name}` | `SubsetService.list_subsets_by_machine(machine_id)`; `NotFoundError` se a máquina não existe |
| Seleção de técnico | lista de `{id, name}` | `TechnicianService.list_technicians()` |
| Seleção de operador | lista de `{id, name}` | `OperatorService.list_operators()`, ordem alfabética |
| Cadastro de operador | `{id, name}` do criado | `OperatorService.create_operator(name)` |
| Confirmação | a manutenção gravada | `MaintenanceRead`, com `elapsed_time` como duração ISO 8601 (ex.: `PT2H30M`) |

A tela mostra **nomes**, e a ficha de entrada leva **ids**.

## Estado do backend (para o Claude Code situar-se)

Pronto e testado: models, persistência, repositories, services da Tela 1 e as fichas de
**entrada**:

- `MaintenanceCreate` (`schemas/maintenance_schema.py`): `extra="forbid"`, ids com `gt=0`,
  `AwareDatetime` em `started_at`/`finished_at` (ambos obrigatórios), Enums para `service`,
  `maintenance_type` e `problem`, `description` aparada e vazia vira `None`, `subset_ids`
  sem repetidos e com ids positivos. Recusa Corretiva sem `problem` e fim anterior ao início.
- `OperatorCreate` (`schemas/operator_schema.py`): só `name`. As regras do nome ficam no
  `OperatorService` (nome completo, caracteres, tamanho, duplicidade).

Ainda **não existe**: fichas de saída (`Read`), rotas da API, `main.py`, sessão de banco
por requisição, tradução de erros de domínio para HTTP.

Decisões em aberto sobre as fichas `Read`: se `TechnicianRead` é enxuta (`id`, `name`) ou
reaproveita a `TechnicianResponse`; se `SubsetRead` leva `machine_id`; se `MaintenanceRead`
inclui `subset_ids`. Formato de erro proposto: `code` e `message` (e `existing_id`/
`existing_name` para operador duplicado), ainda sem decisão.

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
