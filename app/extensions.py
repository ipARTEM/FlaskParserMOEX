from flask_caching import Cache

# Расширения храним отдельно, чтобы был единый доступ из разных модулей
cache = Cache()
