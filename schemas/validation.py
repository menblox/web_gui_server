from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str



class ServerBase(BaseModel):
    name: str = Field(..., description="Название сервера")
    host: str = Field(..., description="IP-адрес или домен")
    port: int = Field(22, description="SSH-порт")
    username: str = Field(..., description="Имя пользователя для SSH")

class ServerResponse(ServerBase):
    id: int
    status: str = Field("offline", description="online/offline")
    cpu: Optional[float] = None
    ram: Optional[float] = None
    disk: Optional[float] = None
    last_seen: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ServerCreate(ServerBase):
    password: str = Field(..., description="Пароль для SSH-подключения")

class ServerUpdate(BaseModel):
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None

class ServerCommand(BaseModel):
    command: str = Field(..., description="Команда для выполнения")
    timeout: int = Field(30, description="Таймаут в секундах")


class ServerCommandResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
    server_id: int
    command: str
    executed_at: datetime