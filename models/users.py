from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, func
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="User")

class Commands(Base):
    __tablename__ =  "commands"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    command = Column(String)
    result = Column(String)
    error = Column(String)
    status = Column(String)  #success/error/timeout
    returncode = Column(Integer)
    usetime = Column(DateTime, default=func.now())

class Server(Base):
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    host = Column(String)
    port = Column(Integer, default=22)
    encrypted_password = Column(String)
    username = Column(String)
    auth_type = Column(String, default="password")  # "password" или "key"
    status = Column(String, default="offline")  # online/offline
    last_seen = Column(DateTime)
    cpu = Column(Float)
    ram = Column(Float)
    disk = Column(Float)

