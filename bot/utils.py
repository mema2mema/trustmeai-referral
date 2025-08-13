import os, json, csv, html
from pathlib import Path
from typing import List, Dict

def ensure_dirs(paths):
    for p in paths:
        Path(p).mkdir(parents=True, exist_ok=True)

def load_json(path: Path, default=None):
    if not Path(path).exists():
        return default if default is not None else {}
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}

def save_json(path: Path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def human_bytes(n: int) -> str:
    for unit in ["B","KB","MB","GB","TB"]:
        if n < 1024.0:
            return f"{n:.1f}{unit}"
        n /= 1024.0
    return f"{n:.1f}PB"

def read_csv_tail(path: Path, n: int=25) -> List[Dict]:
    if not Path(path).exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return rows[-n:]

def parse_trades_csv(path: Path):
    import pandas as pd
    df = pd.read_csv(path)
    lower_map = {c.lower(): c for c in df.columns}
    ren = {}
    if "timestamp" not in lower_map and "time" in lower_map:
        ren[lower_map["time"]] = "timestamp"
    if "symbol" not in lower_map and "ticker" in lower_map:
        ren[lower_map["ticker"]] = "symbol"
    if "pnl" not in lower_map and "profit" in lower_map:
        ren[lower_map["profit"]] = "pnl"
    if "qty" not in lower_map and "quantity" in lower_map:
        ren[lower_map["quantity"]] = "qty"
    if "price" not in lower_map and "fill_price" in lower_map:
        ren[lower_map["fill_price"]] = "price"
    if ren:
        df = df.rename(columns=ren)
    required = ["timestamp","symbol","side","qty","price","pnl"]
    for col in required:
        if col not in df.columns:
            if col == "pnl":
                if "PnL" in df.columns:
                    df["pnl"] = df["PnL"]
                else:
                    df["pnl"] = 0.0
            else:
                df[col] = None
    try:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    except Exception:
        pass
    for c in ["qty","price","pnl"]:
        try:
            df[c] = pd.to_numeric(df[c])
        except Exception:
            pass
    meta = {"rows": len(df), "path": str(path)}
    return df, meta

def safe_html(text: str) -> str:
    return html.escape(str(text)) if text is not None else ""

alphabet = "0123456789abcdefghijklmnopqrstuvwxyz"

def encode_ref(user_id: int) -> str:
    n = int(user_id)
    if n == 0: return "0"
    s = ""
    while n > 0:
        n, r = divmod(n, 36)
        s = alphabet[r] + s
    return s

def decode_ref(code: str) -> int | None:
    try:
        code = code.strip().lower()
        n = 0
        for ch in code:
            if ch not in alphabet:
                return None
            n = n*36 + alphabet.index(ch)
        return n
    except Exception:
        return None

def now_date_str() -> str:
    from datetime import datetime
    return datetime.utcnow().strftime("%Y-%m-%d")
