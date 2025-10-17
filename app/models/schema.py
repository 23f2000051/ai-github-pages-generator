from pydantic import BaseModel , HttpUrl , Field
from typing import List , Optional

class Attachment(BaseModel):
    name:str
    url:str

class TaskRequest(BaseModel):
    email:str
    secret:Optional[str]
    task:str
    round:int
    nonce:str
    brief:str
    checks:List[str]
    evaluation_url:HttpUrl
    attachments:Optional[List[Attachment]]=Field(default_factory=list)



