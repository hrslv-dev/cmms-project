import os 
from dotenv import load_dotenv 

load_dotenv()

# Configuração da conexão com o banco de dados  

class Settings: 
    DATABASE_URL = os.getenv(
        "DATABASE_URL", "postgresql:://postgres:15092006@localhost:5432/cmms" 
    )
    SQLALCHEMY_ECHO = os.getenv("SQLALCHEMY_ECHO", False)