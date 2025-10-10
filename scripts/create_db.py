# scripts/create_db.py
"""
Создаёт таблицы в файле flaskparsermoex.sqlite3
Запуск:  python -m scripts.create_db
"""
from app.services.init_db import create_all_tables

if __name__ == "__main__":
    create_all_tables()
    print("SQLite: таблицы созданы.")
