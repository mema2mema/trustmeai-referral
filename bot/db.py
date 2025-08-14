import os
import psycopg2
import psycopg2.extras
from contextlib import contextmanager

DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)

@contextmanager
def db_cursor():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            yield cur
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def ensure_user(tg_user_id: int, username: str = None, full_name: str = None):
    with db_cursor() as cur:
        cur.execute("SELECT id, tg_user_id, username, full_name, role, balance FROM users WHERE tg_user_id=%s", (tg_user_id,))
        row = cur.fetchone()
        if row:
            return row
        cur.execute(
            "INSERT INTO users (tg_user_id, username, full_name) VALUES (%s,%s,%s) RETURNING id, tg_user_id, username, full_name, role, balance",
            (tg_user_id, username, full_name)
        )
        return cur.fetchone()

def get_pending_withdrawals():
    with db_cursor() as cur:
        cur.execute("""SELECT w.*, u.username, u.tg_user_id
                       FROM withdrawals w
                       JOIN users u ON u.id=w.user_id
                       WHERE w.status='pending'
                       ORDER BY w.requested_at ASC""")
        return cur.fetchall()

def update_withdrawal_status(withdrawal_id: int, status: str, actor: str, txid: str = None, note: str = None):
    with db_cursor() as cur:
        cur.execute("""UPDATE withdrawals
                        SET status=%s, decided_at=NOW(), decided_by=%s, txid=COALESCE(%s, txid), note=COALESCE(%s, note)
                        WHERE id=%s
                        RETURNING *""", (status, actor, txid, note, withdrawal_id))
        return cur.fetchone()

def adjust_user_balance(user_id: int, mode: str, amount: float):
    with db_cursor() as cur:
        if mode == 'set':
            cur.execute("UPDATE users SET balance=%s WHERE id=%s RETURNING *", (amount, user_id))
        elif mode == 'add':
            cur.execute("UPDATE users SET balance=balance+%s WHERE id=%s RETURNING *", (amount, user_id))
        elif mode == 'sub':
            cur.execute("UPDATE users SET balance=balance-%s WHERE id=%s RETURNING *", (amount, user_id))
        else:
            raise ValueError("mode must be one of set|add|sub")
        return cur.fetchone()

def find_user(identifier: str):
    with db_cursor() as cur:
        if identifier.isdigit():
            cur.execute("SELECT * FROM users WHERE tg_user_id=%s", (int(identifier),))
        else:
            handle = identifier.lstrip('@')
            cur.execute("SELECT * FROM users WHERE username ILIKE %s", (handle,))
        return cur.fetchone()

def set_user_role(user_id: int, role: str):
    with db_cursor() as cur:
        cur.execute("UPDATE users SET role=%s WHERE id=%s RETURNING *", (role, user_id))
        return cur.fetchone()

def log_action(actor: str, action: str, entity_type: str = None, entity_id: str = None, meta: dict = None):
    with db_cursor() as cur:
        cur.execute("""INSERT INTO audit_logs (actor, action, entity_type, entity_id, meta)
                        VALUES (%s,%s,%s,%s,%s) RETURNING *""", (actor, action, entity_type, entity_id, psycopg2.extras.Json(meta or {})))
        return cur.fetchone()

def get_audit_logs(limit: int = 200):
    with db_cursor() as cur:
        cur.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT %s", (limit,))
        return cur.fetchall()

def list_users(limit: int = 200):
    with db_cursor() as cur:
        cur.execute("SELECT * FROM users ORDER BY created_at DESC LIMIT %s", (limit,))
        return cur.fetchall()

def list_withdrawals(status: str = None, limit: int = 200):
    with db_cursor() as cur:
        if status:
            cur.execute("""SELECT w.*, u.username, u.tg_user_id
                           FROM withdrawals w JOIN users u ON u.id=w.user_id
                           WHERE w.status=%s ORDER BY requested_at DESC LIMIT %s""", (status, limit))
        else:
            cur.execute("""SELECT w.*, u.username, u.tg_user_id
                           FROM withdrawals w JOIN users u ON u.id=w.user_id
                           ORDER BY requested_at DESC LIMIT %s""", (limit,))
        return cur.fetchall()

def migrate_schema():
    sql = """

DO $$
BEGIN
  -- Create users table if absent
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_name='users'
  ) THEN
    CREATE TABLE users (
      id BIGSERIAL PRIMARY KEY,
      tg_user_id BIGINT UNIQUE,
      username TEXT,
      full_name TEXT,
      role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('admin','manager','support','user')),
      balance NUMERIC(18,6) NOT NULL DEFAULT 0,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
  ELSE
    -- Add missing columns
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_name='users' AND column_name='tg_user_id'
    ) THEN
      ALTER TABLE users ADD COLUMN tg_user_id BIGINT;
    END IF;
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_name='users' AND column_name='username'
    ) THEN
      ALTER TABLE users ADD COLUMN username TEXT;
    END IF;
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_name='users' AND column_name='full_name'
    ) THEN
      ALTER TABLE users ADD COLUMN full_name TEXT;
    END IF;
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_name='users' AND column_name='role'
    ) THEN
      ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user';
    END IF;
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_name='users' AND column_name='balance'
    ) THEN
      ALTER TABLE users ADD COLUMN balance NUMERIC(18,6) NOT NULL DEFAULT 0;
    END IF;
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_name='users' AND column_name='created_at'
    ) THEN
      ALTER TABLE users ADD COLUMN created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
    END IF;
    -- Safe unique constraint on tg_user_id
    BEGIN
      ALTER TABLE users ADD CONSTRAINT users_tg_user_id_key UNIQUE (tg_user_id);
    EXCEPTION WHEN duplicate_object THEN
    END;
  END IF;
END $$;

-- Ensure withdrawals table exists
CREATE TABLE IF NOT EXISTS withdrawals (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  amount NUMERIC(18,6) NOT NULL CHECK (amount > 0),
  address TEXT NOT NULL,
  network TEXT NOT NULL DEFAULT 'TRC20',
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','approved','denied')),
  requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  decided_at TIMESTAMPTZ,
  decided_by TEXT,
  txid TEXT,
  note TEXT
);
CREATE INDEX IF NOT EXISTS withdrawals_status_idx ON withdrawals(status);

-- Ensure audit logs table exists
CREATE TABLE IF NOT EXISTS audit_logs (
  id BIGSERIAL PRIMARY KEY,
  actor TEXT,
  action TEXT NOT NULL,
  entity_type TEXT,
  entity_id TEXT,
  meta JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""
    with db_cursor() as cur:
        cur.execute(sql)
    return True
