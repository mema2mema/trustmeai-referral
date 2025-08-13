# TrustMe AI Telegram Bot — v4.0.0 (PTB 21 + health route)
# - python-telegram-bot 21.x
# - Webhook with health page on same domain (aiohttp)
# - url_path fix for /webhook
# - Polling mode still supported

import os, io, csv, json, logging
from datetime import datetime
from pathlib import Path

import pandas as pd, numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

from dotenv import load_dotenv; load_dotenv()

from aiohttp import web

from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    CallbackContext, ContextTypes, filters
)

# ----- Settings via env -----
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "")
TRADES_PATH = Path(os.getenv("TRADES_PATH", "data/trades.csv"))
STATE_DIR = Path(os.getenv("STATE_DIR", "state"))
UPLOADS_DIR = Path(os.getenv("UPLOADS_DIR", "data/uploads"))
POLLING_MODE = int(os.getenv("POLLING_MODE", "1"))
JOB_INTERVAL_SECONDS = int(os.getenv("JOB_INTERVAL_SECONDS", "10"))
APP_BASE_URL = os.getenv("APP_BASE_URL", "")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "tmai_secret")
AUTO_REPORT_ON_TRADE = int(os.getenv("AUTO_REPORT_ON_TRADE", "1"))
DAILY_REPORT_ENABLE = int(os.getenv("DAILY_REPORT_ENABLE", "1"))
BOT_USERNAME = os.getenv("BOT_USERNAME", "your_bot_username")

SUBSCRIBERS_FILE = STATE_DIR / "subscribers.json"
TRACKER_FILE = STATE_DIR / "trades_tracker.json"
WALLET_FILE = STATE_DIR / "mock_wallet.json"
WITHDRAWALS_FILE = STATE_DIR / "withdrawals.json"
REFERRALS_FILE = STATE_DIR / "referrals.json"
LAST_REPORT_FILE = STATE_DIR / "last_report.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("trustmeai.bot")
STATE_DIR.mkdir(parents=True, exist_ok=True)
TRADES_PATH.parent.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

from .utils import (
    load_json, save_json, read_csv_tail, parse_trades_csv, safe_html,
    encode_ref, decode_ref, now_date_str
)
from .wallet import Wallet
from .summary import build_summary_text

# ---------- Health routes ----------
async def health(request):
    return web.Response(text="TrustMe AI Bot OK", content_type="text/plain")

async def favicon(request):
    return web.Response(status=204)

# ---------- Referral helpers ----------
def admin_chat_id():
    try:
        return int(ADMIN_CHAT_ID) if ADMIN_CHAT_ID else None
    except:
        return None

def add_subscriber(chat_id: int):
    d = load_json(SUBSCRIBERS_FILE, {"subs": []})
    if chat_id not in d["subs"]:
        d["subs"].append(chat_id); save_json(SUBSCRIBERS_FILE, d)

def remove_subscriber(chat_id: int):
    d = load_json(SUBSCRIBERS_FILE, {"subs": []})
    if chat_id in d["subs"]:
        d["subs"].remove(chat_id); save_json(SUBSCRIBERS_FILE, d)

def get_subscribers():
    return load_json(SUBSCRIBERS_FILE, {"subs": []}).get("subs", [])

def ref_data(): return load_json(REFERRALS_FILE, {"users": {}, "stats": {}})
def save_ref_data(d): save_json(REFERRALS_FILE, d)

def set_referrer(user_id: int, code: str) -> bool:
    d = ref_data(); uid = str(user_id)
    if uid in d["users"] and d["users"][uid].get("referrer"): return False
    ref_uid = decode_ref(code)
    if not ref_uid or int(ref_uid) == int(user_id): return False
    d["users"].setdefault(uid, {}); d["users"][uid]["referrer"] = str(ref_uid); d["users"][uid]["joined"] = datetime.utcnow().isoformat()
    d["stats"].setdefault(str(ref_uid), {"direct": 0, "indirect": 0}); d["stats"][str(ref_uid)]["direct"] += 1
    parent = d["users"].get(str(ref_uid), {}).get("referrer")
    if parent:
        d["stats"].setdefault(str(parent), {"direct": 0, "indirect": 0}); d["stats"][str(parent)]["indirect"] += 1
    save_ref_data(d); return True

