# Pendência: alinhar o banco ao model de `maintenance`

**Situação:** pendente, SQL não executado.
**Registrado em:** 24/11/2026, na branch `fix/defesa_sem_schema`.
**Responsável pela execução:** proprietário do projeto, manualmente.

## Divergência

A aplicação só registra manutenções já encerradas. Por isso, `finished_at` e
`elapsed_time` passaram a ser `NOT NULL` no `MaintenanceModel`. O banco não foi
alterado e continua aceitando `NULL` nas duas colunas.

| Coluna de `public.maintenance` | Model | Banco `cmms` |
| --- | --- | --- |
| `finished_at` | `NOT NULL` | aceita `NULL` |
| `elapsed_time` | `NOT NULL` | aceita `NULL` |

O estado do banco nesta tabela é o conferido em 23/11/2026 e informado pelo
proprietário em 24/11/2026. O catálogo não foi consultado de novo.

## Efeito enquanto não for alinhado

- O schema `MaintenanceCreate` e o `MaintenanceService` recusam `finished_at`
  ausente ou nulo. Quem usa esse caminho está protegido.
- `nullable=False` no model só vale para o DDL gerado a partir dele. Escrita
  direta no banco, ou pelo model/repository sem o Service, ainda grava `NULL`.
- Uma linha com `NULL` é lida pelo ORM como `None`, apesar de o tipo do model
  ser `datetime`/`timedelta`.

## SQL a executar

### 1. Conferir se há linhas com `NULL`

Os dois resultados precisam ser 0.

```sql
SELECT count(*) FILTER (WHERE finished_at IS NULL)  AS sem_fim,
       count(*) FILTER (WHERE elapsed_time IS NULL) AS sem_duracao
FROM public.maintenance;
```

Se houver linhas, pare e decida o que fazer com cada uma. O fim real precisa ser
informado; não preencha com um valor inventado. Ao preencher `finished_at`, o
banco recalcula `elapsed_time`, que é uma coluna gerada.

### 2. Aplicar as restrições

Se alguma linha ainda tiver `NULL`, o comando falha e nada é alterado.

```sql
BEGIN;

ALTER TABLE public.maintenance
    ALTER COLUMN finished_at SET NOT NULL,
    ALTER COLUMN elapsed_time SET NOT NULL;

COMMIT;
```

O `ALTER TABLE` bloqueia a tabela enquanto verifica as linhas existentes.

### 3. Conferir o resultado

As duas linhas devem mostrar `is_nullable = NO`.

```sql
SELECT column_name, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'maintenance'
  AND column_name IN ('finished_at', 'elapsed_time');
```

### Desfazer, se necessário

```sql
ALTER TABLE public.maintenance
    ALTER COLUMN finished_at DROP NOT NULL,
    ALTER COLUMN elapsed_time DROP NOT NULL;
```

## O que não precisa mudar

O `CHECK ck_maintenance_finished_after_started`
(`finished_at IS NULL OR finished_at >= started_at`) continua correto. Com
`NOT NULL`, a parte `IS NULL` fica redundante, mas inofensiva.

## Depois de executar

- [ ] Remover do `MaintenanceModel` a nota de divergência temporária.
- [ ] Atualizar o `CLAUDE.md` (seções 1, 4.2, 4.4, 6.2, 6.3 e 9).
- [ ] Atualizar `docs/DER-maintenance-software.dot`, que ainda descreve
      `finished_at` como "nulo = em andamento", e gerar a imagem de novo.
- [ ] Encerrar esta pendência.
