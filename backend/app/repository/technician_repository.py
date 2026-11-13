import sqlalchemy as sq
import sqlalchemy.orm as orm

from app.models.tecnico_model import TecnicoModel
from app.infrastructure.base.base_repository import GenericRepository

class TecnicoRepository(GenericRepository): 
    
    def __init__(self, session:orm.Session):
        super().__init__(session,TecnicoModel)
    