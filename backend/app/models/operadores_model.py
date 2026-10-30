from sqlalchemy import String, Integer


from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.base.base_model import Base

class OperadorModel(Base): 
    __tablename__ = 'operadores'
    
    id: Mapped[int] = mapped_column(
        Integer, nullable=False, primary_key=True
    )
    
    nome:Mapped[String] = mapped_column(
        String(100), nullable=False 
    )