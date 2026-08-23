from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

from app.database import SessionLocal
from models.users import User, Commands


load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


############################################################################
############################################################################

#                          ХЕШИРОВАНИЕ И ПРОВЕРКА                          #

############################################################################
############################################################################

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


############################################################################
############################################################################

#                                    БД                                    #

############################################################################
############################################################################

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, username: str, password: str, role: str = "user"):
    hashed = get_password_hash(password)
    user = User(username=username, password_hash=hashed, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


############################################################################
############################################################################

#                               JWT TOKEN                                  #

############################################################################
############################################################################

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


############################################################################
############################################################################

#                           Получение сессии                               #

############################################################################
############################################################################

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


############################################################################
############################################################################

#                  Проверка токена и получение пользователя                #

############################################################################
############################################################################

security = HTTPBearer()

def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = get_user_by_username(db, username)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


############################################################################
############################################################################

#                  Получение информации о команде из бд                    #

############################################################################
############################################################################


def get_current_commands(
        db: Session, limit: int = 20
):
    result = (
        db.query(Commands, User.username)
        .join(User, Commands.user_id == User.id)
        .order_by(Commands.usetime.desc())
        .limit(limit)
        .all()
    )

    history = []
    for cmd, username in result:
        history.append({
            "command": cmd.command,
            "username": username,
            "usetime": cmd.usetime.isoformat() if cmd.usetime else None
        })

    return history