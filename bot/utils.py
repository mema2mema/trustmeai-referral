import os, json, csv, html
from pathlib import Path

def load_json(path: Path, default=None):
    if not Path(path).exists(): return default if default is not None else {}
    try: return json.loads(Path(path).read_text(encoding='utf-8'))
    except: return default if default is not None else {}

def save_json(path: Path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def read_csv_tail(path: Path, n:int=25):
    if not Path(path).exists(): return []
    with path.open('r', newline='', encoding='utf-8') as f:
        rows=list(csv.DictReader(f))
    return rows[-n:]

def parse_trades_csv(path: Path):
    import pandas as pd
    df=pd.read_csv(path)
    lower={c.lower():c for c in df.columns}
    ren={}
    if 'timestamp' not in df.columns and 'time' in lower: ren[lower['time']]='timestamp'
    if 'symbol' not in df.columns and 'ticker' in lower: ren[lower['ticker']]='symbol'
    if 'pnl' not in df.columns and 'profit' in lower: ren[lower['profit']]='pnl'
    if 'qty' not in df.columns and 'quantity' in lower: ren[lower['quantity']]='qty'
    if 'price' not in df.columns and 'fill_price' in lower: ren[lower['fill_price']]='price'
    if ren: df=df.rename(columns=ren)
    for c in ['timestamp','symbol','side','qty','price','pnl']:
        if c not in df.columns: df[c]=None
    try: df['timestamp']=pd.to_datetime(df['timestamp'])
    except: pass
    for c in ['qty','price','pnl']:
        try: df[c]=pd.to_numeric(df[c])
        except: pass
    meta={'rows':len(df),'path':str(path)}
    return df, meta

def safe_html(s): 
    return html.escape(str(s)) if s is not None else ''

alphabet='0123456789abcdefghijklmnopqrstuvwxyz'
def encode_ref(n:int)->str:
    n=int(n); 
    if n==0: return '0'
    s=''
    while n>0:
        n,r=divmod(n,36); s=alphabet[r]+s
    return s

def decode_ref(code:str):
    try:
        code=code.strip().lower(); n=0
        for ch in code:
            if ch not in alphabet: return None
            n=n*36 + alphabet.index(ch)
        return n
    except: return None

def now_date_str():
    from datetime import datetime
    return datetime.utcnow().strftime('%Y-%m-%d')
