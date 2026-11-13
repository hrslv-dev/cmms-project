import sqlalchemy as sq
import sqlalchemy.orm as orm

from app.models.technician_model import TechnicianModel
from app.infrastructure.base.base_repository import GenericRepository

class TechnicianRepository(GenericRepository): 
    
    def __init__(self, session:orm.Session):
        super().__init__(session,TechnicianModel)
    
