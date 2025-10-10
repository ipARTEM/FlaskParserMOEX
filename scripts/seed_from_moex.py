# scripts/seed_from_moex.py
"""
Тянет реальные данные с MOEX через наши сервисы и сохраняет СНИМКИ в БД.
Запуск: python -m scripts.seed_from_moex
"""
from datetime import datetime
from app.services.db import SessionLocal
from app.services.init_db import create_all_tables
from app.services.repository import MoexRepository
from app.services.heatmap_service import HeatmapService
from app.services.moex_client import MoexClient

# Настрой борды под свои Config, если нужно
STOCK = {"engine": "stock", "market": "shares", "board": "TQBR"}
FUT   = {"engine": "futures", "market": "forts", "board": "RFUD"}

def fetch_tiles(engine: str, market: str, board: str) -> list[dict]:
    client = MoexClient(timeout=10, retries=2)
    data = client.get_board_data(engine, market, board)
    return HeatmapService().compute_tiles(data["rows"])

if __name__ == "__main__":
    create_all_tables()

    s = SessionLocal()
    repo = MoexRepository(s)
    try:
        # STOCK
        eng_s = repo._get_or_create_engine(STOCK["engine"], "Stocks")
        mkt_s = repo._get_or_create_market(eng_s, STOCK["market"], "Shares")
        brd_s = repo._get_or_create_board(mkt_s, STOCK["board"], "T+ Акции")
        tiles_s = fetch_tiles(**STOCK)
        snap_s = repo.create_snapshot(brd_s, created_at=datetime.utcnow())
        repo.add_items(snap_s, HeatmapService().to_db_items(tiles_s))

        # FUTURES
        eng_f = repo._get_or_create_engine(FUT["engine"], "Futures")
        mkt_f = repo._get_or_create_market(eng_f, FUT["market"], "Forts")
        brd_f = repo._get_or_create_board(mkt_f, FUT["board"], "Фьючерсы")
        tiles_f = fetch_tiles(**FUT)
        snap_f = repo.create_snapshot(brd_f, created_at=datetime.utcnow())
        repo.add_items(snap_f, HeatmapService().to_db_items(tiles_f))

        s.commit()
        print("OK: реальные данные загружены в БД.")
    finally:
        repo.close()
