from typing import List, Dict

class SearchService:
    """
    Очень простой «поиск» по тикеру/части названия
    (по уже полученным данным борда, без отдельного запроса).
    В реальности можно расширить до поиска через /securities.json по всей базе.
    """
    def search(self, tiles: List[Dict], query: str) -> List[Dict]:
        q = (query or "").strip().upper()
        if not q:
            return []

        res = []
        for t in tiles:
            secid = (t.get("secid") or "").upper()
            name = (t.get("name") or "").upper()
            if q in secid or q in name:
                res.append(t)
        return res
