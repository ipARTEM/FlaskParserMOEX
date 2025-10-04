from flask import Blueprint, render_template, request, jsonify, abort, current_app
from ...extensions import cache
from ...services.moex_client import MoexClient
from ...services.heatmap_service import HeatmapService
from ...services.search_service import SearchService

bp = Blueprint("market", __name__, template_folder="../../templates")

# Инициализируем сервисы (в ООП-стиле как singletons для блюпринта)
_client = MoexClient(timeout=current_app.config.get("HTTP_TIMEOUT", 10),
                     retries=current_app.config.get("HTTP_RETRIES", 2))
_heatmap = HeatmapService()
_search = SearchService()

def _cache_key(engine: str, market: str, board: str) -> str:
    return f"board:{engine}:{market}:{board}"

def _get_tiles(engine: str, market: str, board: str, fresh: bool = False):
    """
    Возвращает список плиток (теплокарта) с кэшированием.
    fresh=True — форс-обновление (для админа или по кнопке).
    """
    key = _cache_key(engine, market, board)
    if not fresh:
        cached = cache.get(key)
        if cached is not None:
            return cached

    data = _client.get_board_data(engine, market, board)
    tiles = _heatmap.compute_tiles(data["rows"])
    cache.set(key, tiles, timeout=60)  # TTL 60 сек по умолчанию
    return tiles

@bp.get("/parser")
def parser_page():
    """
    Рендерит теплокарты TQBR и RFUD на одной странице.
    Параметр ?mode=fast|fresh:
      - fast (по умолчанию): берём кэш
      - fresh: форс-обновление (если есть admin_token или локально)
    """
    mode = request.args.get("mode", "fast")
    fresh = (mode == "fresh")

    # Проверка админ-токена для fresh (защищаем тяжёлые запросы)
    if fresh:
        token = request.args.get("admin_token", "")
        if token != current_app.config.get("ADMIN_TOKEN", ""):
            # Разрешим fresh и без токена в локалке, если токен не задан
            if current_app.config.get("ADMIN_TOKEN"):
                abort(403, description="Admin token required for fresh mode")

    st = current_app.config["MARKET_STOCK"]  # TQBR
    ft = current_app.config["MARKET_FUT"]    # RFUD

    stock_tiles = _get_tiles(st["engine"], st["market"], st["board"], fresh=fresh)
    fut_tiles   = _get_tiles(ft["engine"], ft["market"], ft["board"], fresh=fresh)

    return render_template(
        "parser.html",
        page_title="Теплокарты MOEX",
        stock_tiles=stock_tiles,
        fut_tiles=fut_tiles,
        mode=mode
    )

@bp.get("/search")
def search_form():
    """
    Простая форма поиска по тикеру/названию.
    Выполняется на этой же странице, результат внизу.
    """
    return render_template("search.html", page_title="Поиск бумаг")

@bp.post("/search")
def search_post():
    """
    Обрабатываем форму. Источник данных — текущие плитки TQBR/RFUD
    (чтобы поиск был мгновенный). При желании можно сделать отдельный
    запрос к /securities.json для полноты.
    """
    query = request.form.get("query", "")

    st = current_app.config["MARKET_STOCK"]
    ft = current_app.config["MARKET_FUT"]
    tiles = []
    tiles += _get_tiles(st["engine"], st["market"], st["board"], fresh=False)
    tiles += _get_tiles(ft["engine"], ft["market"], ft["board"], fresh=False)

    results = _search.search(tiles, query=query)
    return render_template(
        "search.html",
        page_title="Поиск бумаг",
        query=query,
        results=results
    )

# ---------- JSON API ----------

@bp.get("/api/heatmap")
def api_heatmap():
    st = current_app.config["MARKET_STOCK"]
    ft = current_app.config["MARKET_FUT"]
    data = {
        "stocks": _get_tiles(st["engine"], st["market"], st["board"], fresh=False),
        "futures": _get_tiles(ft["engine"], ft["market"], ft["board"], fresh=False),
    }
    return jsonify(data)

@bp.get("/api/search")
def api_search():
    q = request.args.get("q", "")
    st = current_app.config["MARKET_STOCK"]
    ft = current_app.config["MARKET_FUT"]
    tiles = []
    tiles += _get_tiles(st["engine"], st["market"], st["board"], fresh=False)
    tiles += _get_tiles(ft["engine"], ft["market"], ft["board"], fresh=False)
    return jsonify({"query": q, "results": _search.search(tiles, q)})
