from sqlalchemy import inspect, select, text 
from sqlalchemy.orm import Session 
from sqlalchemy import engine

from backend.app.domain.base import Base 
from backend.app.domain.maquina import Maquina
from backend.app.domain.componentes import Components
from backend.app.domain.manutencao import HistoricoManutencao
from backend.app.domain.operadores import Operador
from backend.app.domain.tecnicos import Tecnico
from backend.app.infrastructure.persistence.engine import Engine_factory

models = [ 
          Maquina, 
          Components, 
          Tecnico, 
          Operador, 
          HistoricoManutencao
          ]

engine = Engine_factory.create_db_engine()
try: 
    conexao = engine.connect()
    resultado = conexao.execute(text("SELECT 1")).scalar_one()
    print(f"Conexão OK, ({resultado})")
