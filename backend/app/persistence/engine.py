from connection import Connection
from sqlalchemy import create_engine
from sqlalchemy import QueuePool
from sqlalchemy.engine import URL 

class Engine: 

    def __init__(self):
        pass
        
    @staticmethod
    def generate_url(): 
        creds = Connection.load_envar()
        url = URL.create( 
            drivername="postgresql", 
            username=creds["DB_USER"], 
            password=creds["DB_PASSWORD"], 
            host=creds["DB_HOST"],
            port=int(creds["DB_PORT"]), 
            database=creds["DB_NAME"] 
        )
        return url 

    def engine_factory():
        url = Engine.generate_url
        engine = create_engine(
            # URL é o link correspondente ao banco de dados POSTGRES usando driver PYSCOPG2
            url,
            # Definição do Driver da engine SQLALCHEMY
            # PoolClass -> QueuePool  
            poolclass= QueuePool, 
            # Quantidade de pools
            pool_size=5, 
            # Quantidade máxima de conexões temporárias caso as 5 pools estiverem ocupadas
            max_overflow=10,
            # Confere se a conexão que está no pool ainda está viva. 
            pool_pre_ping=True, 
            # Boolean que confirma se deve se mostrar as querys SQL no console 
            echo=True) 
        
        return engine 