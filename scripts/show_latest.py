# scripts/show_latest.py
from app.services.repository import MoexRepository

if __name__ == "__main__":
    repo = MoexRepository()
    for board_code in ("TQBR", "RFUD"):
        tiles = repo.get_latest_snapshot_items(board_code)
        print(f"\n[{board_code}] {len(tiles)} rows")
        for t in tiles[:10]:
            print(t)
    repo.close()
