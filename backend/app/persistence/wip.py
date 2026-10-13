from sqlalchemy import create_engine
from connection import Connection
from engine import Engine 
from sqlalchemy import QueuePool

url = Engine.generate_url()

# Pela URL o sqlaclhemy sabe qual dialeto conversar com o banco 
# Se for uma URL SQLite, ele sabe que é SQLite, se for postgres, 
# Ele sabe que é postgres 
engine = create_engine(url,  
                       # echo=True
                        pool_size= 10
                       )

print(engine.pool)


# Dessa forma é como se a engine estivesse reutilizando a mesma conexão do pool
con1 = engine.connect()
con1.close()
con2 = engine.connect()
con2.close()
con3 = engine.connect()
# Eu tenho uma conexão ativa aqui



print(engine.pool.status())
# con = engine.connect()

# print(con.connection.dbapi_connection)