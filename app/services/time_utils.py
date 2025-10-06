# app/services/time_utils.py
from __future__ import annotations
from datetime import datetime

def parse_iso_utc(s: str | None) -> datetime | None:
    """
    Ждём формат 'YYYY-MM-DD' или 'YYYY-MM-DD HH:MM' (UTC, без таймзоны).
    Возвращаем naive-UTC datetime или None.
    """
    if not s:
        return None
    s = s.strip().replace("T", " ")
    try:
        if len(s) == 10:           # YYYY-MM-DD
            return datetime.fromisoformat(s)
        return datetime.fromisoformat(s)  # YYYY-MM-DD HH:MM[:SS]
    except Exception:
        return None
