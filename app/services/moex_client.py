import time
from typing import Dict, List, Any, Optional
import requests

class MoexClient:
    """
    Класс-клиент ISS MOEX API.
    Принципы:
    - Чёткие методы: get_board_data(...) для securities+marketdata
    - Малые, предсказуемые ответы (dict/list)
    - Повторы (retries) и таймауты контролируем параметрами
    """

    BASE = "https://iss.moex.com/iss"

    def __init__(self, timeout: int = 10, retries: int = 2) -> None:
        self.timeout = timeout
        self.retries = retries

    def _request(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        last_exc = None
        for attempt in range(self.retries + 1):
            try:
                resp = requests.get(url, params=params, timeout=self.timeout)
                resp.raise_for_status()
                return resp.json()
            except Exception as exc:
                last_exc = exc
                time.sleep(0.5 * attempt + 0.1)
        raise RuntimeError(f"MOEX request failed: {url} params={params} err={last_exc}")

    def get_board_data(
        self, engine: str, market: str, board: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Возвращает объединённые таблицы securities + marketdata для указанного борда.
        Собираем только нужные колонки — так быстрее и понятнее.
        """
        url = f"{self.BASE}/engines/{engine}/markets/{market}/boards/{board}/securities.json"
        params = {
            "iss.only": "securities,marketdata",
            "iss.meta": "off",
            # Можно дополнять колонки по необходимости
            "securities.columns": "SECID,SHORTNAME,PREVPRICE,PREVSETTLEPRICE",
            "marketdata.columns": "SECID,LAST,OPEN,LOW,HIGH,VALTODAY,VOLTODAY",
        }
        data = self._request(url, params=params)

        # Преобразуем в список словарей по строкам
        sec_cols = data["securities"]["columns"]
        sec_rows = data["securities"]["data"]
        md_cols = data["marketdata"]["columns"]
        md_rows = data["marketdata"]["data"]

        securities = [dict(zip(sec_cols, row)) for row in sec_rows]
        marketdata = [dict(zip(md_cols, row)) for row in md_rows]

        # Индексируем marketdata по SECID
        md_index = {row["SECID"]: row for row in marketdata}

        # Склеиваем инфо по каждой бумаге
        merged: List[Dict[str, Any]] = []
        for s in securities:
            secid = s["SECID"]
            md = md_index.get(secid, {})
            merged.append({**s, **md})

        return {"rows": merged}
