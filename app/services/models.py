# app/services/models.py
from __future__ import annotations
from datetime import datetime
from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

class Engine(Base):
    __tablename__ = "engines"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=True)

    markets: Mapped[list["Market"]] = relationship(back_populates="engine")

class Market(Base):
    __tablename__ = "markets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    engine_id: Mapped[int] = mapped_column(ForeignKey("engines.id"), nullable=False)
    code: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=True)

    engine: Mapped["Engine"] = relationship(back_populates="markets")
    boards: Mapped[list["Board"]] = relationship(back_populates="market")

    __table_args__ = (UniqueConstraint("engine_id", "code", name="uq_market_engine_code"),)

class Board(Base):
    __tablename__ = "boards"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    market_id: Mapped[int] = mapped_column(ForeignKey("markets.id"), nullable=False)
    code: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=True)

    market: Mapped["Market"] = relationship(back_populates="boards")
    snapshots: Mapped[list["Snapshot"]] = relationship(back_populates="board")

    __table_args__ = (UniqueConstraint("market_id", "code", name="uq_board_market_code"),)

class Security(Base):
    __tablename__ = "securities"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    secid: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    shortname: Mapped[str] = mapped_column(String, nullable=True)

    items: Mapped[list["SnapshotItem"]] = relationship(back_populates="security")

class Snapshot(Base):
    __tablename__ = "snapshots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    board_id: Mapped[int] = mapped_column(ForeignKey("boards.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    source: Mapped[str] = mapped_column(String, nullable=True, default="moex_iss")

    board: Mapped["Board"] = relationship(back_populates="snapshots")
    items: Mapped[list["SnapshotItem"]] = relationship(back_populates="snapshot", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("board_id", "created_at", name="uq_snapshot_board_time"),)

class SnapshotItem(Base):
    __tablename__ = "snapshot_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    snapshot_id: Mapped[int] = mapped_column(ForeignKey("snapshots.id"), nullable=False)
    security_id: Mapped[int] = mapped_column(ForeignKey("securities.id"), nullable=False)

    last: Mapped[float | None] = mapped_column(Float, nullable=True)
    base_price: Mapped[float | None] = mapped_column(Float, nullable=True)   # prevprice/prevsettle
    change_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    valtoday: Mapped[float | None] = mapped_column(Float, nullable=True)

    snapshot: Mapped["Snapshot"] = relationship(back_populates="items")
    security: Mapped["Security"] = relationship(back_populates="items")

    __table_args__ = (UniqueConstraint("snapshot_id", "security_id", name="uq_item_snapshot_security"),)
