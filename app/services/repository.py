# app/services/repository.py
from __future__ import annotations
from datetime import datetime
from typing import Iterable
from sqlalchemy import select
from sqlalchemy.orm import Session
from .db import SessionLocal
from .models import Engine, Market, Board, Security, Snapshot, SnapshotItem

from datetime import datetime
from sqlalchemy import select, desc, func

class MoexRepository:
    """
    Репозиторий инкапсулирует всю работу с БД:
    - upsert справочников (engine/market/board/security)
    - сохранение снимков
    - выборки для страниц/апи
    """

    def __init__(self, session: Session | None = None) -> None:
        self._own_session = session is None
        self.session: Session = session or SessionLocal()

    def close(self):
        if self._own_session:
            self.session.close()

    # --- upsert helpers ---
    def _get_or_create_engine(self, code: str, name: str | None = None) -> Engine:
        s = self.session.scalar(select(Engine).where(Engine.code == code))
        if s: return s
        s = Engine(code=code, name=name)
        self.session.add(s)
        self.session.flush()
        return s

    def _get_or_create_market(self, engine: Engine, code: str, name: str | None = None) -> Market:
        s = self.session.scalar(select(Market).where(Market.engine_id == engine.id, Market.code == code))
        if s: return s
        s = Market(engine_id=engine.id, code=code, name=name)
        self.session.add(s)
        self.session.flush()
        return s

    def _get_or_create_board(self, market: Market, code: str, title: str | None = None) -> Board:
        s = self.session.scalar(select(Board).where(Board.market_id == market.id, Board.code == code))
        if s: return s
        s = Board(market_id=market.id, code=code, title=title)
        self.session.add(s)
        self.session.flush()
        return s

    def _get_or_create_security(self, secid: str, shortname: str | None) -> Security:
        s = self.session.scalar(select(Security).where(Security.secid == secid))
        if s:
            if shortname and s.shortname != shortname:
                s.shortname = shortname
            return s
        s = Security(secid=secid, shortname=shortname)
        self.session.add(s)
        self.session.flush()
        return s

    # --- snapshots ---
    def create_snapshot(self, board: Board, created_at: datetime | None = None) -> Snapshot:
        snap = Snapshot(board_id=board.id, created_at=created_at or datetime.utcnow())
        self.session.add(snap)
        self.session.flush()
        return snap

    def add_items(self, snapshot: Snapshot, items: Iterable[dict]) -> None:
        """
        items: Iterable[{'secid','shortname','last','base_price','change','valtoday'}]
        """
        for it in items:
            sec = self._get_or_create_security(it["secid"], it.get("shortname"))
            snap_item = SnapshotItem(
                snapshot_id=snapshot.id,
                security_id=sec.id,
                last=it.get("last"),
                base_price=it.get("base_price"),
                change_pct=it.get("change"),
                valtoday=it.get("valtoday"),
            )
            self.session.add(snap_item)

    # --- queries ---
    def get_latest_snapshot_items(self, board_code: str, limit: int = 200):
        stmt = select(Board).where(Board.code == board_code)
        board = self.session.scalar(stmt)
        if not board:
            return []

        # последний снимок по времени
        snap = self.session.scalar(select(Snapshot).where(Snapshot.board_id == board.id).order_by(Snapshot.created_at.desc()))
        if not snap:
            return []

        items = self.session.query(SnapshotItem, Security).join(Security, SnapshotItem.security_id == Security.id)\
            .filter(SnapshotItem.snapshot_id == snap.id).limit(limit).all()

        # приводим к фронтовому формату "tiles"
        tiles = []
        for item, sec in items:
            tiles.append({
                "secid": sec.secid,
                "name": (sec.shortname or sec.secid)[:18],
                "last": item.last,
                "change": item.change_pct,
                "valtoday": item.valtoday,
            })
        return tiles
    

    def get_snapshot_by_time(self, board_code: str, at_utc: datetime | None) -> Snapshot | None:
        """
        Возвращает снимок с наибольшим created_at <= at_utc.
        Если at_utc = None, берём самый последний снимок.
        """
        stmt_board = select(Board).where(Board.code == board_code)
        board = self.session.scalar(stmt_board)
        if not board:
            return None

        q = select(Snapshot).where(Snapshot.board_id == board.id)
        if at_utc:
            q = q.where(Snapshot.created_at <= at_utc)
        q = q.order_by(desc(Snapshot.created_at))
        return self.session.scalars(q).first()

    def get_tiles_for_snapshot(self, snapshot: Snapshot | None, limit: int = 200):
        if not snapshot:
            return []
        items = (self.session.query(SnapshotItem, Security)
                 .join(Security, SnapshotItem.security_id == Security.id)
                 .filter(SnapshotItem.snapshot_id == snapshot.id)
                 .limit(limit).all())
        tiles = []
        for it, sec in items:
            tiles.append({
                "secid": sec.secid,
                "name": (sec.shortname or sec.secid)[:18],
                "last": it.last,
                "change": it.change_pct,
                "valtoday": it.valtoday,
            })
        return tiles

    def list_snapshots(self, board_code: str, limit: int = 50):
        """
        Возвращает список последних снимков доски: (id, created_at, items_count)
        """
        board = self.session.scalar(select(Board).where(Board.code == board_code))
        if not board:
            return []

        q = (
            select(
                Snapshot.id,
                Snapshot.created_at,
                func.count(SnapshotItem.id).label("items_count"),
            )
            .join(SnapshotItem, SnapshotItem.snapshot_id == Snapshot.id, isouter=True)
            .where(Snapshot.board_id == board.id)
            .group_by(Snapshot.id)
            .order_by(desc(Snapshot.created_at))
            .limit(limit)
        )
        return list(self.session.execute(q).all())
