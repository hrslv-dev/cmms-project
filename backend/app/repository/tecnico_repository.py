from sqlalchemy import select
from sqlalchemy.orm import Session  

from app.models.tecnico_model import TecnicoModel

class TecnicoRepository(): 
    
    def __init__(self, session:Session):
        self.session = session
    
    