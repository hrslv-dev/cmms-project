-- Passo 1: cria o banco de testes vazio.
-- Conecte-se ao banco "postgres" com o mesmo usuário dono do banco cmms.
-- Execute sozinho: CREATE DATABASE não pode rodar dentro de uma transação.
-- Se cmms_test já existir, o comando falha e nada é alterado.

CREATE DATABASE cmms_test
    WITH TEMPLATE   = template0
         ENCODING   = 'UTF8'
         LC_COLLATE = 'pt_BR.UTF-8'
         LC_CTYPE   = 'pt_BR.UTF-8'
         TABLESPACE = pg_default;
