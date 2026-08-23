from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
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
    