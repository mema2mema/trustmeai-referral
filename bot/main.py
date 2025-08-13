
import os, logging, threading
from dotenv import load_dotenv; load_dotenv()
from aiohttp import web
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

VERSION = "v5.1.3-adminui-polling"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN","")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID","")
POLLING_MODE = int(os.getenv("POLLING_MODE","1"))  # force polling
PORT = int(os.getenv("PORT","8080"))
ADMIN_PANEL_TOKEN = os.getenv("ADMIN_PANEL_TOKEN","")
APP_BASE_URL = os.getenv("APP_BASE_URL", os.getenv("RAILWAY_PUBLIC_DOMAIN",""))
if APP_BASE_URL and not APP_BASE_URL.startswith("http"):
    APP_BASE_URL = "https://" + APP_BASE_URL

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("trustmeai.polling_admin")

def is_admin(uid:int)->bool:
    try: return ADMIN_CHAT_ID and int(uid)==int(ADMIN_CHAT_ID)
    except: return False

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"TrustMe AI — {VERSION}\nUse /admin to open the web panel.")

async def version_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(VERSION)

async def ping_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("pong")

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Admin only."); return
    base = APP_BASE_URL or "<set APP_BASE_URL>"
    url = (base.rstrip("/") if base else "") + "/admin?token=" + (ADMIN_PANEL_TOKEN or "<set ADMIN_PANEL_TOKEN>")
    await update.message.reply_html(f"<b>Admin panel</b>\nOpen: {url}", disable_web_page_preview=True)

def build_bot() -> Application:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("version", version_cmd))
    app.add_handler(CommandHandler("ping", ping_cmd))
    app.add_handler(CommandHandler("admin", admin_cmd))
    return app

# --- aiohttp admin UI ---
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
<html><head><meta charset="utf-8"><title>TrustMe AI Admin</title>
<style>
body{{font-family:system-ui,-apple-system,Segoe UI,Roboto;background:#0b0f14;color:#e6eef8;max-width:860px;margin:32px auto;padding:0 16px}}
.card{{background:#111827;border:1px solid #1f2937;border-radius:12px;padding:16px;margin-bottom:16px}}
code{{background:#0f172a;padding:2px 6px;border-radius:6px}}
a{{color:#7dd3fc}}
</style></head><body>
<h1>TrustMe AI — Admin</h1>
<div class="card">
  <p>Polling mode admin is running. We’ll add more controls next.</p>
  <p>Telegram commands: <code>/version</code>, <code>/ping</code>, <code>/admin</code></p>
</div>
</body></html>"""
    return web.Response(text=html, content_type="text/html")

def start_admin_server():
    app = web.Application()
    app.router.add_get("/", root_ok)
    app.router.add_get("/admin", admin_home)
    # IMPORTANT: disable signal handling because we're in a thread on Railway/Nixpacks
    web.run_app(app, host="0.0.0.0", port=PORT, handle_signals=False)

def main():
    t = threading.Thread(target=start_admin_server, daemon=True)
    t.start()
    bot = build_bot()
    log.info("Starting bot in polling mode with admin UI on /admin ...")
    bot.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=False)

if __name__=="__main__":
    main()
