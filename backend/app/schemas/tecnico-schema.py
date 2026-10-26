from pydantic import BaseModel, Field 

class TecnicoCreate(BaseModel): 
    nome: str = Field(min_length=5, max_length=200)
    funcao: str = Field()
    
class TecnicoResponse(BaseModel): 
    id: int 
    nome: str 
    funcao: str 
    
    model_config = {"from_attributes": True}