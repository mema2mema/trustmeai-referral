
import os, hmac, hashlib, time, jwt
from typing import Dict, Any, Optional, List

import psycopg2, psycopg2.extras
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_IDS","").replace(";",",").replace(" ",",").split(",") if x.strip().isdigit()}

def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL not set")
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)

def _has_column(cur, table: str, column: str) -> bool:
    cur.execute("SELECT 1 FROM information_schema.columns WHERE table_name=%s AND column_name=%s", (table, column))
    return cur.fetchone() is not None

def migrate_schema():
    sql = """
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='users') THEN
    CREATE TABLE users (
      id BIGSERIAL PRIMARY KEY,
      tg_user_id BIGINT UNIQUE,
      username TEXT,
      full_name TEXT,
      role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('admin','manager','support','user')),
      balance NUMERIC(18,6) NOT NULL DEFAULT 0,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='tg_user_id') THEN
    ALTER TABLE users ADD COLUMN tg_user_id BIGINT;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='username') THEN
    ALTER TABLE users ADD COLUMN username TEXT;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='full_name') THEN
    ALTER TABLE users ADD COLUMN full_name TEXT;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='role') THEN
    ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='balance') THEN
    ALTER TABLE users ADD COLUMN balance NUMERIC(18,6) NOT NULL DEFAULT 0;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='created_at') THEN
    ALTER TABLE users ADD COLUMN created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='users_tg_user_id_key') THEN
    ALTER TABLE users ADD CONSTRAINT users_tg_user_id_key UNIQUE (tg_user_id);
  END IF;
END $$;

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

-- Backfill legacy tg_id if exists
DO $$ BEGIN
IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='tg_id')
THEN UPDATE users SET tg_id = COALESCE(tg_id, tg_user_id); END IF;
END $$;
"""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()

def ensure_user(tg_user_id: int, username: Optional[str]=None, full_name: Optional[str]=None):
    migrate_schema()
    with get_conn() as conn:
        with conn.cursor() as cur:
            # fetch by tg_user_id, fallback tg_id
            cur.execute("SELECT * FROM users WHERE tg_user_id=%s", (tg_user_id,))
            row = cur.fetchone()
            if not row:
                cur.execute("SELECT * FROM users WHERE tg_id=%s", (tg_user_id,))
                row = cur.fetchone()
            if row:
                return row
            cols = ["tg_user_id","username","full_name"]
            vals = [tg_user_id, username, full_name]
            if _has_column(cur, "users", "tg_id"):
                cols = ["tg_user_id","tg_id","username","full_name"]
                vals = [tg_user_id, tg_user_id, username, full_name]
            cur.execute(f"INSERT INTO users ({','.join(cols)}) VALUES ({','.join(['%s']*len(vals))}) RETURNING *", tuple(vals))
            conn.commit()
            return cur.fetchone()

def is_admin(tg_id: int) -> bool:
    if tg_id in ADMIN_IDS:
        return True
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT role FROM users WHERE tg_user_id=%s", (tg_id,))
            r = cur.fetchone()
            if not r:
                cur.execute("SELECT role FROM users WHERE tg_id=%s", (tg_id,))
                r = cur.fetchone()
            return bool(r and r.get("role") in ("admin","manager"))

def _check_telegram_auth(auth_data: Dict[str, Any]) -> Dict[str, Any]:
    if not BOT_TOKEN:
        raise HTTPException(500, "Server not configured (no TELEGRAM_BOT_TOKEN)")
    received_hash = auth_data.get("hash")
    if not received_hash:
        raise HTTPException(400, "Missing hash")
    pairs = []
    for k in sorted(k for k in auth_data.keys() if k != "hash"):
        pairs.append(f"{k}={auth_data[k]}")
    data_check_string = "\n".join(pairs)
    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    h = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if h != received_hash:
        raise HTTPException(403, "Invalid signature")
    # auth_date freshness
    try:
        auth_ts = int(auth_data.get("auth_date", "0"))
        if abs(time.time() - auth_ts) > 86400:
            raise HTTPException(403, "Auth data expired")
    except ValueError:
        pass
    return auth_data

