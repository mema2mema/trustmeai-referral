import os
DB_URL = os.getenv("DATABASE_URL", "").strip()
conn = None

def _connect():
    global conn
    if not DB_URL:
        return None
    if conn is not None:
        return conn
    try:
        import psycopg2
        conn = psycopg2.connect(DB_URL, sslmode="require" if "sslmode" not in DB_URL and DB_URL.startswith("postgres") else None)
        _init_schema(conn)
        return conn
    except Exception as e:
        print("DB connect failed:", e)
        return None

def _init_schema(c):
    cur=c.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS subscribers (chat_id BIGINT PRIMARY KEY, joined_at TIMESTAMP DEFAULT NOW());
CREATE TABLE IF NOT EXISTS trades (
    id BIGSERIAL PRIMARY KEY,
    ts TIMESTAMP,
    symbol TEXT, side TEXT, qty DOUBLE PRECISION, price DOUBLE PRECISION, pnl DOUBLE PRECISION
);
CREATE TABLE IF NOT EXISTS wallet (user_id BIGINT PRIMARY KEY, balance DOUBLE PRECISION DEFAULT 0);
CREATE TABLE IF NOT EXISTS withdrawals (
    id BIGSERIAL PRIMARY KEY, user_id BIGINT, amount DOUBLE PRECISION, ts TIMESTAMP, status TEXT
);
CREATE TABLE IF NOT EXISTS referrals (
    user_id BIGINT PRIMARY KEY, referrer BIGINT, joined_at TIMESTAMP
);
""")
    c.commit()

def add_subscriber(chat_id:int):
    c=_connect(); 
    if not c: return
    try:
        cur=c.cursor(); cur.execute("INSERT INTO subscribers(chat_id) VALUES(%s) ON CONFLICT DO NOTHING;", (chat_id,)); c.commit()
    except Exception: c.rollback()

def remove_subscriber(chat_id:int):
    c=_connect(); 
    if not c: return
    try:
        cur=c.cursor(); cur.execute("DELETE FROM subscribers WHERE chat_id=%s;", (chat_id,)); c.commit()
    except Exception: c.rollback()

def insert_trade(ts, symbol, side, qty, price, pnl):
    c=_connect(); 
    if not c: return
    try:
        cur=c.cursor(); cur.execute("INSERT INTO trades(ts,symbol,side,qty,price,pnl) VALUES(%s,%s,%s,%s,%s,%s);",
            (ts, symbol, side, qty, price, pnl)); c.commit()
    except Exception: c.rollback()

def wallet_set(user_id:int, balance:float):
    c=_connect(); 
    if not c: return
    try:
        cur=c.cursor(); cur.execute("INSERT INTO wallet(user_id,balance) VALUES(%s,%s) ON CONFLICT(user_id) DO UPDATE SET balance=EXCLUDED.balance;", (user_id,balance)); c.commit()
    except Exception: c.rollback()

def withdrawal_add(user_id:int, amount:float, ts, status:str):
    c=_connect(); 
    if not c: return
    try:
        cur=c.cursor(); cur.execute("INSERT INTO withdrawals(user_id,amount,ts,status) VALUES(%s,%s,%s,%s);", (user_id,amount,ts,status)); c.commit()
    except Exception: c.rollback()

def referral_set(user_id:int, referrer:int, joined_at):
    c=_connect();
    if not c: return
    try:
        cur=c.cursor(); cur.execute("INSERT INTO referrals(user_id,referrer,joined_at) VALUES(%s,%s,%s) ON CONFLICT(user_id) DO UPDATE SET referrer=EXCLUDED.referrer;", (user_id,referrer,joined_at)); c.commit()
    except Exception: c.rollback()
