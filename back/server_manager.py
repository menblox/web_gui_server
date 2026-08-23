import asyncssh
import asyncio
from cryptography.fernet import Fernet
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Dict, Any, List
import os
import re

from models.users import Server
from schemas.validation import ServerCreate, ServerUpdate

MASTER_KEY = os.getenv("FERNET_KEY")
if not MASTER_KEY:
    raise ValueError("FERNET_KEY не задан в .env")
cipher = Fernet(MASTER_KEY)



# ----- Вспомогательные функции для шифрования -----
def encrypt_password(password: str) -> str:
    """Зашифровать пароль"""
    return cipher.encrypt(password.encode()).decode()

def decrypt_password(encrypted: str) -> str:
    """Расшифровать пароль"""
    return cipher.decrypt(encrypted.encode()).decode()



# ----- Функции для работы с БД -----
def get_server(db: Session, server_id: int) -> Optional[Server]:
    """Получить сервер по ID"""
    return db.query(Server).filter(Server.id == server_id).first()

def get_servers(db: Session) -> List[Server]:
    """Получить все серверы"""
    return db.query(Server).all()

def create_server(db: Session, server_data: ServerCreate) -> Server:
    """Создать новый сервер (сохранить в БД с зашифрованным паролем)"""
    encrypted = encrypt_password(server_data.password)
    db_server = Server(
        name=server_data.name,
        host=server_data.host,
        port=server_data.port,
        username=server_data.username,
        encrypted_password=encrypted,
        status="offline",
        last_seen=None,
        cpu=None,
        ram=None,
        disk=None
    )
    db.add(db_server)
    db.commit()
    db.refresh(db_server)
    return db_server

def update_server(db:Session, server_id: int, update_data: ServerUpdate) -> Optional[Server]:
    """Обновить данные сервера"""
    server = get_server(db, server_id)
    if not server:
        return None
    if update_data.name is not None:
        server.name = update_data.name
    if update_data.host is not None:
        server.host = update_data.host
    if update_data.port is not None:
        server.port = update_data.port
    if update_data.username is not None:
        server.username = update_data.username
    if update_data.password is not None:
        server.encrypted_password = encrypt_password(update_data.password)
    db.commit()
    db.refresh(server)
    return server

def delete_server(db: Session, server_id: int) -> bool:
    """Удалить сервер из БД"""
    server = get_server(db, server_id)
    if not server:
        return False
    db.delete(server)
    db.commit()
    return True



# ----- SSH-функции (асинхронные) -----
async def run_ssh_command(
        host: str,
        username: str,
        password: str,
        command: str,
        port: int = 22,
        timeout: int = 30
) -> Dict[str, Any]:
    """
    Выполнить команду на удалённом сервере по SSH
    Возвращает dict с ключами: stdout, stderr, exit_code
    """
    try:
        async with asyncssh.connect(
            host,
            port=port,
            username=username,
            password=password,
            known_hosts=None
        )as conn: 
            result = await asyncio.wait_for(
                conn.run(command, check=False),
                timeout=timeout
            )
            return{
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.exit_status
            }
    except asyncio.TimeoutError:
        return {"stdout": "", "stderr": "SSH connection timeout", "exit_code": -1}
    except asyncssh.Error as e:
        return {"stdout": "", "stderr": f"SSH error: {str(e)}", "exit_code": -1}
    except Exception as e:
        return {"stdout": "", "stderr": f"Unexpected error: {str(e)}", "exit_code": -1}


async def check_server_status(server: Server) -> bool:
    """
    Проверить доступность сервера (попытка SSH-подключения)
    """
    password = decrypt_password(server.encrypted_password)
    try:
        async with asyncssh.connect(
            server.host,
            port=server.port,
            username=server.username,
            password=password,
            known_hosts=None,
            connect_timeout=5
        ):
            return True
    except Exception:
        return False

async def collect_server_metrics(server: Server) -> Dict[str, Optional[float]]:
    """
    Собрать метрики с удалённого сервера (CPU, RAM, диск)
    Возвращает словарь с ключами: cpu, ram, disk (проценты)
    """
    password = decrypt_password(server.encrypted_password)
    commands = {
        "cpu": "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1",
        "ram": "free | grep Mem | awk '{printf \"%.2f\", $3/$2 * 100.0}'",
        "disk": "df -h / | awk 'NR==2 {print $5}' | sed 's/%//'"
    }
    metrics = {"cpu": None, "ram": None, "disk": None}
    for key, cmd in commands.items():
        result = await run_ssh_command(
            server.host,
            server.username,
            password,
            cmd,
            port=server.port,
            timeout=10
        )
        if result["exit_code"] == 0 and result["stdout"].strip():
            try:
                val = float(result["stdout"].strip())
                metrics[key] = val
            except ValueError:
                try:
                    val = float(result["stdout"].strip().replace(",", "."))
                    metrics[key] = val
                except ValueError:
                    metrics[key] = None
    return metrics



# ----- Основные публичные функции -----
async def add_new_server(db: Session, server_data: ServerCreate) -> Server:
    """
    Добавить новый сервер: сохранить в БД, проверить доступность, обновить статус и метрики
    """
    server = create_server(db, server_data)
    is_online = await check_server_status(server)
    server.status = "online" if is_online else "ofline"
    server.last_seen = datetime.utcnow()
    if is_online:
        metrics = await collect_server_metrics(server)
        server.cpu = metrics.get("cpu")
        server.ram = metrics.get("ram")
        server.disk = metrics.get("disk")
    db.commit()
    db.refresh(server)
    return server

async def update_server_data(db: Session, server_id: int, update_data: ServerUpdate) -> Optional[Server]:
    """
    Обновить данные сервера и перепроверить статус
    """
    server = update_server(db, server_id, update_data)
    if not server:
        return None
    is_online = await check_server_status(server)
    server.status = "online" if is_online else "offline"
    server.last_seen = datetime.utcnow()
    if is_online:
        metrics = await collect_server_metrics(server)
        server.cpu = metrics.get("cpu")
        server.ram = metrics.get("ram")
        server.disk = metrics.get("disk")
    db.commit()
    db.refresh(server)
    return server

async def execute_on_server(db: Session, server_id: int, command: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Выполнить команду на сервере по SSH и вернуть результат
    """
    server = get_server(db, server_id)
    if not server:
        raise ValueError("Сервер не найден")
    password = decrypt_password(server.encrypted_password)
    result = await run_ssh_command(
        server.host,
        server.username,
        password,
        command,
        port=server.port,
        timeout=timeout
    )
    server.last_seen = datetime.utcnow()
    if result["exit_code"] == 0:
        server.status = "online"
    else:
        if "SSH" in result["stderr"] or "timeout" in result["stderr"].lower():
            server.status = "ofline"
    db.commit()
    return result

async def refresh_server_metrics(db: Session, server_id: int) -> Optional[Server]:
    """
    Обновить метрики для одного сервера
    """
    server = get_server(db, server_id)
    if not server:
        return None
    is_online = await check_server_status(server)
    server.status = "online" if is_online else "offline"
    server.last_seen = datetime.utcnow()
    if is_online:
        metrics = await collect_server_metrics(server)
        server.cpu = metrics.get("cpu")
        server.ram = metrics.get("ram")
        server.disk = metrics.get("disk")
    else:
        server.cpu = None
        server.ram = None
        server.disk = None
    db.commit()
    db.refresh(server)
    return server

async def refresh_all_servers(db: Session):
    """
    Обновить метрики и статусы всех серверов (для фоновой задачи)
    """
    servers = get_servers(db)
    for server in servers:
        await refresh_server_metrics(db, server.id)