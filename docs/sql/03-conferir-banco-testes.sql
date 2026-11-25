-- Passo 3: só leitura. Execute em cmms e em cmms_test.
-- Os dois resultados devem ser iguais, inclusive "impressao_digital".
-- A ordem das colunas é relativa (row_number): colunas já removidas do cmms
-- deixam lacunas em ordinal_position, sem efeito na estrutura.

WITH estrutura AS (
    SELECT 'coluna' AS tipo,
           concat_ws('|', table_name,
                     row_number() OVER (PARTITION BY table_name ORDER BY ordinal_position),
                     column_name, data_type,
                     character_maximum_length, is_nullable, column_default,
                     is_identity, identity_generation, generation_expression) AS item
    FROM information_schema.columns
    WHERE table_schema = 'public'
    UNION ALL
    SELECT 'constraint',
           concat_ws('|', conrelid::regclass, conname, pg_get_constraintdef(oid))
    FROM pg_constraint
    WHERE connamespace = 'public'::regnamespace
    UNION ALL
    SELECT 'indice', indexdef FROM pg_indexes WHERE schemaname = 'public'
)
SELECT count(*) FILTER (WHERE tipo = 'coluna')     AS colunas,
       count(*) FILTER (WHERE tipo = 'constraint') AS constraints,
       count(*) FILTER (WHERE tipo = 'indice')     AS indices,
       md5(string_agg(tipo || item, E'\n' ORDER BY (tipo || item) COLLATE "C"))
           AS impressao_digital
FROM estrutura;
