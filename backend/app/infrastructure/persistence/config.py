import os
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

# Classe connection é responsável por todas as funções relacionadas a conexão com banco de dados
# Desde o carregamento das variavéis de ambiente do banco até a criação do esquema ORM com SQLALCHEMY 
class Config:
    """Carrega as credenciais PostgreSQL e oferece conexão direta via psycopg2."""
    
    # Carrega as variavéis de ambiente relacionadas ao banco de dados do arquivo .env
    @staticmethod
    def load_envar():
        """Carrega o `.env` vizinho e retorna as cinco variáveis de acesso ao banco.

        Chaves ausentes são retornadas com valor `None`; este método não valida
        as credenciais nem abre uma conexão.
        """
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
        """Abre uma conexão psycopg2 e a devolve ao chamador.

        Em caso de sucesso, imprime uma mensagem e retorna a conexão aberta,
        que o chamador deve fechar. Se `psycopg2.connect()` falhar, imprime
        uma mensagem genérica e retorna `None`.
        """
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