def referral_summary(uid: int):
    code = encode_ref(uid); link = f"https://t.me/{BOT_USERNAME}?start=ref={code}"
    d = ref_data(); stats = d["stats"].get(str(uid), {"direct": 0, "indirect": 0})
    return link, stats

def top_referrers(n=10):
    d = ref_data(); items = []
    for uid, s in d["stats"].items():
        total = int(s.get("direct",0)) + int(s.get("indirect",0))
        items.append((uid,total,s.get("direct",0),s.get("indirect",0)))
    items.sort(key=lambda x: x[1], reverse=True); return items[:n]

_wallet = Wallet(WALLET_FILE)

def wd_data(): return load_json(WITHDRAWALS_FILE, {"next_id":1,"pending":[],"history":[]})
def save_wd_data(d): save_json(WITHDRAWALS_FILE, d)
def new_withdrawal(uid:int, amount:float):
    d=wd_data(); wid=d["next_id"]; d["next_id"]+=1
    item={"id":wid,"user_id":int(uid),"amount":float(amount),"ts":datetime.utcnow().isoformat(),"status":"pending"}
    d["pending"].append(item); save_wd_data(d); return item
def approve_withdrawal(wid:int):
    d=wd_data(); idx=next((i for i,x in enumerate(d["pending"]) if x["id"]==wid),None)
    if idx is None: return False,"Request not found",None
    item=d["pending"].pop(idx); ok,msg=_wallet.withdraw(item["user_id"], item["amount"])
    item["status"]="approved" if ok else "rejected"; d["history"].append(item); save_wd_data(d)
    return ok, ("Withdrawal approved" if ok else "Rejected: "+msg), item
def deny_withdrawal(wid:int):
    d=wd_data(); idx=next((i for i,x in enumerate(d["pending"]) if x["id"]==wid),None)
    if idx is None: return False,"Request not found",None
    item=d["pending"].pop(idx); item["status"]="rejected"; d["history"].append(item); save_wd_data(d)
    return True,"Withdrawal denied.", item

# ---------- Commands ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id=update.effective_chat.id; add_subscriber(chat_id)
    payload = ""
    if update.message and update.message.text:
        parts = update.message.text.split(maxsplit=1)
        if len(parts) > 1: payload = parts[1].strip()
    if payload.startswith("ref="): set_referrer(chat_id, payload.split("=",1)[1])
    code = encode_ref(chat_id)
    await update.message.reply_html(
        "<b>TrustMe AI Bot — v4.0.0</b>\n\n"
        "You're subscribed to real-time trade alerts.\n\n"
        "<b>Key commands</b>\n"
        "/summary — performance summary\n"
        "/graph — equity curve chart\n"
        "/log — last 25 trades (or attach file)\n"
        "/subscribe — enable alerts here\n"
        "/unsubscribe — stop alerts here\n"
        "/balance — mock USDT balance\n"
        "/deposit 100 — add funds (mock)\n"
        "/withdraw 50 — request withdraw (admin approval)\n"
        "/referral — your link + stats\n"
        "/leaderboard — top referrers\n"
        "Upload a .csv to analyze it instantly.\n\n"
        f"Your referral code: <code>{code}</code>"
    )

async def help_cmd(update, context): await start(update, context)

async def subscribe(update, context): add_subscriber(update.effective_chat.id); await update.message.reply_html("✅ Subscribed.")
async def unsubscribe(update, context): remove_subscriber(update.effective_chat.id); await update.message.reply_html("🚫 Unsubscribed.")

async def status(update, context):
    subs=len(get_subscribers())
    await update.message.reply_html(
        f"<b>Status</b>\nSubscribers: {subs}\nFile: <code>{TRADES_PATH}</code>\nMode: {'Webhook' if not POLLING_MODE else 'Polling'}"
    )

