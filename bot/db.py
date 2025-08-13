
import os, time, datetime, threading
from dataclasses import dataclass
from typing import Optional, List, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

_DB_LOCK = threading.Lock()
_ENGINE: Optional[Engine] = None

def get_db_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        # local fallback
        os.makedirs("data", exist_ok=True)
        return "sqlite:///data/trustmeai.db"
    # normalize for SQLAlchemy psycopg: convert postgres:// to postgresql+psycopg://
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url.split("://",1)[1]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url.split("://",1)[1]
    elif url.startswith("postgresql+psycopg://"):
        pass
    return url

def engine() -> Engine:
    global _ENGINE
    with _DB_LOCK:
        if _ENGINE is None:
            _ENGINE = create_engine(get_db_url(), pool_pre_ping=True, future=True)
            init_db(_ENGINE)
    return _ENGINE

def init_db(e: Engine):
    with e.begin() as conn:
        conn.exec_driver_sql("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            tg_id BIGINT UNIQUE NOT NULL,
            username TEXT,
            balance_cents BIGINT NOT NULL DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
        """)
        conn.exec_driver_sql("""
        CREATE TABLE IF NOT EXISTS withdrawals (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            amount_cents BIGINT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending', -- pending, approved, rejected
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            decided_at TIMESTAMP NULL
        );
        """)

# Helpers
def get_or_create_user(tg_id: int, username: Optional[str]) -> Tuple[int, int]:
    """
    Returns (user_id, balance_cents)
    """
    e = engine()
    with e.begin() as conn:
        row = conn.execute(text("SELECT id, balance_cents FROM users WHERE tg_id=:tg_id"),
                           {"tg_id": tg_id}).first()
        if row:
            return row[0], int(row[1])
        res = conn.execute(text("INSERT INTO users (tg_id, username) VALUES (:tg_id, :username) RETURNING id, balance_cents"),
                           {"tg_id": tg_id, "username": username})
        r = res.first()
        return r[0], int(r[1])

def get_balance(tg_id:int)->int:
    e = engine()
    with e.begin() as conn:
        row = conn.execute(text("SELECT balance_cents FROM users WHERE tg_id=:tg_id"), {"tg_id": tg_id}).first()
        return int(row[0]) if row else 0

def add_deposit(tg_id:int, amount_cents:int)->int:
    e = engine()
    with e.begin() as conn:
        # ensure user exists
        conn.execute(text("INSERT INTO users (tg_id) VALUES (:tg_id) ON CONFLICT (tg_id) DO NOTHING"), {"tg_id": tg_id})
        conn.execute(text("UPDATE users SET balance_cents = balance_cents + :amt WHERE tg_id=:tg_id"),
                     {"amt": amount_cents, "tg_id": tg_id})
        row = conn.execute(text("SELECT balance_cents FROM users WHERE tg_id=:tg_id"), {"tg_id": tg_id}).first()
        return int(row[0])

def request_withdrawal(tg_id:int, amount_cents:int) -> Tuple[int, int]:
    """
    Creates a pending withdrawal if balance is enough. Returns (withdrawal_id, new_balance_cents).
    Raises ValueError if insufficient.
    """
    e = engine()
    with e.begin() as conn:
        u = conn.execute(text("SELECT id, balance_cents FROM users WHERE tg_id=:tg_id FOR UPDATE"),
                         {"tg_id": tg_id}).first()
        if not u:
            # auto create
            conn.execute(text("INSERT INTO users (tg_id) VALUES (:tg_id)"), {"tg_id": tg_id})
            u = conn.execute(text("SELECT id, balance_cents FROM users WHERE tg_id=:tg_id FOR UPDATE"),
                             {"tg_id": tg_id}).first()
        uid, bal = int(u[0]), int(u[1])
        if bal < amount_cents:
            raise ValueError("Insufficient balance")
        conn.execute(text("UPDATE users SET balance_cents = balance_cents - :amt WHERE id=:uid"),
                     {"amt": amount_cents, "uid": uid})
        res = conn.execute(text("""
            INSERT INTO withdrawals (user_id, amount_cents, status)
            VALUES (:uid, :amt, 'pending') RETURNING id
        """), {"uid": uid, "amt": amount_cents})
        wid = int(res.first()[0])
        nb = conn.execute(text("SELECT balance_cents FROM users WHERE id=:uid"), {"uid": uid}).first()[0]
        return wid, int(nb)

def list_pending_withdrawals(limit:int=50):
    e = engine()
    with e.begin() as conn:
        rows = conn.exec_driver_sql("""
            SELECT w.id, u.tg_id, u.username, w.amount_cents, w.created_at
            FROM withdrawals w
            JOIN users u ON u.id = w.user_id
            WHERE w.status='pending'
            ORDER BY w.created_at ASC
            LIMIT :lim
        """, {"lim": limit}).fetchall()
        return [{
            "id": int(r[0]), "tg_id": int(r[1]), "username": r[2],
            "amount_cents": int(r[3]), "created_at": str(r[4])
        } for r in rows]

def set_withdrawal_status(wid:int, status:str):
    e = engine()
    with e.begin() as conn:
        conn.exec_driver_sql("""
            UPDATE withdrawals SET status=:s, decided_at=NOW() WHERE id=:wid
        """, {"s": status, "wid": wid})

def get_user_id_for_withdrawal(wid:int)->Optional[int]:
    e = engine()
    with e.begin() as conn:
        r = conn.exec_driver_sql("""
            SELECT u.tg_id FROM withdrawals w JOIN users u ON u.id=w.user_id WHERE w.id=:wid
        """, {"wid": wid}).first()
        return int(r[0]) if r else None
