from sqlalchemy import inspect, select, text 
from sqlalchemy.orm import Session 
from sqlalchemy import engine

from backend.app.models.base import Base 
from backend.app.models.maquina import Maquina
from backend.app.models.componentes import Components
from backend.app.models.manutencao import HistoricoManutencao
from backend.app.models.operadores import Operador
from backend.app.models.tecnicos import Tecnico
from backend.app.infrastructure.persistence.engine import Engine_factory

"""Teste de integração SOMENTE LEITURA 
    Esse teste deve responder o seguinte: 
    - O python consegue abrir uma conexão com PostgreSQL? 
    - As tabelas descritas pelos modelos existem no banco? 
    - Cada entidade consegue executar uma consulta ORM nessa tabela? 
"""

models = [ 
          Maquina, 
          Components, 
          Tecnico, 
          Operador, 
          HistoricoManutencao
          ] 

engine = Engine_factory.create_db_engine()
try: 
    with engine.connect() as connection: 
        result =connection.execute(text("SELECT 1")).scalar_one()
        print(f"Conexão OK, ({result})")
    
    # Compara os modelos Python carregados com as tabelas do banco e dados: 
    modeled_tables = set(Base.metadata.tables)
    db_tables = set(inspect(engine).get_table_names(schema="public")) 
    
    missing =  modeled_tables - db_tables
    if missing: 
        print(f"Tabelas ausentes no PostgresSQL: {sorted(missing)}") 
    else: 
        print("Tabelas dos modelos encontradas com sucesso no PostgresSQL!")
        
    # Executa uma consulta ORM para cada entidade, sem gravar dados
    with Session(engine) as session: 
        for model in models: 
            session.scalars(select(model).limit(1)).first()
            print(f"Consulta ORM: OK - {model.__tablename__}")
finally: 
    engine.dispose()


