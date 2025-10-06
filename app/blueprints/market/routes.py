# app/blueprints/market/routes.py
from flask import Blueprint, render_template, request, jsonify, abort, current_app, g, Response
from ...extensions import cache
from ...services.moex_client import MoexClient
from ...services.heatmap_service import HeatmapService
from ...services.search_service import SearchService

from ...services.repository import MoexRepository
from ...services.time_utils import parse_iso_utc

from datetime import datetime
import csv
from io import StringIO

bp = Blueprint("market", __name__, template_folder="../../templates")

_heatmap = HeatmapService()
_search = SearchService()

# ---------- helpers ----------

def _get_client() -> MoexClient:
    if not hasattr(g, "_moex_client"):
        g._moex_client = MoexClient(
            timeout=current_app.config.get("HTTP_TIMEOUT", 10),
            retries=current_app.config.get("HTTP_RETRIES", 2),
        )
    return g._moex_client

def _cache_key(engine: str, market: str, board: str) -> str:
    return f"board:{engine}:{market}:{board}"

def _get_tiles(engine: str, market: str, board: str, fresh: bool = False):
    key = _cache_key(engine, market, board)
    if not fresh:
        cached = cache.get(key)
        if cached is not None:
            return cached

    client = _get_client()
    data = client.get_board_data(engine, market, board)
    tiles = _heatmap.compute_tiles(data["rows"])
    cache.set(key, tiles, timeout=60)
    return tiles

# ---------- routes ----------

@bp.get("/parser")
def parser_page():
    mode = request.args.get("mode", "fast")
    fresh = (mode == "fresh")

    if fresh:
        token = request.args.get("admin_token", "")
        if current_app.config.get("ADMIN_TOKEN") and token != current_app.config["ADMIN_TOKEN"]:
            abort(403, description="Admin token required for fresh mode")

    # ВАЖНО: получаем конфиг и плитки СНАЧАЛА
    st = current_app.config["MARKET_STOCK"]  # {'engine','market','board'}
    ft = current_app.config["MARKET_FUT"]

    stock_tiles = _get_tiles(st["engine"], st["market"], st["board"], fresh=fresh)
    fut_tiles   = _get_tiles(ft["engine"], ft["market"], ft["board"], fresh=fresh)

    # Сохраняем снимки в БД только в fresh-режиме
    if fresh:
        repo = None
        try:
            repo = MoexRepository()

            eng_s = repo._get_or_create_engine(st["engine"], st["engine"].title())
            mkt_s = repo._get_or_create_market(eng_s, st["market"], st["market"].title())
            brd_s = repo._get_or_create_board(mkt_s, st["board"], st["board"])
            snap_s = repo.create_snapshot(brd_s, created_at=datetime.utcnow())
            repo.add_items(snap_s, _heatmap.to_db_items(stock_tiles))

            eng_f = repo._get_or_create_engine(ft["engine"], ft["engine"].title())
            mkt_f = repo._get_or_create_market(eng_f, ft["market"], ft["market"].title())
            brd_f = repo._get_or_create_board(mkt_f, ft["board"], ft["board"])
            snap_f = repo.create_snapshot(brd_f, created_at=datetime.utcnow())
            repo.add_items(snap_f, _heatmap.to_db_items(fut_tiles))

            repo.session.commit()
        except Exception as e:
            current_app.logger.warning(f"DB snapshot save failed: {e}")
        finally:
            if repo:
                repo.close()

    return render_template(
        "parser.html",
        page_title="Теплокарты MOEX",
        stock_tiles=stock_tiles,
        fut_tiles=fut_tiles,
        mode=mode
    )

@bp.get("/search")
def search_form():
    return render_template("search.html", page_title="Поиск бумаг")

@bp.post("/search")
def search_post():
    query = request.form.get("query", "")

    st = current_app.config["MARKET_STOCK"]
    ft = current_app.config["MARKET_FUT"]
    tiles = []
    tiles += _get_tiles(st["engine"], st["market"], st["board"], fresh=False)
    tiles += _get_tiles(ft["engine"], ft["market"], ft["board"], fresh=False)

    results = _search.search(tiles, query=query)
    return render_template("search.html", page_title="Поиск бумаг", query=query, results=results)

@bp.get("/api/heatmap")
def api_heatmap():
    st = current_app.config["MARKET_STOCK"]
    ft = current_app.config["MARKET_FUT"]
    return jsonify({
        "stocks": _get_tiles(st["engine"], st["market"], st["board"], fresh=False),
        "futures": _get_tiles(ft["engine"], ft["market"], ft["board"], fresh=False),
    })

