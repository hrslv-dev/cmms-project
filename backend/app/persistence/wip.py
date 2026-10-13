from sqlalchemy import create_engine
from connection import Connection
from engine import Engine 

url = Engine.generate_url()

# Pela URL o sqlaclhemy sabe qual dialeto conversar com o banco 
# Se for uma URL SQLite, ele sabe que é SQLite, se for postgres, 
# Ele sabe que é postgres 
engine = create_engine(url, echo=True)

con = engine.connect()

print(con.connection.dbapi_connection)