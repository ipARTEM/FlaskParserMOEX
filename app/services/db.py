# app/services/db.py
from __future__ import annotations
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, scoped_session
import os

# Файл БД можно хранить в корне проекта
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "flaskparsermoex.sqlite3")
DEFAULT_DB_URL = f"sqlite:///{os.path.abspath(DEFAULT_DB_PATH)}"

class Base(DeclarativeBase):
    """SQLAlchemy базовый класс для моделей."""

def make_engine(db_url: str | None = None):
    url = db_url or os.environ.get("FLASK_DB_URL", DEFAULT_DB_URL)
    engine = create_engine(
        url,
        echo=False,
        connect_args={"check_same_thread": False},  # важно для Flask/Thread
        pool_pre_ping=True,
    )
    return engine

# Глобальные фабрики:
ENGINE = make_engine()
SessionLocal = scoped_session(sessionmaker(bind=ENGINE, autoflush=False, autocommit=False))
