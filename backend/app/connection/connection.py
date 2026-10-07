import os
import psycopg2
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker 

# Classe connection é responsável por todas as funções relacionadas a conexão com banco de dados
# Desde o carregamento das variavéis de ambiente do banco até a criação do esquema ORM com SQLALCHEMY 
class Connection:


    # Carrega as variavéis de ambiente relacionadas ao banco de dados do arquivo .env
    @staticmethod
    def load_envar():
        load_dotenv()
        return {
            "DB_HOST": os.getenv("DB_HOST"),
            "DB_PORT": os.getenv("DB_PORT"),
            "DB_NAME": os.getenv("DB_NAME"),
            "DB_USER": os.getenv("DB_USER"),
            "DB_PASSWORD": os.getenv("DB_PASSWORD"),
        }

    # Faz a conexão com o banco de dados
    @staticmethod
    def make_connection():
        db_env = Connection.load_envar()
        try:
            connection = psycopg2.connect(
                host=db_env["DB_HOST"],
                port=db_env["DB_PORT"],
                database=db_env["DB_NAME"],
                user=db_env["DB_USER"],
                password=db_env["DB_PASSWORD"],
            )
            print("Conexão estabelecida com sucesso")
            return connection
        
        except Exception:
            print("Erro ao tentar se conectar ao banco de dados")
            return None

    # Gera a url do banco de dados usando como driver o psycopg2 
    @staticmethod
    def get_database_url(): 
        creds = Connection.load_envar()
        url = ( 
            f"postgresql+psycopg2://"
            f"{creds['DB_USER']}:{creds['DB_PASSWORD']}"
            f"@{creds['DB_HOST']}:{creds['DB_PORT']}"
            f"/{creds['DB_NAME']}"
        )
        return url

    # Cria a engine do sqlalchemy
    def create_engine_sqlalchemy(): 
        url = Connection.get_database_url()
        # Sabe como chegar ao DB (pela url)
        engine = create_engine(
                    # URL é o link correspondente ao banco de dados POSTGRES usando driver PYSCOPG2
                    url,
                    # Definição do Driver da engine SQLALCHEMY 
                    poolclass=psycopg2.extensions.connection, 
                    # Quantidade de pools
                    pool_size=5, 
                    # Quantidade máxima de conexões temporárias caso as 5 pools estiverem ocupadas
                    max_overflow=10,
                    # Confere se a conexão que está no pool ainda está viva. 
                    pool_pre_ping=True, 
                    # Boolean que confirma se deve se mostrar as querys SQL no console 
                    echo=True) 
        return engine 


    # Session é quem realiza as operações ORM e 
    def create_session_factory(): 
        from sqlalchemy import sessionmaker 
        
        engine = Connection.create_engine_sqlalchemy()
        return sessionmaker(autocommit=False, autflush=False, bind=engine)

