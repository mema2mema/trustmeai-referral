# TrustMe AI — v3.7.6

- Admin panel: approve/deny withdrawals, balances, roles, logs
- Telegram bot: polling or webhook (Railway-ready); supports ADMIN_IDS env
- Webhook env compatibility: `BOT_MODE` (or legacy `POLLING_MODE`), `PUBLIC_URL` (or `APP_BASE_URL`), optional `WEBHOOK_PATH`, `APP_TOKEN_IN_PATH`
- Commands: `/start`, `/summary`, `/log`, `/graph`, `/whoami`, admin `/approve_withdraw`, `/deny_withdraw`, `/balance`, `/set_role`, `/migrate`
- `/migrate` runs DB migrations to add missing columns/tables

## Env
- `TELEGRAM_BOT_TOKEN` (required)
- `DATABASE_URL` (required)
- `BOT_MODE` = `webhook` or `polling` (default polling). If missing, `POLLING_MODE=1` implies polling, `0` implies webhook.
- `PUBLIC_URL` (required if webhook). If missing, `APP_BASE_URL` is also read.
- `APP_TOKEN_IN_PATH` = `1` to use `/webhook/<token>`
- `WEBHOOK_PATH` = override path (e.g. `/webhook`)
- `ADMIN_IDS` = comma-separated numeric Telegram IDs (use `/whoami`)

## DB
Run once (optional if you will use `/migrate`):
```bash
psql "$DATABASE_URL" -f admin_panel/schema.sql
```
Or in Telegram as admin: `/migrate`

## Start
```bash
# polling (local)
export BOT_MODE=polling
python -m bot.main

# webhook (Railway)
export BOT_MODE=webhook
export PUBLIC_URL="https://<your-service>.up.railway.app"
python -m bot.main
```
