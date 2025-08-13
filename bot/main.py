
import os, logging, threading, asyncio, html
from dotenv import load_dotenv; load_dotenv()
from aiohttp import web
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from . import db

VERSION = "v5.2.0-dbadmin-polling"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN","")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID","")
POLLING_MODE = int(os.getenv("POLLING_MODE","1"))
PORT = int(os.getenv("PORT","8080"))
ADMIN_PANEL_TOKEN = os.getenv("ADMIN_PANEL_TOKEN","")
APP_BASE_URL = os.getenv("APP_BASE_URL", os.getenv("RAILWAY_PUBLIC_DOMAIN",""))
if APP_BASE_URL and not APP_BASE_URL.startswith("http"):
    APP_BASE_URL = "https://" + APP_BASE_URL

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("trustmeai.bot")

def is_admin(uid:int)->bool:
    try: return ADMIN_CHAT_ID and int(uid)==int(ADMIN_CHAT_ID)
    except: return False

# ---------- Telegram Handlers -----------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    await asyncio.to_thread(db.get_or_create_user, u.id, u.username)
    await update.message.reply_text(
        "TrustMe AI — %s\n"
        "Commands: /balance, /deposit 100, /withdraw 50, /admin" % VERSION
    )

async def version_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(VERSION)

async def ping_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("pong")

def _fmt_usd(cents:int)->str:
    return f"${cents/100:.2f}"

async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bal = await asyncio.to_thread(db.get_balance, update.effective_user.id)
    await update.message.reply_text(f"Balance: {_fmt_usd(bal)}")

async def deposit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = update.message.text.split()
    if len(args)<2 or not args[1].replace(".","",1).isdigit():
        await update.message.reply_text("Usage: /deposit <amount, e.g. 100 or 12.34>"); return
    amt = float(args[1])
    cents = int(round(amt*100))
    nb = await asyncio.to_thread(db.add_deposit, update.effective_user.id, cents)
    await update.message.reply_text(f"Deposited {_fmt_usd(cents)}. New balance: {_fmt_usd(nb)}")

async def withdraw_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = update.message.text.split()
    if len(args)<2 or not args[1].replace(".","",1).isdigit():
        await update.message.reply_text("Usage: /withdraw <amount>"); return
    amt = float(args[1]); cents = int(round(amt*100))
    try:
        wid, nb = await asyncio.to_thread(db.request_withdrawal, update.effective_user.id, cents)
    except ValueError:
        await update.message.reply_text("Insufficient balance"); return

    await update.message.reply_text(f"Withdrawal requested: {_fmt_usd(cents)} (id={wid}). Pending admin approval. New balance: {_fmt_usd(nb)}")
    # notify admin
    if ADMIN_CHAT_ID:
        try:
            link = (APP_BASE_URL.rstrip("/") if APP_BASE_URL else "") + f"/admin/withdrawals?token={ADMIN_PANEL_TOKEN}"
            await context.bot.send_message(chat_id=int(ADMIN_CHAT_ID),
                text=f"🧾 New withdrawal pending\nUser: {update.effective_user.id}\nAmount: {_fmt_usd(cents)}\nID: {wid}\n\nApprove: /approve_{wid}\nReject: /reject_{wid}\n\nAdmin page: {link}")
        except Exception as e:
            log.warning("Notify admin failed: %s", e)

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Admin only."); return
    base = APP_BASE_URL or "<set APP_BASE_URL>"
    url = (base.rstrip("/") if base else "") + "/admin?token=" + (ADMIN_PANEL_TOKEN or "<set ADMIN_PANEL_TOKEN>")
    await update.message.reply_html(f"<b>Admin panel</b>\nOpen: {html.escape(url)}", disable_web_page_preview=True)

async def approve_reject_inline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text or ""
    if not is_admin(update.effective_user.id):
        return
    if txt.startswith("/approve_"):
        wid = int(txt.split("_",1)[1]); await asyncio.to_thread(db.set_withdrawal_status, wid, "approved")
        uid = await asyncio.to_thread(db.get_user_id_for_withdrawal, wid)
        await update.message.reply_text(f"✅ Approved withdrawal id={wid}")
        if uid: 
            try: await context.bot.send_message(chat_id=uid, text=f"✅ Your withdrawal id={wid} has been approved.")
            except: pass
    elif txt.startswith("/reject_"):
        wid = int(txt.split("_",1)[1]); await asyncio.to_thread(db.set_withdrawal_status, wid, "rejected")
        uid = await asyncio.to_thread(db.get_user_id_for_withdrawal, wid)
        await update.message.reply_text(f"❌ Rejected withdrawal id={wid}")
        if uid:
            try: await context.bot.send_message(chat_id=uid, text=f"❌ Your withdrawal id={wid} has been rejected.")
            except: pass

def build_application()->Application:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("version", version_cmd))
    app.add_handler(CommandHandler("ping", ping_cmd))
    app.add_handler(CommandHandler("balance", balance_cmd))
    app.add_handler(CommandHandler("deposit", deposit_cmd))
    app.add_handler(CommandHandler("withdraw", withdraw_cmd))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, approve_reject_inline))
    return app

