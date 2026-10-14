from backend.app.infrastructure.persistence.engine import Engine_factory

engine = Engine_factory.create_db_engine()

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
