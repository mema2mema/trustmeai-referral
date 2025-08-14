-- TrustMe AI — schema.sql (idempotent-ish)
-- Requires Postgres 12+

CREATE TABLE IF NOT EXISTS users (
  id BIGSERIAL PRIMARY KEY,
  tg_user_id BIGINT UNIQUE,
  username TEXT,
  full_name TEXT,
  role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('admin','manager','support','user')),
  balance NUMERIC(18,6) NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

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

CREATE TABLE IF NOT EXISTS audit_logs (
  id BIGSERIAL PRIMARY KEY,
  actor TEXT,
  action TEXT NOT NULL,
  entity_type TEXT,
  entity_id TEXT,
  meta JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS trades (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
  ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  symbol TEXT,
  side TEXT CHECK (side IN ('buy','sell')),
  qty NUMERIC(18,6),
  price NUMERIC(18,6),
  pnl NUMERIC(18,6)
);