async def log_cmd(update, context):
    if not TRADES_PATH.exists(): await update.message.reply_html("No trades file found."); return
    tail = read_csv_tail(TRADES_PATH, 25)
    if not tail: await update.message.reply_html("Trades file is empty."); return
    lines=["<b>Last 25 trades</b>"]
    for r in tail:
        ts=r.get("timestamp") or r.get("time") or r.get("date") or ""
        sym=r.get("symbol","?"); side=(r.get("side") or "").upper() or "?"
        qty=r.get("qty") or r.get("quantity") or r.get("size") or ""
        price=r.get("price") or r.get("fill_price") or ""
        pnl=r.get("pnl") or r.get("PnL") or r.get("profit") or ""
        lines.append(f"• {safe_html(ts)} {safe_html(sym)} {safe_html(side)} qty=<code>{safe_html(qty)}</code> price=<code>{safe_html(price)}</code> pnl=<code>{safe_html(pnl)}</code>")
    await update.message.reply_html("\n".join(lines))

async def summary_cmd(update, context):
    if not TRADES_PATH.exists(): await update.message.reply_html("No trades file found."); return
    try:
        df, meta = parse_trades_csv(TRADES_PATH); txt = build_summary_text(df, meta)
        await update.message.reply_html(txt, disable_web_page_preview=True)
    except Exception as e: await update.message.reply_text(f"Error: {e}")

async def graph_cmd(update, context):
    if not TRADES_PATH.exists(): await update.message.reply_html("No trades file found."); return
    try:
        df, meta = parse_trades_csv(TRADES_PATH)
        if "equity" not in df.columns:
            start=float(os.getenv("START_EQUITY","1000")); df["equity"]=start+df["pnl"].cumsum()
        fig=STATE_DIR/"equity.png"
        plt.figure(); plt.plot(df["timestamp"], df["equity"]); plt.title("Equity Curve"); plt.xlabel("Time"); plt.ylabel("Equity"); plt.xticks(rotation=30); plt.tight_layout(); plt.savefig(fig, dpi=150); plt.close()
        with open(fig,"rb") as f: await update.message.reply_photo(InputFile(f, filename="equity.png"), caption="Equity curve")
    except Exception as e: await update.message.reply_text(f"Graph error: {e}")

async def balance_cmd(update, context):
    uid=update.effective_chat.id; bal= _wallet.balance(uid)
    await update.message.reply_html(f"💼 <b>Mock USDT Balance:</b> <code>{bal:.2f}</code>")

async def deposit_cmd(update, context):
    uid=update.effective_chat.id
    try:
        amount=float(context.args[0]); _wallet.deposit(uid, amount)
        await update.message.reply_html(f"✅ Deposited <b>{amount:.2f}</b> USDT\nNew balance: <code>{_wallet.balance(uid):.2f}</code>")
    except: await update.message.reply_html("Usage: <code>/deposit 100</code>")

async def withdraw_cmd(update, context):
    uid=update.effective_chat.id
    try:
        amount=float(context.args[0]); wd=new_withdrawal(uid, amount); admin_id=admin_chat_id()
        if admin_id:
            kb=InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Approve", callback_data=f"wd:approve:{wd['id']}"),
                InlineKeyboardButton("❌ Deny", callback_data=f"wd:deny:{wd['id']}")
            ]])
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=(f"💸 <b>Withdraw Request</b>\nID: <code>{wd['id']}</code>\nUser: <code>{uid}</code>\nAmount: <b>{amount:.2f}</b> USDT"),
                    parse_mode=ParseMode.HTML, reply_markup=kb
                )
            except Exception as e:
                log.warning(f"Admin notify failed: {e}")
            await update.message.reply_html(f"⏳ Withdraw request submitted for <b>{amount:.2f}</b> USDT.")
        else:
            ok,msg,_=approve_withdrawal(wd["id"]); await update.message.reply_html(safe_html(msg))
    except: await update.message.reply_html("Usage: <code>/withdraw 50</code>")

