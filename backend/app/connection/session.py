from sqlalchemy import sessionmaker
from connection import Connection

class Session: 
         # Session é quem realiza as operações ORM e 
    def create_session_factory(): 
        from sqlalchemy import sessionmaker 
        
        engine = Connection.create_engine_sqlalchemy()
        return sessionmaker(autocommit=False, autoflush=False, bind=engine)


    def create_new_session(sessionmaker): 
        # Usada como dependência do FastAPI para criar uma sessão por requisição.
        session = sessionmaker()
        try:
            yield session
        finally:
            session.close()
