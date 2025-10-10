# app/services/repository.py
"""
Репозиторий инкапсулирует работу с ORM: upsert справочников, сохранение снимков, выборки.
"""

from __future__ import annotations
from datetime import datetime
from sqlalchemy import select, desc, func
from sqlalchemy.orm import Session
from .db import SessionLocal
from .models import Engine, Market, Board, Security, Snapshot, SnapshotItem


class MoexRepository:
    def __init__(self, session: Session | None = None) -> None:
        self._own_session = session is None
        self.session: Session = session or SessionLocal()

    def close(self) -> None:
        if self._own_session:
            self.session.close()

    # -------- upsert справочников --------

    def _get_or_create_engine(self, code: str, name: str | None = None) -> Engine:
        result = self.session.scalar(select(Engine).where(Engine.code == code))
        if result:
            return result
        obj = Engine(code=code, name=name)
        self.session.add(obj)
        self.session.flush()
        return obj

    def _get_or_create_market(self, engine: Engine, code: str, name: str | None = None) -> Market:
        result = self.session.scalar(select(Market).where(Market.engine_id == engine.id, Market.code == code))
        if result:
            return result
        obj = Market(engine_id=engine.id, code=code, name=name)
        self.session.add(obj)
        self.session.flush()
        return obj

    def _get_or_create_board(self, market: Market, code: str, title: str | None = None) -> Board:
        result = self.session.scalar(select(Board).where(Board.market_id == market.id, Board.code == code))
        if result:
            return result
        obj = Board(market_id=market.id, code=code, title=title)
        self.session.add(obj)
        self.session.flush()
        return obj

    def _get_or_create_security(self, secid: str, shortname: str | None) -> Security:
        result = self.session.scalar(select(Security).where(Security.secid == secid))
        if result:
            if shortname and result.shortname != shortname:
                result.shortname = shortname
            return result
        obj = Security(secid=secid, shortname=shortname)
        self.session.add(obj)
        self.session.flush()
        return obj

    # -------- работа со снимками --------

    def create_snapshot(self, board: Board, created_at: datetime | None = None) -> Snapshot:
        snap = Snapshot(board_id=board.id, created_at=created_at or datetime.utcnow())
        self.session.add(snap)
        self.session.flush()
        return snap

    def add_items(self, snapshot: Snapshot, items: list[dict]) -> None:
        """
        items: [{secid, shortname, last, base_price, change, valtoday}, ...]
        """
        for it in items:
            sec = self._get_or_create_security(it["secid"], it.get("shortname"))
            self.session.add(SnapshotItem(
                snapshot_id=snapshot.id,
                security_id=sec.id,
                last=it.get("last"),
                base_price=it.get("base_price"),
                change_pct=it.get("change"),
                valtoday=it.get("valtoday"),
            ))

    # -------- выборки для сайта / API --------

    def get_snapshot_by_time(self, board_code: str, at_utc: datetime | None):
        board = self.session.scalar(select(Board).where(Board.code == board_code))
        if not board:
            return None
        q = select(Snapshot).where(Snapshot.board_id == board.id)
        if at_utc:
            q = q.where(Snapshot.created_at <= at_utc)
        q = q.order_by(desc(Snapshot.created_at))
        return self.session.scalars(q).first()

    def get_tiles_for_snapshot(self, snapshot: Snapshot | None, limit: int = 400):
        if not snapshot:
            return []
        rows = (
            self.session.query(SnapshotItem, Security)
            .join(Security, SnapshotItem.security_id == Security.id)
            .filter(SnapshotItem.snapshot_id == snapshot.id)
            .limit(limit).all()
        )
        tiles = []
        for it, sec in rows:
            tiles.append({
                "secid": sec.secid,
                "name": (sec.shortname or sec.secid)[:18],
                "last": it.last,
                "change": it.change_pct,
                "valtoday": it.valtoday,
            })
        return tiles

    def list_snapshots(self, board_code: str, limit: int = 100):
        """Список последних снимков (id, created_at, items_count)."""
        board = self.session.scalar(select(Board).where(Board.code == board_code))
        if not board:
            return []
        q = (
            select(Snapshot.id, Snapshot.created_at, func.count(SnapshotItem.id).label("items_count"))
            .join(SnapshotItem, SnapshotItem.snapshot_id == Snapshot.id, isouter=True)
            .where(Snapshot.board_id == board.id)
            .group_by(Snapshot.id)
            .order_by(desc(Snapshot.created_at))
            .limit(limit)
        )
        return list(self.session.execute(q).all())
