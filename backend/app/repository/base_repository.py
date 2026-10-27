from sqlalchemy import select 
from sqlalchemy.orm import Session 

from typing import Generic, TypeVar

from app.infrastructure.base.base_model import Base


"""Tipo genérico que é limitado as classes que herdam de Base"""

ModelType = TypeVar("ModelType", bound=Base)

class GenericRepository(Generic[ModelType]): 
    def __init__(self, session: Session, model:type[ModelType]):
        self.session = session 
        self.model = model
        
    def list_all(self) -> list[ModelType]: 
        stmt = select(self.model)
        return list(self.session.scalars(stmt).all())
        