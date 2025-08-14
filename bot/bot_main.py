import os
import logging
import csv

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from .db import ensure_user, find_user, set_user_role, adjust_user_balance, update_withdrawal_status, log_action, migrate_schema

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("trustmeai.bot")

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# --- mode compatibility ---
_raw_mode = os.getenv("BOT_MODE")
if not _raw_mode:
    _pm = os.getenv("POLLING_MODE")
    if _pm and _pm.strip().lower() in ("1","true","yes","on"):
        _raw_mode = "polling"
    elif _pm and _pm.strip().lower() in ("0","false","no","off"):
        _raw_mode = "webhook"
    else:
        _raw_mode = "polling"
MODE = _raw_mode.lower()

# compat: PUBLIC_URL or APP_BASE_URL
PUBLIC_URL = os.getenv("PUBLIC_URL") or os.getenv("APP_BASE_URL")
PORT = int(os.getenv("PORT", "8080"))
APP_TOKEN_IN_PATH = int(os.getenv("APP_TOKEN_IN_PATH", "0")) == 1
TRADES_PATH = os.getenv("TRADES_PATH", "trades.csv")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH")  # optional override

def _parse_admin_ids_env():
    raw = os.getenv("ADMIN_IDS", "").replace(";", ",").replace(" ", ",")
    ids = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            ids.add(int(part))
        except ValueError:
            pass
    return ids
ADMIN_IDS = _parse_admin_ids_env()

def is_admin(user_id: int) -> bool:
    if user_id in ADMIN_IDS:
        return True
    try:
        row = ensure_user(user_id)
        return row and row.get("role") in ("admin", "manager")
    except Exception:
        return False

# --- Commands ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    ensure_user(u.id, u.username, u.full_name)
    await update.message.reply_html(
        f"""👋 Welcome <b>{u.first_name}</b>!
<b>TrustMe AI</b> bot is online.
Use /summary, /log, /graph to review performance.
""")

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        total = 0.0
        wins = 0
        losses = 0
        with open(TRADES_PATH, "r", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                pnl = float(row.get("pnl", "0") or 0)
                total += pnl
                if pnl >= 0:
                    wins += 1
                else:
                    losses += 1
        await update.message.reply_html(
            f"""<b>Performance Summary</b>
Total PnL: <b>{total:.2f}</b>
Wins: <b>{wins}</b> • Losses: <b>{losses}</b>""")
    except FileNotFoundError:
        await update.message.reply_text("No trades file found.")

async def log_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import html
    try:
        with open(TRADES_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()[-16:]
        safe = html.escape("".join(lines))
        await update.message.reply_html(f"<pre><code>{safe}</code></pre>")
    except FileNotFoundError:
        await update.message.reply_text("No trades file found.")

async def graph(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Graph endpoint pending — use admin panel for now.")

# --- Admin Commands ---

async def approve_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        return await update.message.reply_text("Admins only.")
    if not context.args:
        return await update.message.reply_text("Usage: /approve_withdraw <withdrawal_id> [txid]")
    wid = int(context.args[0])
    txid = context.args[1] if len(context.args) > 1 else None
    before = {"id": wid}
    updated = update_withdrawal_status(wid, "approved", f"tg:{uid}", txid, None)
    log_action(f"tg:{uid}", "withdrawal_approve", "withdrawal", str(wid), {"before": before, "after": updated})
    await update.message.reply_text(f"Approved withdrawal #{wid}")

async def deny_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        return await update.message.reply_text("Admins only.")
    if not context.args:
        return await update.message.reply_text("Usage: /deny_withdraw <withdrawal_id> [reason]")
    wid = int(context.args[0])
    note = " ".join(context.args[1:]) if len(context.args) > 1 else "Denied"
    before = {"id": wid}
    updated = update_withdrawal_status(wid, "denied", f"tg:{uid}", None, note)
    log_action(f"tg:{uid}", "withdrawal_deny", "withdrawal", str(wid), {"before": before, "after": updated})
    await update.message.reply_text(f"Denied withdrawal #{wid}")

async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        return await update.message.reply_text("Admins only.")
    if len(context.args) < 2:
        return await update.message.reply_text("Usage: /balance <tg_id|@user> <get|set|add|sub> [amount]")
    ident, mode = context.args[0], context.args[1]
    amount = float(context.args[2]) if len(context.args) > 2 else 0.0
    user = find_user(ident)
    if not user:
        return await update.message.reply_text("User not found.")
    if mode == "get":
        return await update.message.reply_text(f"Balance: {user['balance']}")
    before = user.copy()
    updated = adjust_user_balance(user['id'], mode, amount)
    log_action(f"tg:{uid}", f"balance_{mode}", "user", str(user['id']), {"before": before, "after": updated, "amount": amount})
    await update.message.reply_text(f"Updated balance → {updated['balance']}")

async def set_role_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        return await update.message.reply_text("Admins only.")
    if len(context.args) < 2:
        return await update.message.reply_text("Usage: /set_role <tg_id|@user> <admin|manager|support|user>")
    ident, role = context.args[0], context.args[1]
    user = find_user(ident)
    if not user:
        return await update.message.reply_text("User not found.")
    before = user.copy()
    updated = set_user_role(user['id'], role)
    log_action(f"tg:{uid}", "role_set", "user", str(user['id']), {"before": before, "after": updated})
    await update.message.reply_text(f"Role set → {role}")

async def whoami(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    ensure_user(u.id, u.username, u.full_name)
    handle = f"@{u.username}" if u.username else "—"
    await update.message.reply_html(f"<b>ID:</b> {u.id}\n<b>Username:</b> {handle}\n<b>Name:</b> {u.full_name}")

async def migrate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        return await update.message.reply_text("Admins only.")
    try:
        migrate_schema()
        await update.message.reply_text("Migration complete ✅")
    except Exception as e:
        await update.message.reply_text(f"Migration failed: {e}")

def make_app() -> Application:
    if not TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set")
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(CommandHandler("log", log_cmd))
    app.add_handler(CommandHandler("graph", graph))
    app.add_handler(CommandHandler("whoami", whoami))

    app.add_handler(CommandHandler("approve_withdraw", approve_withdraw))
    app.add_handler(CommandHandler("deny_withdraw", deny_withdraw))
    app.add_handler(CommandHandler("balance", balance_cmd))
    app.add_handler(CommandHandler("set_role", set_role_cmd))
    app.add_handler(CommandHandler("migrate", migrate_cmd))

    async def on_error(update, context):
        log.exception("Unhandled error", exc_info=context.error)
    app.add_error_handler(on_error)

    return app

def main():
    app = make_app()
    if MODE == "webhook":
        if not PUBLIC_URL:
            raise RuntimeError("PUBLIC_URL required for webhook mode")
        if WEBHOOK_PATH:
            url_path = WEBHOOK_PATH.lstrip("/")
        else:
            url_path = f"webhook/{TOKEN}" if APP_TOKEN_IN_PATH else "webhook"
        webhook_url = f"{PUBLIC_URL.rstrip('/')}/{url_path}"
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=url_path,
            webhook_url=webhook_url,
            drop_pending_updates=True
        )
    else:
        app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
