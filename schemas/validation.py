from pydantic import BaseModel

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str


class CommandResponse(BaseModel):
    username: str
    role: str
    command: str
    result: str
    error: str
    returncode: int
    
class CommandPost(BaseModel):
    command: str

