# app/services/init_db.py
from .db import ENGINE, Base

def create_all_tables():
    Base.metadata.create_all(bind=ENGINE)
