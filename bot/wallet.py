
import json
from pathlib import Path
class Wallet:
    def __init__(self, path: Path): self.path=path; self._ensure()
    def _ensure(self):
        if not self.path.exists(): self._write({'balances':{}})
    def _read(self):
        try: return json.loads(self.path.read_text(encoding='utf-8'))
        except: return {'balances':{}}
    def _write(self, d): self.path.parent.mkdir(parents=True, exist_ok=True); self.path.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding='utf-8')
    def balance(self, uid:int)->float:
        d=self._read(); return float(d.get('balances',{}).get(str(uid),0.0))
    def deposit(self, uid:int, amt:float):
        d=self._read(); bal=float(d.get('balances',{}).get(str(uid),0.0)); d.setdefault('balances',{})[str(uid)]=bal+float(amt); self._write(d)
    def withdraw(self, uid:int, amt:float):
        d=self._read(); bal=float(d.get('balances',{}).get(str(uid),0.0))
        if amt<=0: return False,'Amount must be > 0'
        if amt>bal: return False,'Insufficient balance'
        d['balances'][str(uid)]=bal-amt; self._write(d); return True, f'Withdrew {amt:.2f} USDT'
