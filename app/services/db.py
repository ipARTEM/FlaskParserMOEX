# app/services/db.py
"""
Инициализация движка и Session для SQLite.
Включаем:
- check_same_thread=False — чтобы ORM не ругалась при работе из Flask-потоков,
- timeout и WAL — чтобы реже ловить 'database is locked'.
"""

from __future__ import annotations
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session, DeclarativeBase

# Файл БД храним в корне репо
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "flaskparsermoex.sqlite3")
DEFAULT_DB_URL = f"sqlite:///{os.path.abspath(DEFAULT_DB_PATH)}"


class Base(DeclarativeBase):
    """Базовый класс для всех ORM-моделей."""


def make_engine(db_url: str | None = None):
    url = db_url or os.environ.get("FLASK_DB_URL", DEFAULT_DB_URL)
    engine = create_engine(
        url,
        echo=False,
        connect_args={
            "check_same_thread": False,  # важно для Flask
            "timeout": 15,               # ждём освобождения файла
        },
        pool_pre_ping=True,
    )

    # Переходим на WAL для лучшей конкурентности
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL;")
        cur.execute("PRAGMA synchronous=NORMAL;")
        cur.close()

    return engine


ENGINE = make_engine()
# scoped_session — безопасен для многопоточности Flask
SessionLocal = scoped_session(sessionmaker(bind=ENGINE, autoflush=False, autocommit=False))
