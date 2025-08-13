import os, json
from pathlib import Path
def load_json(path: Path, default=None):
    if not path.exists(): return default if default is not None else {}
    try: return json.loads(path.read_text(encoding='utf-8'))
    except: return default if default is not None else {}
def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
