-- Dados FICTÍCIOS para usar a Tela 1 no cmms_test. Nomes inventados.
-- Duas travas: só roda no cmms_test e só se as tabelas de cadastro estiverem
-- vazias (evita duplicar). Tudo em uma transação.

BEGIN;

DO $$
BEGIN
    IF current_database() <> 'cmms_test' THEN
        RAISE EXCEPTION 'Banco errado: %. Conecte-se a cmms_test.', current_database();
    END IF;
    IF EXISTS (SELECT FROM public.machines)
       OR EXISTS (SELECT FROM public.subsets)
       OR EXISTS (SELECT FROM public.operators)
       OR EXISTS (SELECT FROM public.technical_functions)
       OR EXISTS (SELECT FROM public.technicians) THEN
        RAISE EXCEPTION 'Já há cadastros em cmms_test. Nada foi inserido.';
    END IF;
END
$$;

INSERT INTO public.machines (name) VALUES
    ('Nova Bloc'),
    ('Máquina 2'),
    ('Máquina sem subconjuntos');

-- O id é gerado pelo banco; por isso os vínculos são feitos pelo nome.
INSERT INTO public.subsets (name, machine_id)
SELECT s.name, m.id
FROM (VALUES
    ('Esteira de entrada', 'Nova Bloc'),
    ('Motor principal',    'Nova Bloc'),
    ('Painel elétrico',    'Nova Bloc'),
    ('Unidade hidráulica', 'Nova Bloc'),
    ('Misturador',         'Máquina 2'),
    ('Prensa',             'Máquina 2'),
    ('Painel elétrico',    'Máquina 2')
) AS s (name, machine_name)
JOIN public.machines AS m ON m.name = s.machine_name;

INSERT INTO public.technical_functions (name, active) VALUES
    ('Mecânico',          TRUE),
    ('Eletricista',       TRUE),
    ('Função desativada', FALSE);

INSERT INTO public.technicians (name, function_id)
SELECT t.name, f.id
FROM (VALUES
    ('Carlos Teste',  'Mecânico'),
    ('Beatriz Teste', 'Eletricista'),
    ('Álvaro Teste',  'Mecânico')
) AS t (name, function_name)
JOIN public.technical_functions AS f ON f.name = t.function_name;

INSERT INTO public.operators (name) VALUES
    ('Ana Teste'),
    ('João Teste');

COMMIT;

-- Esperado: 3 máquinas, 7 subconjuntos, 3 funções, 3 técnicos, 2 operadores.
SELECT (SELECT count(*) FROM public.machines)            AS maquinas,
       (SELECT count(*) FROM public.subsets)             AS subconjuntos,
       (SELECT count(*) FROM public.technical_functions) AS funcoes,
       (SELECT count(*) FROM public.technicians)         AS tecnicos,
       (SELECT count(*) FROM public.operators)           AS operadores;
