-- Também usado pela suíte pytest (backend/tests/conftest.py).
-- Passo 2: cria as sete tabelas, idênticas às do banco cmms em 25/11/2026.
-- Conecte-se ao banco "cmms_test". Em qualquer outro banco, a trava abaixo
-- interrompe a execução. Tudo roda em uma transação: se algo falhar, nada fica.

BEGIN;

DO $$
BEGIN
    IF current_database() <> 'cmms_test' THEN
        RAISE EXCEPTION 'Banco errado: %. Conecte-se a cmms_test.', current_database();
    END IF;
END
$$;

CREATE TABLE public.machines (
    id   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE public.operators (
    id   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE public.technical_functions (
    id     INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name   VARCHAR(50) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT technical_functions_name_key UNIQUE (name),
    CONSTRAINT ck_function_name CHECK (LENGTH(BTRIM(name)) > 0)
);

CREATE TABLE public.technicians (
    id          INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    function_id INTEGER NOT NULL,
    CONSTRAINT fk_technical_function FOREIGN KEY (function_id)
        REFERENCES public.technical_functions (id) ON DELETE RESTRICT
);

CREATE TABLE public.subsets (
    id         INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    machine_id INTEGER NOT NULL,
    CONSTRAINT fk_subsets_machines FOREIGN KEY (machine_id)
        REFERENCES public.machines (id)
);

-- finished_at e elapsed_time aceitam NULL, como no cmms hoje
-- (ver docs/pendencia-alinhamento-banco.md).
CREATE TABLE public.maintenance (
    id            INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    operator_id   INTEGER,
    technician_id INTEGER NOT NULL,
    machine_id    INTEGER NOT NULL,
    service       VARCHAR(20) NOT NULL,
    problem       TEXT,
    type          VARCHAR(20) NOT NULL,
    description   TEXT,
    started_at    TIMESTAMPTZ NOT NULL,
    finished_at   TIMESTAMPTZ,
    elapsed_time  INTERVAL GENERATED ALWAYS AS (finished_at - started_at) STORED,
    CONSTRAINT fk_maintenance_operator FOREIGN KEY (operator_id)
        REFERENCES public.operators (id),
    CONSTRAINT fk_maintenance_technician FOREIGN KEY (technician_id)
        REFERENCES public.technicians (id),
    CONSTRAINT fk_maintenance_machine FOREIGN KEY (machine_id)
        REFERENCES public.machines (id),
    CONSTRAINT ck_maintenance_type CHECK (type IN ('Corretiva', 'Preventiva')),
    CONSTRAINT ck_maintenance_service CHECK (service IN (
        'Inspeção', 'Lubrificação', 'Substituição', 'Ajuste', 'Limpeza',
        'Reparo', 'Instalação', 'Configuração', 'Calibração', 'Modificação'
    )),
    CONSTRAINT ck_maintenance_problem_corrective
        CHECK (type <> 'Corretiva' OR problem IS NOT NULL),
    CONSTRAINT ck_maintenance_finished_after_started
        CHECK (finished_at IS NULL OR finished_at >= started_at)
);

CREATE TABLE public.subsets_maintenance (
    id             INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    subset_id      INTEGER NOT NULL,
    maintenance_id INTEGER NOT NULL,
    CONSTRAINT fk_assoc_subsets FOREIGN KEY (subset_id)
        REFERENCES public.subsets (id),
    CONSTRAINT fk_assoc_maintenance FOREIGN KEY (maintenance_id)
        REFERENCES public.maintenance (id),
    CONSTRAINT uq_maintenance_subset UNIQUE (maintenance_id, subset_id)
);

CREATE INDEX idx_subsets_machine ON public.subsets (machine_id);
CREATE INDEX idx_maintenance_operator ON public.maintenance (operator_id);
CREATE INDEX idx_maintenance_technician ON public.maintenance (technician_id);
CREATE INDEX idx_maintenance_machine ON public.maintenance (machine_id);
CREATE INDEX idx_subsets_maintenance_subset ON public.subsets_maintenance (subset_id);
CREATE INDEX idx_technicians_function ON public.technicians (function_id);

COMMIT;
