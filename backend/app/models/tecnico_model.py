from sqlalchemy import Base 
from sqlalchemy import String, Integer 
from sqlalchemy import CheckConstraint

from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.base.base_model import Base 

"""Model da entidade técnicos no banco de dados (dados persistidos no ambiente python)"""

class TecnicoModel(Base): 
    __tablename__ = "tecnicos"
    __table_args__ = (CheckConstraint(
        "funcao IN ('Eletricista', 'Mecânico')", 
        name = "ck_funcao_tecnico")) 

    
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )

    nome: Mapped[str] = mapped_column(
        String(50), nullable=False
    )

    funcao: Mapped[str] = mapped_column(
        String(50), nullable=False
    ) 