@bp.get("/api/search")
def api_search():
    q = request.args.get("q", "")
    st = current_app.config["MARKET_STOCK"]
    ft = current_app.config["MARKET_FUT"]
    tiles = []
    tiles += _get_tiles(st["engine"], st["market"], st["board"], fresh=False)
    tiles += _get_tiles(ft["engine"], ft["market"], ft["board"], fresh=False)
    return jsonify({"query": q, "results": _search.search(tiles, q)})

@bp.get("/snapshot")
def snapshot_latest():
    """Показывает снимок из SQLite. Поддерживает ?at=YYYY-MM-DD[ HH:MM] (UTC)."""
    at = parse_iso_utc(request.args.get("at"))

    # Инициализируем, чтобы не ловить UnboundLocalError
    stock_tiles, fut_tiles = [], []

    repo = MoexRepository()
    try:
        snap_tqbr = repo.get_snapshot_by_time("TQBR", at)
        stock_tiles = repo.get_tiles_for_snapshot(snap_tqbr)

        snap_rfud = repo.get_snapshot_by_time("RFUD", at)
        fut_tiles  = repo.get_tiles_for_snapshot(snap_rfud)
    finally:
        repo.close()

    # Если БД ещё пустая — показываем дружелюбный экран
    if not stock_tiles and not fut_tiles:
        return render_template(
            "parser.html",
            page_title="Снимок из БД (нет данных)",
            stock_tiles=[],
            fut_tiles=[],
            mode="db",
        )

    return render_template(
        "parser.html",
        page_title=f"Снимок из БД ({'последний' if at is None else 'на момент ' + request.args.get('at','')})",
        stock_tiles=stock_tiles,
        fut_tiles=fut_tiles,
        mode="db",
    )

@bp.get("/api/snapshot")
def api_snapshot():
    """JSON-API: /market/api/snapshot?board=TQBR&at=YYYY-MM-DD[ HH:MM]"""
    at = parse_iso_utc(request.args.get("at"))
    board = (request.args.get("board") or "").upper().strip()
    repo = MoexRepository()
    try:
        def _one(bc: str):
            snap = repo.get_snapshot_by_time(bc, at)
            return repo.get_tiles_for_snapshot(snap)

        if board in ("TQBR", "RFUD"):
            return jsonify({board: _one(board)})
        return jsonify({"TQBR": _one("TQBR"), "RFUD": _one("RFUD")})
    finally:
        repo.close()

@bp.get("/snapshot.csv")
def snapshot_csv():
    """Экспорт последнего снимка (или на момент ?at) в CSV по обеим доскам."""
    at = parse_iso_utc(request.args.get("at"))
    repo = MoexRepository()
    try:
        rows = []
        for bc in ("TQBR", "RFUD"):
            snap = repo.get_snapshot_by_time(bc, at)
            tiles = repo.get_tiles_for_snapshot(snap)
            for t in tiles:
                rows.append({
                    "board": bc,
                    "secid": t["secid"], "name": t["name"],
                    "last": t["last"], "change": t["change"], "valtoday": t["valtoday"],
                })

        buf = StringIO()
        writer = csv.DictWriter(buf, fieldnames=["board", "secid", "name", "last", "change", "valtoday"])
        writer.writeheader()
        writer.writerows(rows)
        data = buf.getvalue()
        buf.close()

        filename = "snapshot_latest.csv" if at is None else f"snapshot_at_{request.args.get('at','').replace(':','-').replace(' ','_')}.csv"
        return Response(data, mimetype="text/csv",
                        headers={"Content-Disposition": f'attachment; filename=\"{filename}\"'})
    finally:
        repo.close()

@bp.get("/snapshots")
def snapshots_list():
    """
    Страница со списком последних снимков в БД (по двум доскам).
    У каждой строки — кнопка 'Показать' → /market/snapshot?at=YYYY-MM-DD HH:MM:SS
    """
    repo = MoexRepository()
    try:
        tqbr = repo.list_snapshots("TQBR", limit=100)
        rfud = repo.list_snapshots("RFUD", limit=100)
    finally:
        repo.close()

    return render_template(
        "snapshots.html",
        page_title="Снимки из БД",
        tqbr=tqbr,
        rfud=rfud,
    )

