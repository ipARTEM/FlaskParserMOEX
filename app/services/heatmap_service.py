from typing import Dict, List, Any
from math import isnan

class HeatmapService:
    """
    Строит модель данных для теплокарт:
    - вычисляет % изменения
    - возвращает компактные «плитки» с полями для шаблона
    """

    @staticmethod
    def _safe(x):
        try:
            return float(x)
        except Exception:
            return float("nan")

    def compute_tiles(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        tiles = []
        for r in rows:
            secid = r.get("SECID")
            short = (r.get("SHORTNAME") or secid or "")[:18]

            last = self._safe(r.get("LAST"))
            prev = self._safe(r.get("PREVPRICE"))
            prev_settle = self._safe(r.get("PREVSETTLEPRICE"))

            base = prev if not isnan(prev) else prev_settle
            change = None
            if base and base == base and last and last == last and base != 0:
                change = (last - base) / base * 100.0

            tiles.append({
                "secid": secid,
                "name": short,
                "shortname": short,
                "last": last if last == last else None,
                "base_price": base if base == base else None,   # ← добавили
                "change": change,
                "valtoday": r.get("VALTODAY") or r.get("VOLTODAY"),
            })
        return tiles

    def to_db_items(self, tiles: list[dict]) -> list[dict]:
        """
        Приводит плитки к списку словарей с ключами, которые ожидает репозиторий:
        secid, shortname, last, base_price, change, valtoday
        """
        return [
            {
                "secid": t["secid"],
                "shortname": t.get("shortname"),
                "last": t.get("last"),
                "base_price": t.get("base_price"),
                "change": t.get("change"),
                "valtoday": t.get("valtoday"),
            }
            for t in tiles
        ]
