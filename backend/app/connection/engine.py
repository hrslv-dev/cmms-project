from connection import Connection
from sqlalchemy import create_engine
import psycopg2
import sqlalchemy

class Engine: 
    
    @staticmethod
    def create_engine_sqlalchemy(): 
        url = Connection.get_database_url()
        engine = create_engine(
            # URL é o link correspondente ao banco de dados POSTGRES usando driver PYSCOPG2
            url,
            # Definição do Driver da engine SQLALCHEMY
            # PoolClass -> QueuePool  
            poolclass=, 
            # Quantidade de pools
            pool_size=5, 
            # Quantidade máxima de conexões temporárias caso as 5 pools estiverem ocupadas
            max_overflow=10,
            # Confere se a conexão que está no pool ainda está viva. 
            pool_pre_ping=True, 
            # Boolean que confirma se deve se mostrar as querys SQL no console 
            echo=True) 
        return engine 