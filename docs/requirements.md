# Requisitos do Projeto CMMS

## 1. Requisitos Funcionais da V1

Com base no que estruturamos até agora, aqui está a consolidação para a V1.

---

### 📦 Módulo: Máquinas

| ID | Requisito |
|---|---|
| **RF01** | Cadastrar máquina |
| **RF02** | Consultar máquinas |
| **RF03** | Editar máquina |

#### RF01 — Cadastrar máquina
O sistema deve permitir cadastrar máquinas contendo, inicialmente:
- Identificação
- Nome
- Descrição
- Status

#### RF02 — Consultar máquinas
O sistema deve permitir visualizar as máquinas cadastradas.

#### RF03 — Editar máquina
O sistema deve permitir alterar os dados de uma máquina cadastrada.

---

### 🔧 Módulo: Componentes

| ID | Requisito |
|---|---|
| **RF04** | Cadastrar componente |
| **RF05** | Associar componente a uma máquina |
| **RF06** | Consultar componentes |
| **RF07** | Consultar componentes de uma máquina |

#### RF04 — Cadastrar componente
O sistema deve permitir cadastrar componentes.

#### RF05 — Associar componente a uma máquina
O sistema deve permitir associar cada componente a uma máquina.

#### RF06 — Consultar componentes
O sistema deve permitir visualizar os componentes cadastrados.

#### RF07 — Consultar componentes de uma máquina
O sistema deve permitir visualizar quais componentes pertencem a determinada máquina.

---

### 👷 Módulo: Técnicos

| ID | Requisito |
|---|---|
| **RF08** | Cadastrar técnico |
| **RF09** | Consultar técnicos |
| **RF10** | Editar técnico |

#### RF08 — Cadastrar técnico
O sistema deve permitir cadastrar técnicos contendo, inicialmente:
- Nome
- Função

#### RF09 — Consultar técnicos
O sistema deve permitir visualizar os técnicos cadastrados.

#### RF10 — Editar técnico
O sistema deve permitir alterar os dados cadastrais de um técnico.

---

### 🔨 Módulo: Manutenção

> ⭐ **Este é o coração do sistema.**

| ID | Requisito |
|---|---|
| **RF11** | Registrar manutenção |
| **RF12** | Associar manutenção a uma máquina |
| **RF13** | Associar componente à manutenção |
| **RF14** | Associar técnico à manutenção |
| **RF15** | Classificar o tipo de manutenção |
| **RF16** | Registrar problema |
| **RF17** | Registrar serviço |
| **RF18** | Registrar observações |

#### RF11 — Registrar manutenção
O sistema deve permitir registrar uma atividade de manutenção. O registro deve conter:
- Data
- Máquina
- Componente (quando aplicável)
- Técnico responsável
- Tipo de manutenção
- Problema identificado
- Serviço realizado
- Observações

#### RF12 — Associar manutenção a uma máquina
Toda manutenção registrada deve estar relacionada a uma máquina.

#### RF13 — Associar componente à manutenção
O sistema deve permitir informar o componente relacionado à manutenção, quando aplicável.

#### RF14 — Associar técnico à manutenção
O sistema deve permitir informar o técnico responsável pela execução da manutenção.

#### RF15 — Classificar o tipo de manutenção
O sistema deve permitir classificar a manutenção. Inicialmente:
- Corretiva
- Preventiva
- Preditiva (se mantida na V1)

#### RF16 — Registrar problema
O sistema deve permitir registrar o problema ou falha identificada.

#### RF17 — Registrar serviço
O sistema deve permitir registrar o serviço executado.

#### RF18 — Registrar observações
O sistema deve permitir registrar informações adicionais relacionadas à manutenção.

---

### 📊 Módulo: Histórico

| ID | Requisito |
|---|---|
| **RF19** | Consultar histórico de manutenção |
| **RF20** | Visualizar detalhes da manutenção |
| **RF21** | Filtrar histórico |

#### RF19 — Consultar histórico de manutenção
O sistema deve permitir visualizar todas as manutenções registradas.

#### RF20 — Visualizar detalhes da manutenção
O sistema deve permitir consultar individualmente os detalhes de uma manutenção.

#### RF21 — Filtrar histórico
O sistema deve permitir filtrar manutenções por:
- Máquina
- Componente
- Técnico
- Tipo
- Período

---

### 📈 Módulo: Indicadores

> Para a primeira versão, mantém-se os indicadores que os dados atuais realmente suportam.

| ID | Requisito |
|---|---|
| **RF22** | Exibir total de manutenções |
| **RF23** | Exibir manutenções corretivas |
| **RF24** | Exibir manutenções preventivas |
| **RF25** | Exibir manutenções por máquina |
| **RF26** | Exibir manutenções por componente |
| **RF27** | Exibir evolução temporal |
| **RF28** | Exibir indicadores em painel |

