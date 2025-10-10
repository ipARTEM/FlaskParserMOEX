# app/services/init_db.py
"""Создание всех таблиц в базе."""
from .db import ENGINE, Base

def create_all_tables() -> None:
    Base.metadata.create_all(bind=ENGINE)
