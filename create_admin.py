# create_admin.py
from app.database import SessionLocal
from back.auth import create_user

db = SessionLocal()
try:
    user = create_user(db, username="admin", password="admin123", role="admin")
    print(f"Администратор создан: {user.username} (role={user.role})")
except Exception as e:
    print("Ошибка:", e)
finally:
    db.close()