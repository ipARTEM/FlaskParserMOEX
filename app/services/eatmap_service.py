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

            # Для фьючерсов часто нет PREVPRICE — используем PREVSETTLEPRICE
            base = prev if not isnan(prev) else prev_settle
            change = None
            if base and base == base and last and last == last and base != 0:
                change = (last - base) / base * 100.0

            tiles.append({
                "secid": secid,
                "name": short,
                "last": last if last == last else None,
                "change": change,   # может быть None
                "valtoday": r.get("VALTODAY") or r.get("VOLTODAY"),
            })
        return tiles