#### RF22 — Exibir total de manutenções
O sistema deve calcular a quantidade total de manutenções registradas.

#### RF23 — Exibir manutenções corretivas
O sistema deve calcular a quantidade de manutenções classificadas como corretivas.

#### RF24 — Exibir manutenções preventivas
O sistema deve calcular a quantidade de manutenções classificadas como preventivas.

#### RF25 — Exibir manutenções por máquina
O sistema deve apresentar a quantidade de intervenções realizadas em cada máquina.

#### RF26 — Exibir manutenções por componente
O sistema deve apresentar a quantidade de intervenções relacionadas a cada componente.

#### RF27 — Exibir evolução temporal
O sistema deve permitir analisar a quantidade de manutenções ao longo do tempo. Inicialmente, por mês.

#### RF28 — Exibir indicadores em painel
O sistema deve apresentar os principais indicadores em uma interface de visualização gerencial.

---

## 2. Requisitos Não Funcionais

> Lista objetiva de requisitos não-funcionais para a V1.

| ID | Requisito |
|---|---|
| **RNF01** | Usabilidade |
| **RNF02** | Integridade dos dados |
| **RNF03** | Persistência |
| **RNF04** | Escalabilidade |
| **RNF05** | Manutenibilidade |
| **RNF06** | Desempenho |
| **RNF07** | Compatibilidade |

### RNF01 — Usabilidade
O sistema deve possuir uma interface simples e intuitiva, permitindo que usuários com pouco conhecimento técnico consigam registrar e consultar informações.

### RNF02 — Integridade dos dados
O sistema deve impedir registros inconsistentes.

**Exemplo:**
- Uma manutenção não pode ser associada a um componente pertencente a outra máquina.

### RNF03 — Persistência
Os dados cadastrados devem ser armazenados permanentemente em banco de dados.

### RNF04 — Escalabilidade
A arquitetura deve permitir a adição futura de novos módulos, como:
- Estoque
- Ordens de serviço
- Manutenção preventiva
- Autenticação
- Integração com WhatsApp

### RNF05 — Manutenibilidade
O código deve possuir uma organização que facilite alterações futuras.

### RNF06 — Desempenho
As operações básicas de cadastro, consulta e filtragem devem apresentar resposta adequada para o volume inicial de dados.

### RNF07 — Compatibilidade
O sistema deve funcionar inicialmente através de navegador web moderno.

---

## 3. Regras de Negócio

> Essas regras são importantes porque vão virar validações no backend e, em alguns casos, restrições no banco.

| ID | Descrição |
|---|---|
| **RN01** | Máquina com ID única |
| **RN02** | Máquina com nome obrigatório |
| **RN03** | Máquina com status válido |
| **RN04** | Componente associado a máquina existente |
| **RN05** | Componente não pode estar em máquina inexistente |
| **RN06** | Técnico com ID única |
| **RN07** | Técnico com nome obrigatório |
| **RN08** | Manutenção associada a máquina existente |
| **RN09** | Componente da manutenção pertence à máquina selecionada |
| **RN10** | Técnico da manutenção deve existir no cadastro |
| **RN11** | Tipo de manutenção deve ser categoria permitida |
| **RN12** | Data da manutenção deve ser válida |

### RN01 — Toda máquina deve possuir identificação única
Cada máquina deve ter um identificador único que não pode ser duplicado.

### RN02 — Toda máquina deve possuir nome
O nome é um campo obrigatório para toda máquina cadastrada.

### RN03 — Toda máquina deve possuir um status válido
O status deve estar dentro das opções permitidas pelo sistema.

### RN04 — Todo componente deve estar associado a uma máquina existente
Um componente só pode ser cadastrado se a máquina a qual se destina existe.

### RN05 — Um componente não pode estar associado a uma máquina inexistente
Validação de integridade referencial.

### RN06 — Todo técnico deve possuir identificação única
Cada técnico deve ter um identificador único.

### RN07 — Todo técnico deve possuir nome
O nome é um campo obrigatório para todo técnico cadastrado.

### RN08 — Toda manutenção deve estar associada a uma máquina existente
Uma manutenção só pode ser registrada se referencia uma máquina que existe no sistema.

### RN09 — O componente informado em uma manutenção deve pertencer à máquina selecionada
⚠️ **Essa será uma validação muito importante.**

Garante que não haja inconsistências ao registrar manutenção de um componente que não pertence à máquina informada.

### RN10 — O técnico informado em uma manutenção deve existir no cadastro
Validação de integridade referencial para técnicos.

### RN11 — O tipo de manutenção deve pertencer às categorias permitidas
As categorias permitidas são:
- Corretiva
- Preventiva
- Preditiva

### RN12 — A data da manutenção deve ser válida
A data informada deve ser uma data válida e respeitar as restrições do negócio.