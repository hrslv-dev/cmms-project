from app.infrastructure.conf.session import SessionLocal
# Importar os models relacionados registra suas classes na mesma Base antes de
# o SQLAlchemy configurar os mappers de MaquinasModel.
from app.models import componentes_model, manutencoes_model, operadores_model, tecnico_model
from app.models.maquinas_model import MaquinasModel
from app.repository.maquina_repository import MaquinaRepository

def main(): 
    with SessionLocal() as session: 
        
        maquina_repo = MaquinaRepository(session)
        
        new_machine = MaquinasModel(
            nome = "Multiforca", 
            componentes = []
        )
        maquina_repo.add(new_machine)
        
        session.commit()
        
        print("Máquina Adicionada!")
        
        query = maquina_repo.list_all() 
        
        for maquina in query: 
            print(maquina.id, maquina.componentes,maquina.nome)       
        
            
if __name__ == "__main__": 
    main() 
