# scripts/create_db.py  (новый файл)
from app.services.init_db import create_all_tables

if __name__ == "__main__":
    create_all_tables()
    print("SQLite: таблицы созданы.")
