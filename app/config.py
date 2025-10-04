import os

class Config:
    """
    Все основные настройки проекта:
    - Порт/DEBUG берутся в run.py
    - Кэш по умолчанию — простая память (для локальной разработки)
    - ADMIN_TOKEN — для защиты тяжёлых операций
    - Рыночные режимы/борды MOEX по умолчанию (совместимо с твоим проектом)
    """
    SECRET_KEY = os.environ.get("SECRET_KEY", "local-secret")
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 60  # сек, дефолтный TTL для кэша

    # Админ-токен для тяжёлых запросов (например, история по многим тикерам)
    ADMIN_TOKEN = os.environ.get("FLASK_ADMIN_TOKEN", "")

    # Настройки рынков: (TQBR — акции, RFUD — фьючерсы)
    MARKET_STOCK = {"engine": "stock", "market": "shares", "board": "TQBR"}
    MARKET_FUT = {"engine": "futures", "market": "forts", "board": "RFUD"}

    # Таймауты & ретраи для HTTP
    HTTP_TIMEOUT = 10
    HTTP_RETRIES = 2
