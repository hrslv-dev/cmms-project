"""Experimento manual de conexões e pool PostgreSQL, não é um teste automatizado.

Importar ou executar este arquivo cria uma engine, abre e fecha duas conexões,
abre uma terceira conexão que permanece aberta (`con3`) e imprime o estado do
pool. Requer PostgreSQL configurado e disponível; não importe em produção.
"""

from backend.app.infrastructure.persistence.engine import Engine_factory

engine = Engine_factory.create_db_engine()

# Mostra qual implementação de pool o SQLAlchemy selecionou para PostgreSQL.
print(engine.pool)


# Abre e fecha duas conexões para observar a reutilização de conexões pelo pool.
con1 = engine.connect()
con1.close()
con2 = engine.connect()
con2.close()

# Abre uma terceira conexão e a mantém aberta intencionalmente neste rascunho.
con3 = engine.connect()



print(engine.pool.status())
# con = engine.connect()

# print(con.connection.dbapi_connection)
