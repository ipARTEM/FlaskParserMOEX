# scripts/show_latest.py
"""
Выводит 10 бумаг из последнего снимка для TQBR и RFUD.
Запуск: python -m scripts.show_latest
"""
from app.services.repository import MoexRepository

if __name__ == "__main__":
    repo = MoexRepository()
    try:
        for board in ("TQBR", "RFUD"):
            snap = repo.get_snapshot_by_time(board, at_utc=None)
            tiles = repo.get_tiles_for_snapshot(snap)
            print(f"\n[{board}] {len(tiles)} rows")
            for t in tiles[:10]:
                print(t)
    finally:
        repo.close()