def sign_jwt(user: Dict[str, Any]) -> str:
    payload = {
        "sub": str(user.get("id")),  # telegram id
        "username": user.get("username"),
        "first_name": user.get("first_name"),
        "last_name": user.get("last_name"),
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def auth_from_header(req: Request) -> Dict[str, Any]:
    auth = req.headers.get("Authorization") or ""
    if not auth.lower().startswith("bearer "):
        raise HTTPException(401, "Missing bearer token")
    token = auth.split(" ",1)[1].strip()
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except Exception as e:
        raise HTTPException(401, f"Invalid token: {e}")

app = FastAPI(title="TrustMe AI — Web API")

if ALLOWED_ORIGIN:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[ALLOWED_ORIGIN],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Serve static landing + dashboard for convenience
root_dir = os.path.dirname(os.path.dirname(__file__))
landing_dir = os.path.join(root_dir, "landing")
app.mount("/", StaticFiles(directory=landing_dir, html=True), name="static")

@app.post("/verify")
async def verify(req: Request):
    body = await req.json()
    auth = _check_telegram_auth(body)
    # ensure exists in DB
    ensure_user(int(auth["id"]), auth.get("username"), (auth.get("first_name") or "") + " " + (auth.get("last_name") or ""))
    token = sign_jwt(auth)
    return {"ok": True, "token": token}

@app.get("/me")
async def me(req: Request):
    user = auth_from_header(req)
    tid = int(user["sub"])
    row = ensure_user(tid, user.get("username"), (user.get("first_name") or "") + " " + (user.get("last_name") or ""))
    return {"ok": True, "user": {"tg_id": tid, "username": user.get("username"), "first_name": user.get("first_name"), "last_name": user.get("last_name")}, "profile": {"role": row.get("role"), "balance": str(row.get("balance"))}}

@app.get("/withdrawals")
async def my_withdrawals(req: Request):
    user = auth_from_header(req)
    tid = int(user["sub"])
    with get_conn() as conn:
        with conn.cursor() as cur:
            # resolve pk
            cur.execute("SELECT id FROM users WHERE tg_user_id=%s", (tid,))
            r = cur.fetchone()
            if not r:
                cur.execute("SELECT id FROM users WHERE tg_id=%s", (tid,))
                r = cur.fetchone()
            if not r:
                return {"ok": True, "items": []}
            uid = r["id"]
            cur.execute("SELECT * FROM withdrawals WHERE user_id=%s ORDER BY requested_at DESC LIMIT 200", (uid,))
            items = cur.fetchall()
            return {"ok": True, "items": items}

@app.post("/withdraw")
async def withdraw(req: Request):
    user = auth_from_header(req)
    body = await req.json()
    try:
        amount = float(body.get("amount"))
        if amount <= 0: raise ValueError
    except Exception:
        raise HTTPException(400, "Invalid amount")
    address = body.get("address")
    network = body.get("network","TRC20")
    tid = int(user["sub"])
    with get_conn() as conn:
        with conn.cursor() as cur:
            # user row
            cur.execute("SELECT * FROM users WHERE tg_user_id=%s", (tid,))
            row = cur.fetchone()
            if not row:
                cur.execute("SELECT * FROM users WHERE tg_id=%s", (tid,))
                row = cur.fetchone()
            if not row:
                row = ensure_user(tid, user.get("username"), (user.get("first_name") or "") + " " + (user.get("last_name") or ""))
            if float(row["balance"]) < amount:
                raise HTTPException(400, f"Insufficient balance ({row['balance']})")
            # debit + create withdrawal
            cur.execute("UPDATE users SET balance=balance-%s WHERE id=%s RETURNING *", (amount, row["id"]))
            updated = cur.fetchone()
            cur.execute("INSERT INTO withdrawals (user_id, amount, address, network) VALUES (%s,%s,%s,%s) RETURNING *", (row["id"], amount, address, network))
            wd = cur.fetchone()
            conn.commit()
            return {"ok": True, "withdrawal": wd, "balance": str(updated["balance"])}

@app.get("/admin/summary")
async def admin_summary(req: Request):
    user = auth_from_header(req)
    tid = int(user["sub"])
    if not is_admin(tid):
        raise HTTPException(403, "Admins only")
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS users FROM users")
            users = cur.fetchone()["users"]
            cur.execute("SELECT COUNT(*) AS pending FROM withdrawals WHERE status='pending'")
            pending = cur.fetchone()["pending"]
            cur.execute("SELECT COALESCE(SUM(balance),0) AS total_balances FROM users")
            tb = cur.fetchone()["total_balances"]
            return {"ok": True, "users": users, "pending_withdrawals": pending, "total_balances": str(tb)}


from fastapi import Path, Body

def admin_required(req: Request):
    user = auth_from_header(req)
    tid = int(user["sub"])
    if not is_admin(tid):
        raise HTTPException(403, "Admins only")
    return tid

@app.get("/admin/users")
async def admin_users(req: Request, limit: int = 200):
    admin_required(req)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users ORDER BY created_at DESC LIMIT %s", (limit,))
            return {"ok": True, "items": cur.fetchall()}

@app.post("/admin/users/{user_id}/role")
async def admin_set_role(req: Request, user_id: int = Path(...), role: str = Body(..., embed=True)):
    admin_required(req)
    if role not in ("admin","manager","support","user"):
        raise HTTPException(400, "Invalid role")
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET role=%s WHERE id=%s RETURNING *", (role, user_id))
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "User not found")
            conn.commit()
            return {"ok": True, "user": row}

