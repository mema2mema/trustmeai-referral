import json
from pathlib import Path

class Wallet:
    def __init__(self, path: Path):
        self.path = path
        self._ensure()

    def _ensure(self):
        if not self.path.exists():
            self._write({"balances": {}})

    def _read(self):
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {"balances": {}}

    def _write(self, data):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def balance(self, user_id: int) -> float:
        d = self._read()
        return float(d.get("balances", {}).get(str(user_id), 0.0))

    def deposit(self, user_id: int, amount: float):
        d = self._read()
        bal = float(d.get("balances", {}).get(str(user_id), 0.0))
        d.setdefault("balances", {})[str(user_id)] = bal + float(amount)
        self._write(d)

    def withdraw(self, user_id: int, amount: float):
        d = self._read()
        bal = float(d.get("balances", {}).get(str(user_id), 0.0))
        if amount <= 0:
            return False, "Amount must be > 0"
        if amount > bal:
            return False, "Insufficient balance"
        d["balances"][str(user_id)] = bal - amount
        self._write(d)
        return True, f"Withdrew {amount:.2f} USDT"
