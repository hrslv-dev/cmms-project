import os 
import psycopg2
from dotenv import load_dotenv

# Carrega as variavéis do arquivo .env para o ambiente de processo python 
load_dotenv()

# Define as variaveis de ambiente para o mundo python 
DB_HOST= os.getenv('DB_HOST')  
DB_PORT= os.getenv('DB_PORT')
DB_NAME= os.getenv('DB_NAME')
DB_USER= os.getenv('DB_USER')
DB_PASSWORD= os.getenv('DB_PASSWORD')


try: 
    connection = psycopg2.connect(
        host = DB_HOST, 
        port = DB_PORT, 
        database = DB_NAME, 
        user = DB_USER, 
        password = DB_PASSWORD
    ) 
    print("Conexão estabelecida com sucesso") 

    cursor = connection.cursor()
    cursor.execute("SELECT version();")
    db_version = cursor.fetchone()
    print(f"Versão do banco de dados : {db_version[0]}")

    cursor.close()
    connection.close()

except Exception as error: 
    print(f"Erro ao conectar ao banco")

