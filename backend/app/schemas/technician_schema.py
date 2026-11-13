from pydantic import BaseModel, Field 

class TechnicianCreate(BaseModel): 
    name: str = Field(min_length=5, max_length=200)
    function: str = Field()
    
class TechnicianResponse(BaseModel): 
    id: int 
    name: str 
    function: str 
    
    model_config = {"from_attributes": True}