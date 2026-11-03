from app.infrastructure.conf.session import SessionLocal
from sqlalchemy import text

def main(): 
    with SessionLocal() as session: 
        
        resultado = session.execute(
            text("SELECT 1")
        )
        
        print("Conexão:", resultado.scalar())
            
if __name__ == "__main__": 
    main() 