async def callback_handler(update, context):
    q=update.callback_query; await q.answer(); data=q.data or ""
    try: kind,action,sid=data.split(":",2)
    except: return
    if kind=="wd":
        wid=int(sid)
        if action=="approve":
            ok,msg,item=approve_withdrawal(wid); await q.edit_message_text(f"Admin: {msg}")
            if item:
                try: await context.bot.send_message(chat_id=item["user_id"], text=f"✅ Your withdrawal of {item['amount']:.2f} USDT has been approved.")
                except: pass
        elif action=="deny":
            ok,msg,item=deny_withdrawal(wid); await q.edit_message_text(f"Admin: {msg}")
            if item:
                try: await context.bot.send_message(chat_id=item["user_id"], text=f"❌ Your withdrawal of {item['amount']:.2f} USDT was denied.")
                except: pass

async def referral_cmd(update, context):
    uid=update.effective_chat.id; link,stats=referral_summary(uid); code=encode_ref(uid)
    await update.message.reply_html(
        f"<b>Referral Program</b>\nYour code: <code>{code}</code>\nDeep link: {safe_html(link)}\n\nDirect: <b>{stats.get('direct',0)}</b> | L2: <b>{stats.get('indirect',0)}</b>",
        disable_web_page_preview=True
    )

async def leaderboard_cmd(update, context):
    rows=top_referrers(10)
    if not rows: await update.message.reply_html("No referrals yet."); return
    lines=["<b>Top Referrers</b>"]+[f"{i}. <code>{uid}</code> — total: <b>{tot}</b> (direct {d}, L2 {ind})" for i,(uid,tot,d,ind) in enumerate(rows,1)]
    await update.message.reply_html("\n".join(lines))

async def handle_document(update, context):
    doc=update.message.document
    if not doc or not doc.file_name.lower().endswith(".csv"):
        await update.message.reply_html("Please upload a .csv file."); return
    f=await doc.get_file(); dest=UPLOADS_DIR/f"{int(datetime.utcnow().timestamp())}_{doc.file_name}"
    await f.download_to_drive(dest)
    try:
        df,meta=parse_trades_csv(dest); TRADES_PATH.write_bytes(dest.read_bytes())
        await update.message.reply_html("<b>CSV uploaded and analyzed.</b>\n\n"+build_summary_text(df,meta), disable_web_page_preview=True)
    except Exception as e:
        await update.message.reply_text(f"Analyze failed: {e}")

def generate_report_files():
    if not TRADES_PATH.exists(): return None,None
    try:
        df,meta=parse_trades_csv(TRADES_PATH)
        if "equity" not in df.columns:
            start=float(os.getenv("START_EQUITY","1000")); df["equity"]=start+df["pnl"].cumsum()
        fig=STATE_DIR/"equity.png"
        plt.figure(); plt.plot(df["timestamp"], df["equity"]); plt.title("Equity Curve"); plt.xlabel("Time"); plt.ylabel("Equity"); plt.xticks(rotation=30); plt.tight_layout(); plt.savefig(fig, dpi=150); plt.close()
        txt=STATE_DIR/"performance-report.txt"; txt.write_text(build_summary_text(df,meta), encoding="utf-8")
        return txt, fig
    except Exception: return None,None

async def send_report(context:CallbackContext, chat_ids=None, title_prefix="Auto"):
    txt,fig=generate_report_files()
    if not txt or not fig: return
    if not chat_ids: chat_ids=get_subscribers()
    for cid in chat_ids:
        try:
            await context.bot.send_message(chat_id=cid, text=f"🧾 <b>{title_prefix} Performance Report</b>", parse_mode=ParseMode.HTML)
            with open(txt,"rb") as f: await context.bot.send_document(chat_id=cid, document=InputFile(f, filename="performance-report.txt"))
            with open(fig,"rb") as f: await context.bot.send_photo(chat_id=cid, photo=InputFile(f, filename="equity.png"), caption="Equity curve")
        except: pass

