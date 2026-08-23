import sys
import os
from datetime import datetime

# Добавляем путь к проекту, чтобы импортировать модули
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from models.users import Commands  # или CommandLog, если ты переименовал

def show_commands(limit=20):
    db = SessionLocal()
    try:
        # Получаем последние записи, сортируем по убыванию времени
        records = db.query(Commands).order_by(Commands.usetime.desc()).limit(limit).all()
        
        if not records:
            print("Таблица пуста.")
            return
        
        print("\n=== Последние выполненные команды ===\n")
        for cmd in records:
            print(f"ID: {cmd.id}")
            print(f"Пользователь ID: {cmd.user_id}")
            print(f"Команда: {cmd.command}")
            print(f"Результат: {cmd.result or '(пусто)'}")
            print(f"Ошибка: {cmd.error or '(нет)'}")
            print(f"Статус: {cmd.status}")
            print(f"Время: {cmd.usetime}")
            print("-" * 50)
        print(f"Всего показано: {len(records)} записей")
    except Exception as e:
        print(f"Ошибка при чтении БД: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    show_commands()