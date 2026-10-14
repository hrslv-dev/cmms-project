import os
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

# Classe connection é responsável por todas as funções relacionadas a conexão com banco de dados
# Desde o carregamento das variavéis de ambiente do banco até a criação do esquema ORM com SQLALCHEMY 
class Config: 
    
    # Carrega as variavéis de ambiente relacionadas ao banco de dados do arquivo .env
    @staticmethod
    def load_envar():
        load_dotenv(dotenv_path=Path(__file__).with_name(".env"))
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
        db_env = Config.load_envar()
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