# --------- Web Admin (aiohttp) ---------
def require_token(handler):
    async def inner(request: web.Request):
        token = request.query.get("token") or request.headers.get("x-admin-token") or ""
        if not ADMIN_PANEL_TOKEN or token != ADMIN_PANEL_TOKEN:
            return web.Response(status=401, text="Unauthorized")
        return await handler(request)
    return inner

async def root_ok(request: web.Request):
    return web.Response(text=f"TrustMe AI Bot OK (polling) — {VERSION}", content_type="text/plain")

@require_token
async def admin_home(request: web.Request):
    html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>TrustMe AI — Admin</title>
<style>
body{{font-family:system-ui,-apple-system,Segoe UI,Roboto;background:#0b0f14;color:#e6eef8;max-width:1000px;margin:32px auto;padding:0 16px}}
.card{{background:#111827;border:1px solid #1f2937;border-radius:12px;padding:16px;margin-bottom:16px}}
table{{width:100%;border-collapse:collapse}} td,th{{border-bottom:1px solid #1f2937;padding:8px;text-align:left}}
a{{color:#7dd3fc;text-decoration:none}} .btn{{padding:6px 10px;border:1px solid #1f2937;border-radius:8px;background:#0f172a}}
</style></head><body>
<h1>TrustMe AI — Admin</h1>
<div class="card">
  <p>Polling mode admin is running.</p>
  <p><a class="btn" href="/admin/withdrawals?token={ADMIN_PANEL_TOKEN}">View pending withdrawals</a></p>
</div>
</body></html>"""
    return web.Response(text=html, content_type="text/html")

@require_token
async def admin_withdrawals(request: web.Request):
    rows = await asyncio.to_thread(db.list_pending_withdrawals, 100)
    def row_html(r):
        amt = f"${r['amount_cents']/100:.2f}"
        return f"<tr><td>{r['id']}</td><td>{r['tg_id']}</td><td>{r['username'] or ''}</td><td>{amt}</td><td>{r['created_at']}</td><td><a class='btn' href='/admin/approve?id={r['id']}&token={ADMIN_PANEL_TOKEN}'>Approve</a> <a class='btn' href='/admin/reject?id={r['id']}&token={ADMIN_PANEL_TOKEN}'>Reject</a></td></tr>"
    html = f"""<!doctype html><html><head><meta charset="utf-8"><title>Withdrawals</title>
<style>body{{font-family:system-ui;background:#0b0f14;color:#e6eef8;max-width:1100px;margin:32px auto;padding:0 16px}} table{{width:100%;border-collapse:collapse}} td,th{{border-bottom:1px solid #1f2937;padding:8px}}</style>
</head><body>
<h2>Pending withdrawals</h2>
<table><thead><tr><th>ID</th><th>User</th><th>Username</th><th>Amount</th><th>Requested</th><th>Action</th></tr></thead>
<tbody>
{''.join(row_html(r) for r in rows) if rows else "<tr><td colspan=6>No pending withdrawals</td></tr>"}
</tbody></table>
<p><a href="/admin?token={ADMIN_PANEL_TOKEN}">← Back</a></p>
</body></html>"""
    return web.Response(text=html, content_type="text/html")

@require_token
async def admin_approve(request: web.Request):
    wid = int(request.query.get("id","0"))
    await asyncio.to_thread(db.set_withdrawal_status, wid, "approved")
    uid = await asyncio.to_thread(db.get_user_id_for_withdrawal, wid)
    if uid:
        try:
            from telegram import Bot
            bot = Bot(token=TELEGRAM_BOT_TOKEN)
            await bot.send_message(chat_id=uid, text=f"✅ Your withdrawal id={wid} has been approved.")
        except Exception as e:
            pass
    raise web.HTTPFound(f"/admin/withdrawals?token={ADMIN_PANEL_TOKEN}")

@require_token
async def admin_reject(request: web.Request):
    wid = int(request.query.get("id","0"))
    await asyncio.to_thread(db.set_withdrawal_status, wid, "rejected")
    uid = await asyncio.to_thread(db.get_user_id_for_withdrawal, wid)
    if uid:
        try:
            from telegram import Bot
            bot = Bot(token=TELEGRAM_BOT_TOKEN)
            await bot.send_message(chat_id=uid, text=f"❌ Your withdrawal id={wid} has been rejected.")
        except Exception as e:
            pass
    raise web.HTTPFound(f"/admin/withdrawals?token={ADMIN_PANEL_TOKEN}")

def start_admin_server():
    app = web.Application()
    app.router.add_get("/", root_ok)
    app.router.add_get("/admin", admin_home)
    app.router.add_get("/admin/withdrawals", admin_withdrawals)
    app.router.add_get("/admin/approve", admin_approve)
    app.router.add_get("/admin/reject", admin_reject)
    web.run_app(app, host="0.0.0.0", port=PORT, handle_signals=False)

def main():
    # Ensure DB is initialised
    _ = db.engine()
    # Start aiohttp admin server
    t = threading.Thread(target=start_admin_server, daemon=True)
    t.start()
    # Start telegram bot (polling)
    app = build_application()
    log.info("Starting bot in polling mode with DB + admin UI ...")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=False)

if __name__=="__main__":
    main()
