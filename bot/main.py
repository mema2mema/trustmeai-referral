
import os, logging, secrets
from dotenv import load_dotenv; load_dotenv()
from aiohttp import web
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

VERSION = "v5.1.1-adminui-compat"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN","")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID","")
POLLING_MODE = int(os.getenv("POLLING_MODE","0"))
APP_BASE_URL = os.getenv("APP_BASE_URL","")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH","/webhook")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET","tmai_secret")
ADMIN_PANEL_TOKEN = os.getenv("ADMIN_PANEL_TOKEN","")
BOT_USERNAME = os.getenv("BOT_USERNAME","TrustMeAI_bot")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("trustmeai.adminui")

def is_admin(uid:int)->bool:
    try: return ADMIN_CHAT_ID and int(uid)==int(ADMIN_CHAT_ID)
    except: return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"TrustMe AI — {VERSION}\nUse /admin to open the web panel.")

async def version_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(VERSION)

async def ping_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("pong")

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Admin only."); return
    base = APP_BASE_URL or os.getenv("RAILWAY_PUBLIC_DOMAIN","")
    if base and not base.startswith("http"): base = "https://" + base
    url = (base.rstrip("/") if base else "") + "/admin?token=" + (os.getenv("ADMIN_PANEL_TOKEN",""))
    await update.message.reply_html(f"<b>Admin panel</b>\nOpen: {url}", disable_web_page_preview=True)

def require_token(handler):
    async def inner(request: web.Request):
        token = request.query.get("token") or request.headers.get("x-admin-token") or ""
        if not ADMIN_PANEL_TOKEN or token != ADMIN_PANEL_TOKEN:
            return web.Response(status=401, text="Unauthorized")
        return await handler(request)
    return inner

@require_token
async def admin_home(request: web.Request):
    html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>TrustMe AI Admin</title>
<style>
body{{font-family:system-ui,-apple-system,Segoe UI,Roboto;background:#0b0f14;color:#e6eef8;max-width:860px;margin:32px auto;padding:0 16px}}
.card{{background:#111827;border:1px solid #1f2937;border-radius:12px;padding:16px;margin-bottom:16px}}
button{{padding:10px 14px;border-radius:10px;border:1px solid #334155;background:#0ea5e9;color:#04131e;font-weight:700;cursor:pointer}}
.muted{{color:#93a2b8}}
</style></head><body>
<h1>TrustMe AI — Admin</h1>
<div class="muted">Version {VERSION}</div>
<div class="card">
  <p>Web admin is live. We’ll add more controls next.</p>
</div>
</body></html>"""
    return web.Response(text=html, content_type="text/html")

def build_app() -> Application:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("version", version_cmd))
    app.add_handler(CommandHandler("ping", ping_cmd))
    app.add_handler(CommandHandler("admin", admin_cmd))
    return app

def main():
    global ADMIN_PANEL_TOKEN
    if not ADMIN_PANEL_TOKEN:
        ADMIN_PANEL_TOKEN = secrets.token_hex(16)
        os.environ["ADMIN_PANEL_TOKEN"] = ADMIN_PANEL_TOKEN
        print("ADMIN_PANEL_TOKEN (temporary):", ADMIN_PANEL_TOKEN)

    app = build_app()

    if POLLING_MODE:
        log.info("Starting in polling mode...")
        app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=False)
        return

    # webhook mode
    base = APP_BASE_URL or os.getenv("RAILWAY_PUBLIC_DOMAIN","")
    if base and not base.startswith("http"): base = "https://" + base
    if not base:
        raise RuntimeError("APP_BASE_URL or RAILWAY_PUBLIC_DOMAIN must be set for webhook mode")
    webhook_url = base.rstrip("/") + WEBHOOK_PATH

    # Try PTB 21.x signature first (supports web_app)
    try:
        from telegram.ext import __version__ as PTB_VERSION
    except Exception:
        PTB_VERSION = "unknown"
    log.info(f"python-telegram-bot version: {PTB_VERSION}")

    try:
        web_app = web.Application()
        web_app.router.add_get("/", lambda r: web.Response(text="TrustMe AI Bot OK", content_type="text/plain"))
        web_app.router.add_get("/admin", admin_home)

        log.info("Starting webhook with admin UI (PTB21 path)...")
        app.run_webhook(web_app=web_app, listen="0.0.0.0", port=int(os.getenv("PORT","8080")),
                        url_path=WEBHOOK_PATH, webhook_url=webhook_url,
                        secret_token=WEBHOOK_SECRET, allowed_updates=Update.ALL_TYPES,
                        drop_pending_updates=False)
    except TypeError:
        # PTB 20.x fallback: no web_app argument available.
        log.warning("PTB 20.x detected. Admin UI disabled in webhook mode. Upgrade to PTB >=21 to enable /admin web.")
        app.run_webhook(listen="0.0.0.0", port=int(os.getenv("PORT","8080")),
                        url_path=WEBHOOK_PATH, webhook_url=webhook_url,
                        secret_token=WEBHOOK_SECRET, allowed_updates=Update.ALL_TYPES,
                        drop_pending_updates=False)

if __name__=="__main__":
    main()
