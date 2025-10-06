# scripts/seed_fake.py
from datetime import datetime
from app.services.db import SessionLocal
from app.services.models import Engine, Market, Board
from app.services.repository import MoexRepository
from app.services.init_db import create_all_tables

if __name__ == "__main__":
    create_all_tables()
    s = SessionLocal()
    repo = MoexRepository(s)

    # Справочники
    eng = repo._get_or_create_engine("stock", "Stocks")
    mkt = repo._get_or_create_market(eng, "shares", "Shares")
    brd = repo._get_or_create_board(mkt, "TQBR", "T+ Акции")

    snap = repo.create_snapshot(brd, created_at=datetime.utcnow())
    items = [
        {"secid":"GAZP","shortname":"GAZP","last":207.5,"base_price":205.0,"change":(207.5-205)/205*100,"valtoday":1.23e9},
        {"secid":"SBER","shortname":"SBER","last":296.7,"base_price":300.0,"change":(296.7-300)/300*100,"valtoday":2.34e9},
        {"secid":"LKOH","shortname":"LKOH","last":7850,"base_price":7700,"change":(7850-7700)/7700*100,"valtoday":0.98e9},
    ]
    repo.add_items(snap, items)
    s.commit()

    # выборка
    tiles = repo.get_latest_snapshot_items("TQBR")
    for t in tiles:
        print(t)

    repo.close()
    print("OK: тестовые данные загружены и выбраны.")
