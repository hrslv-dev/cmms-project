from sqlalchemy import select 
from sqlalchemy.orm import Session 

class BaseRepository(): 
    def __init__(self, session: Session ):
        self.session = session 
        
    def create()