@app.post("/admin/users/{user_id}/balance")
async def admin_balance(req: Request, user_id: int = Path(...), mode: str = Body(..., embed=True), amount: float = Body(0.0, embed=True)):
    admin_required(req)
    if mode not in ("get","set","add","sub"):
        raise HTTPException(400, "Mode must be get|set|add|sub")
    with get_conn() as conn:
        with conn.cursor() as cur:
            if mode == "get":
                cur.execute("SELECT balance FROM users WHERE id=%s", (user_id,))
                r = cur.fetchone()
                if not r:
                    raise HTTPException(404, "User not found")
                return {"ok": True, "balance": str(r["balance"])}
            if mode == "set":
                cur.execute("UPDATE users SET balance=%s WHERE id=%s RETURNING balance", (amount, user_id))
            elif mode == "add":
                cur.execute("UPDATE users SET balance=balance+%s WHERE id=%s RETURNING balance", (amount, user_id))
            else:
                cur.execute("UPDATE users SET balance=balance-%s WHERE id=%s RETURNING balance", (amount, user_id))
            r = cur.fetchone()
            if not r:
                raise HTTPException(404, "User not found")
            conn.commit()
            return {"ok": True, "balance": str(r["balance"])}

@app.get("/admin/withdrawals")
async def admin_withdrawals(req: Request, status: str = None, limit: int = 500):
    admin_required(req)
    q = "SELECT w.*, u.username, u.tg_user_id FROM withdrawals w JOIN users u ON u.id=w.user_id"
    args = []
    if status in ("pending","approved","denied"):
        q += " WHERE w.status=%s"
        args.append(status)
    q += " ORDER BY requested_at DESC LIMIT %s"
    args.append(limit)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(q, tuple(args))
            return {"ok": True, "items": cur.fetchall()}

@app.post("/admin/withdrawals/{wid}/approve")
async def admin_w_approve(req: Request, wid: int = Path(...), txid: str = Body(None, embed=True)):
    admin_required(req)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM withdrawals WHERE id=%s", (wid,))
            prev = cur.fetchone()
            if not prev:
                raise HTTPException(404, "Withdrawal not found")
            cur.execute("""UPDATE withdrawals
                          SET status='approved', decided_at=NOW(), decided_by='web', txid=COALESCE(%s, txid)
                          WHERE id=%s RETURNING *""", (txid, wid))
            updated = cur.fetchone()
            conn.commit()
            return {"ok": True, "withdrawal": updated, "prev": prev}

