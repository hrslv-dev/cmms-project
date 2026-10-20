from sqlalchemy import text
from backend.app.domain.maquina import Maquina
from backend.app.infrastructure.persistence.engine import Engine_factory

engine = Engine_factory.create_db_engine()
with engine.connect() as connection: 
    with connection.begin(): 
        # Com begin eu garanto atomicidade as minhas transações 
        result = connection.execute(text("SELECT 1 ")).scalar_one()
        print(f"Connection OK({result})")


    
    
    
    
    
    command1 = text("SELECT id, nome FROM maquinas;")  
    command2 = text("INSERT INTO maquinas (nome) VALUES('Multiforca');")
  
    insert =  connection.execute(command2)
    connection.commit()
       
    search = connection.execute(command1)
    
    print(search.fetchall())     