# TrustMe AI — v3.7.0 (Admin Actions + Roles + Logging + Webhook-ready + Landing Site)

This upgrade delivers:
1) **Admin actions** to approve/deny withdrawals and adjust balances (Streamlit admin panel)
2) **User roles** (`admin`, `manager`, `support`, `user`) and a basic role editor
3) **Audit logging** for all admin changes
4) **Telegram bot** runnable in **polling** or **webhook** mode (Railway-ready)
5) **Branded landing site** (static, Netlify-ready)

---

## 0) Environment

Set these env vars (Railway/locally):

- `TELEGRAM_BOT_TOKEN`  (required)
- `DATABASE_URL`        (required, e.g. postgres://user:pass@host:5432/dbname)
- `BOT_MODE`            (`polling` or `webhook`, default: `polling`)
- `PUBLIC_URL`          (required if `BOT_MODE=webhook`, e.g. https://your-app.up.railway.app)
- `APP_TOKEN_IN_PATH`   (0 or 1; default 0) — if 1, webhook path adds the bot token
- `TRADES_PATH`         (optional, default `trades.csv`) — for /summary, /log, /graph
- `ADMIN_PASSPHRASE`    (passphrase to unlock Streamlit admin, e.g. set in Railway variables)

---

## 1) Database

Apply `schema.sql` **once** to your Postgres:

```bash
psql "$DATABASE_URL" -f admin_panel/schema.sql
```

If you already have tables, this file uses `IF NOT EXISTS` and safe constraints.

---

## 2) Admin Panel

Run locally:
```bash
pip install -r requirements.txt
streamlit run admin_panel/admin_panel.py
```

Open http://localhost:8501, enter your **ADMIN_PASSPHRASE**, and operate:
- **Withdrawals**: approve/deny pending requests
- **Balances**: set/add/subtract user balances
- **Users**: assign roles
- **Logs**: view audit logs

---

## 3) Telegram Bot

### Polling mode (local quick run)
```bash
export BOT_MODE=polling
python bot/bot_main.py
```

### Webhook mode (Railway 24/7)

Set Railway env:
- `BOT_MODE=webhook`
- `PUBLIC_URL=https://<your-railway-subdomain>.up.railway.app`
- `PORT=8080` (Railway sets this automatically; we read it)

Start command:
```bash
python bot/bot_main.py
```

This app will:
- Set webhook to `${PUBLIC_URL}/webhook` (or `/webhook/<token>` if `APP_TOKEN_IN_PATH=1`)
- Bind to `0.0.0.0:$PORT`

**Tip:** If you change the domain, redeploy to refresh the webhook.

---

## 4) Landing Site (Netlify-ready)

Upload the `web/` folder to Netlify. The contact form uses [Netlify Forms].
- Change links & copy in `index.html`
- Update logo in `web/assets/logo.svg`

`netlify.toml` is included (pretty URLs, basic security headers).

---

## 5) Notes

- Roles are stored per user (`users.role`). Admin panel access is guarded by `ADMIN_PASSPHRASE`.
- Every admin change writes to `audit_logs` with a helpful JSON snapshot.
- The bot includes admin commands (`/approve_withdraw`, `/deny_withdraw`, `/balance`, `/set_role`) — restricted by a hardcoded allowlist you can widen in `bot_main.py` or by mapping Telegram users to role=admin in the DB.