@app.post("/admin/withdrawals/{wid}/deny")
async def admin_w_deny(req: Request, wid: int = Path(...), note: str = Body("Denied", embed=True)):
    admin_required(req)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM withdrawals WHERE id=%s", (wid,))
            prev = cur.fetchone()
            if not prev:
                raise HTTPException(404, "Withdrawal not found")
            cur.execute("""UPDATE withdrawals
                          SET status='denied', decided_at=NOW(), decided_by='web', note=%s
                          WHERE id=%s RETURNING *""", (note, wid))
            updated = cur.fetchone()
            # auto-refund when denying pending
            if prev.get("status") == "pending":
                cur.execute("UPDATE users SET balance=balance+%s WHERE id=%s", (prev["amount"], prev["user_id"]))
            conn.commit()
            return {"ok": True, "withdrawal": updated, "refunded": prev.get("status") == "pending"}

@app.get("/admin/logs")
async def admin_logs(req: Request, limit: int = 200):
    admin_required(req)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT %s", (limit,))
            return {"ok": True, "items": cur.fetchall()}


from fastapi.responses import StreamingResponse, PlainTextResponse
import csv
from io import StringIO

def token_or_header(req: Request) -> str:
    # Allow Authorization header OR token=? query for CSV links
    auth = req.headers.get("Authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth.split(" ",1)[1].strip()
    token = req.query_params.get("token")
    if token:
        return token
    raise HTTPException(401, "Missing token")

@app.get("/health")
async def health():
    return {"ok": True}

@app.get("/export/users.csv")
async def export_users(req: Request):
    token = token_or_header(req)
    user = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    if not is_admin(int(user["sub"])):
        raise HTTPException(403, "Admins only")
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, tg_user_id, username, full_name, role, balance, created_at FROM users ORDER BY created_at DESC")
            rows = cur.fetchall()
    buf = StringIO()
    w = csv.DictWriter(buf, fieldnames=["id","tg_user_id","username","full_name","role","balance","created_at"])
    w.writeheader()
    for r in rows:
        w.writerow(r)
    buf.seek(0)
    return PlainTextResponse(buf.read(), media_type="text/csv", headers={"Content-Disposition":"attachment; filename=users.csv"})

@app.get("/export/withdrawals.csv")
async def export_withdrawals(req: Request):
    token = token_or_header(req)
    user = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    if not is_admin(int(user["sub"])):
        raise HTTPException(403, "Admins only")
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""SELECT w.*, u.username, u.tg_user_id
                            FROM withdrawals w JOIN users u ON u.id=w.user_id
                            ORDER BY requested_at DESC""")
            rows = cur.fetchall()
    buf = StringIO()
    if rows:
        fields = list(rows[0].keys())
    else:
        fields = ["id","user_id","amount","address","network","status","requested_at","decided_at","decided_by","txid","note","username","tg_user_id"]
    w = csv.DictWriter(buf, fieldnames=fields)
    w.writeheader()
    for r in rows:
        w.writerow(r)
    buf.seek(0)
    return PlainTextResponse(buf.read(), media_type="text/csv", headers={"Content-Disposition":"attachment; filename=withdrawals.csv"})

@app.get("/export/logs.csv")
async def export_logs(req: Request):
    token = token_or_header(req)
    user = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    if not is_admin(int(user["sub"])):
        raise HTTPException(403, "Admins only")
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM audit_logs ORDER BY created_at DESC")
            rows = cur.fetchall()
    buf = StringIO()
    if rows:
        fields = list(rows[0].keys())
    else:
        fields = ["id","actor","action","entity_type","entity_id","meta","created_at"]
    w = csv.DictWriter(buf, fieldnames=fields)
    w.writeheader()
    for r in rows:
        # ensure JSON is stringified
        if isinstance(r.get("meta"), dict):
            r = dict(r)
            r["meta"] = json.dumps(r["meta"])
        w.writerow(r)
    buf.seek(0)
    return PlainTextResponse(buf.read(), media_type="text/csv", headers={"Content-Disposition":"attachment; filename=logs.csv"})