async def daily_report_job(context:CallbackContext):
    if not DAILY_REPORT_ENABLE: return
    today=now_date_str(); last=load_json(LAST_REPORT_FILE, {"date":""}).get("date","")
    if last==today: return
    if TRADES_PATH.exists():
        try:
            df,_=parse_trades_csv(TRADES_PATH)
            if len(df)>0: await send_report(context, title_prefix="Daily"); save_json(LAST_REPORT_FILE, {"date":today})
        except: pass

async def monitor_trades_job(context:CallbackContext):
    chat_ids=get_subscribers()
    if not chat_ids:
        return
    tracker=load_json(TRACKER_FILE, {"last_line":0}); last=tracker.get("last_line",0)
    if not TRADES_PATH.exists(): return
    try:
        with TRADES_PATH.open("r", newline="", encoding="utf-8") as f:
            rows=list(csv.DictReader(f))
    except Exception: return
    total=len(rows)
    if total<last: last=0
    new=rows[last:]
    if new:
        for r in new:
            ts=r.get("timestamp") or r.get("time") or r.get("date") or ""
            sym=r.get("symbol","?"); side=(r.get("side") or "").upper() or "?"
            qty=r.get("qty") or r.get("quantity") or r.get("size") or ""
            price=r.get("price") or r.get("fill_price") or ""
            pnl=r.get("pnl") or r.get("PnL") or r.get("profit") or ""
            emoji="🟢" if not str(pnl).strip().startswith("-") else "🔴"
            text=(f"⚡ <b>Trade Executed</b>\n{safe_html(ts)} — <b>{safe_html(sym)}</b> <b>{safe_html(side)}</b>\n"
                  f"qty=<code>{safe_html(qty)}</code> price=<code>{safe_html(price)}</code>\n"
                  f"PnL: {emoji} <code>{safe_html(pnl)}</code>")
            for cid in chat_ids:
                try: await context.bot.send_message(chat_id=cid, text=text, parse_mode=ParseMode.HTML)
                except: pass
        tracker["last_line"]=total; save_json(TRACKER_FILE, tracker)
        if AUTO_REPORT_ON_TRADE: await send_report(context, title_prefix="Auto")

def build_application() -> Application:
    if not TELEGRAM_BOT_TOKEN: raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("log", log_cmd))
    app.add_handler(CommandHandler("summary", summary_cmd))
    app.add_handler(CommandHandler("graph", graph_cmd))
    app.add_handler(CommandHandler("balance", balance_cmd))
    app.add_handler(CommandHandler("deposit", deposit_cmd))
    app.add_handler(CommandHandler("withdraw", withdraw_cmd))
    app.add_handler(CommandHandler("referral", referral_cmd))
    app.add_handler(CommandHandler("leaderboard", leaderboard_cmd))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(CallbackQueryHandler(callback_handler))

    if app.job_queue is None: raise RuntimeError("Install python-telegram-bot[job-queue]")
    app.job_queue.run_repeating(monitor_trades_job, interval=JOB_INTERVAL_SECONDS, first=5)
    app.job_queue.run_repeating(daily_report_job, interval=3600, first=60)
    return app

def main():
    app = build_application()
    if POLLING_MODE:
        log.info("Starting in polling mode...")
        app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=False)
    else:
        port = int(os.getenv("PORT", "8080"))
        base = APP_BASE_URL or os.getenv("RAILWAY_PUBLIC_DOMAIN", "")
        if base and not base.startswith("http"): base = "https://" + base
        if not base: raise RuntimeError("APP_BASE_URL or RAILWAY_PUBLIC_DOMAIN must be set for webhook mode")
        webhook_url = base.rstrip("/") + WEBHOOK_PATH
        log.info(f"Starting webhook on 0.0.0.0:{port} webhook_url={webhook_url}")

        # Small HTTP app for health + favicon
        web_app = web.Application()
        web_app.router.add_get("/", health)
        web_app.router.add_get("/favicon.ico", favicon)

        app.run_webhook(
            web_app=web_app,
            listen="0.0.0.0",
            port=port,
            url_path=WEBHOOK_PATH,
            webhook_url=webhook_url,
            secret_token=WEBHOOK_SECRET,
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=False
        )

if __name__ == "__main__":
    main()
