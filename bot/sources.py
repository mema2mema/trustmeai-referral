import os, csv
from datetime import datetime, timezone
from pathlib import Path

def _normalize(rows):
    out=[]
    for r in rows:
        out.append({
            "timestamp": r.get("timestamp") or r.get("time") or r.get("date"),
            "symbol": r.get("symbol") or r.get("ticker"),
            "side": (r.get("side") or "").upper(),
            "qty": float(r.get("qty") or r.get("quantity") or 0),
            "price": float(r.get("price") or r.get("fill_price") or 0),
            "pnl": float(r.get("pnl") or r.get("profit") or 0),
        })
    return out

def fetch_from_csv(path: Path):
    if not Path(path).exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        rows=list(csv.DictReader(f))
    return _normalize(rows)

def fetch_from_sheets():
    key = os.getenv("GOOGLE_SHEETS_KEY","").strip()
    url = os.getenv("GOOGLE_SHEETS_URL","").strip()
    worksheet = os.getenv("GOOGLE_SHEETS_WORKSHEET","trades")
    sa_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON","").strip()
    if not sa_json:
        return []
    try:
        import gspread, json
        from google.oauth2.service_account import Credentials
        info = json.loads(sa_json)
        scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        creds = Credentials.from_service_account_info(info, scopes=scopes)
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(key) if key else gc.open_by_url(url)
        ws = sh.worksheet(worksheet)
        rows = ws.get_all_records()
        return _normalize(rows)
    except Exception as e:
        print("Sheets fetch error:", e)
        return []

def fetch_from_exchange():
    exid = os.getenv("EXCHANGE","").lower()
    if not exid:
        return []
    try:
        import ccxt
        klass = getattr(ccxt, exid)
        apiKey=os.getenv("EXCHANGE_API_KEY",""); secret=os.getenv("EXCHANGE_SECRET",""); password=os.getenv("EXCHANGE_PASSWORD","") or None
        exchange = klass({"apiKey": apiKey, "secret": secret, "password": password, "enableRateLimit": True})
        symbols = [s.strip() for s in os.getenv("EXCHANGE_SYMBOLS","BTC/USDT").split(",") if s.strip()]
        out=[]
        since = None
        for sym in symbols:
            try:
                trades = exchange.fetchMyTrades(symbol=sym, since=since, limit=50)
                for t in trades:
                    side = (t.get("side") or "").upper()
                    qty = float(t.get("amount") or 0)
                    price = float(t.get("price") or 0)
                    ts = t.get("timestamp")
                    ts_str = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if ts else ""
                    out.append({"timestamp": ts_str, "symbol": sym.replace("/",""), "side": side, "qty": qty, "price": price, "pnl": 0.0})
            except Exception as e:
                print("Exchange fetch error:", e)
        return out
    except Exception as e:
        print("CCXT not available:", e)
        return []

def write_csv(path: Path, rows):
    if not rows:
        return
    cols=["timestamp","symbol","side","qty","price","pnl"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for r in rows:
            w.writerow({k:r.get(k) for k in cols})
