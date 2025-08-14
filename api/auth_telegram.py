
import os, hmac, hashlib, time
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import jwt

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN")

app = FastAPI(title="TrustMe AI Auth API")

if ALLOWED_ORIGIN:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[ALLOWED_ORIGIN],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

def _check_telegram_auth(auth_data: Dict[str, Any]) -> Dict[str, Any]:
    if not BOT_TOKEN:
        raise HTTPException(500, "Server not configured (no TELEGRAM_BOT_TOKEN)")
    received_hash = auth_data.get("hash")
    if not received_hash:
        raise HTTPException(400, "Missing hash")
    # Build data-check-string from all fields except 'hash'
    pairs = []
    for k in sorted(k for k in auth_data.keys() if k != "hash"):
        pairs.append(f"{k}={auth_data[k]}")
    data_check_string = "\n".join(pairs)
    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    h = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if h != received_hash:
        raise HTTPException(403, "Invalid signature")
    # check auth_date (optional)
    try:
        auth_ts = int(auth_data.get("auth_date", "0"))
        if abs(time.time() - auth_ts) > 86400:  # older than 24h
            raise HTTPException(403, "Auth data expired")
    except ValueError:
        pass
    return auth_data

@app.post("/verify")
async def verify(req: Request):
    body = await req.json()
    auth = _check_telegram_auth(body)
    # Sign short-lived JWT
    payload = {
        "sub": str(auth.get("id")),
        "username": auth.get("username"),
        "first_name": auth.get("first_name"),
        "last_name": auth.get("last_name"),
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return {"ok": True, "token": token, "user": payload}

@app.get("/")
async def root():
    return {"ok": True, "service": "TrustMe AI Auth API"}
