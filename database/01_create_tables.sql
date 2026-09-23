-- Cria uma tabela chamada maquinas, (tabela, dados estruturados etc)
CREATE TABLE maquinas (
    id INTEGER GENERATED ALWAYS AS IDENTITY,
    nome VARCHAR(100) NOT NULL,

    CONSTRAINT pk_maquinas PRIMARY KEY (id)
);

CREATE TABLE componentes (
    id INTEGER GENERATED ALWAYS AS IDENTITY,
    nome VARCHAR(100) NOT NULL,
    maquina_id INTEGER NOT NULL,

    CONSTRAINT pk_componentes PRIMARY KEY (id),
    CONSTRAINT fk_componentes_maquina
        FOREIGN KEY (maquina_id)
        REFERENCES maquinas (id)
);

CREATE TABLE tecnicos (
    id INTEGER GENERATED ALWAYS AS IDENTITY,
    nome VARCHAR(100) NOT NULL,
    funcao VARCHAR(20) NOT NULL,

    CONSTRAINT pk_tecnicos PRIMARY KEY (id),
    CONSTRAINT chk_tecnicos_funcao
        CHECK (funcao IN ('Eletricista', 'Mecânico'))
);

CREATE TABLE operadores (
    id INTEGER GENERATED ALWAYS AS IDENTITY,
    nome VARCHAR(100) NOT NULL,

    CONSTRAINT pk_operadores PRIMARY KEY (id)
);

CREATE TABLE historico_manutencao (
    id INTEGER GENERATED ALWAYS AS IDENTITY,
    maquina_id INTEGER NOT NULL,
    tecnico_id INTEGER NOT NULL,
    componente_id INTEGER NOT NULL,
    operador_id INTEGER NOT NULL,
    tipo VARCHAR(20) NOT NULL,
    problema TEXT,
    servico VARCHAR(20) NOT NULL,
    descricao TEXT,
    data_manutencao DATE NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fim TIME,

    tempo_manutencao INTERVAL
        GENERATED ALWAYS AS (hora_fim - hora_inicio) STORED,

    CONSTRAINT pk_historico_manutencao PRIMARY KEY (id),

    CONSTRAINT fk_historico_maquina
        FOREIGN KEY (maquina_id)
        REFERENCES maquinas (id),

    CONSTRAINT fk_historico_tecnico
        FOREIGN KEY (tecnico_id)
        REFERENCES tecnicos (id),

    CONSTRAINT fk_historico_componente
        FOREIGN KEY (componente_id)
        REFERENCES componentes (id),

    CONSTRAINT fk_historico_operador
        FOREIGN KEY (operador_id)
        REFERENCES operadores (id),

    CONSTRAINT chk_historico_tipo
        CHECK (tipo IN ('Corretiva', 'Preventiva')),

    CONSTRAINT chk_historico_servico
        CHECK (
            servico IN (
                'Inspeção',
                'Limpeza',
                'Ajuste',
                'Lubrificação',
                'Substituição',
                'Reparo',
                'Instalação',
                'Configuração',
                'Calibração',
                'Modificação'
            )
        ),

    CONSTRAINT chk_historico_horario
        CHECK (hora_fim IS NULL OR hora_inicio < hora_fim)
);