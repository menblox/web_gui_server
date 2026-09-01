import asyncio

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from datetime import datetime

from app.database import engine
from models.users import Base, User, Commands
from schemas.validation import ServerCommand, ServerCreate, ServerResponse, ServerUpdate, UserLogin, Token

from back.auth import get_user_by_username, verify_password, create_access_token, get_current_user, get_db, get_current_commands
from back.server_manager import add_new_server, delete_server, execute_on_server, get_server, get_servers, refresh_all_servers, refresh_server_metrics, update_server_data

Base.metadata.create_all(bind=engine)

app = FastAPI()


##################################################################
#                           Логин                                #
##################################################################

@app.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = get_user_by_username(db, user_data.username)
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": token, "token_type": "bearer"}


##################################################################
#                       post запросы                             #
##################################################################

@app.post("/api/servers", response_model=ServerResponse)
async def create_server_endpoint(
    server_data: ServerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещён")
    server = await add_new_server(db, server_data)
    return server

@app.delete("/api/servers/{server_id}")
async def delete_server_endpoint(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Доступ запрещён")
    if not delete_server(db, server_id):
        raise HTTPException(404, "Сервер не найден")
    return {"message": "Сервер удалён"}

@app.post("/api/servers/{server_id}/exec")
async def exec_on_server_commands(
    server_id: int,
    cmd_data: ServerCommand,
    db: Session = Depends(get_db),
):
    result = await execute_on_server(db, server_id, cmd_data.command, cmd_data.timeout)
    return result

@app.post("/api/servers/{server_id}/refresh")
async def api_metrics(server_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "user"]:
            raise HTTPException(status_code=403, detail="Доступ запрещён")
    update_server = await refresh_server_metrics(db, server_id)
    if not update_server:
        raise HTTPException(status_code=404, detail="Сервер не найден")
    return update_server
##################################################################
#                       get запросы                              #
##################################################################

class GET_HTML():

    _path_in_project = "web/templates/"

    def __init__(self, path_html):
        self.path_html = path_html

    def open_page(self):
        with open(self._path_in_project + self.path_html, "r", encoding="utf-8") as f:
            return f.read()


@app.get("/login", response_class=HTMLResponse)
def login_page():
    return GET_HTML("login.html").open_page()


@app.get("/home/profile/", response_class=HTMLResponse)
def profile_page():
    return GET_HTML("profile.html").open_page()

@app.get("/api/profile/")
async def api_profile(current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "user"]:
        raise HTTPException(status_code=403, detail="Доступ запрещён")
    return {"username": current_user.username, "role": current_user.role}


@app.get("/api/server/commands/")
async def api_server_commands(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещён")
    return get_current_commands(db, limit=20)


@app.get("/home/servers/", response_class=HTMLResponse)
def servers_page():
    return GET_HTML("servers.html").open_page()

@app.get("/api/servers")
async def api_metrics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "user"]:
            raise HTTPException(status_code=403, detail="Доступ запрещён")
    servers = get_servers(db)
    return servers

@app.get("/api/servers/{server_id}")
async def update_server_get(server_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = get_server(db, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Сервер не найден")
    return server

@app.patch("/api/servers/{server_id}")
async def update_server(
    server_id: int,
    update_data: ServerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    update = await update_server_data(db, server_id, update_data)
    if not update:
        raise HTTPException(status_code=404, detail="Сервер не найден")
    return update

@app.get("/home/servers/{server_id}/exec", response_class=HTMLResponse)
def server_id_exec():
    return GET_HTML("server_id_exec.html").open_page()

@app.get("/home/servers/{server_id}/update", response_class=HTMLResponse)
def server_id_update():
    return GET_HTML("server_id_update.html").open_page()