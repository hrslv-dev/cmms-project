from sqlalchemy import select
from sqlalchemy.orm import Session  

from app.models.tecnico_model import TecnicoModel
from app.infrastructure.base.base_repository import GenericRepository

class TecnicoRepository(GenericRepository): 
    
    def __init__(self, session:Session):
        super().__init__(session,TecnicoModel)
    