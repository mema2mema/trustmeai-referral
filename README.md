# TrustMe AI Telegram Bot — v3.9

New in v3.9:
- ✅ Admin **approve/deny** flow for withdrawals (inline buttons sent to `ADMIN_CHAT_ID`)
- 👥 **Multi-level referrals** (direct + level 2) with `/referral` and `/leaderboard`
- 🧾 **Auto performance report**: sent daily, and optionally after each trade (configurable)

## Quickstart
```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill TELEGRAM_BOT_TOKEN, ADMIN_CHAT_ID, BOT_USERNAME
export $(grep -v '^#' .env | xargs)  # or set envs on Windows manually
python -m bot.main
```

## Commands
- `/start` — subscribe + shows your referral code/link
- `/summary` `/graph` `/log`
- `/balance` `/deposit 100` `/withdraw 50` (requires admin approval if ADMIN_CHAT_ID set)
- `/referral` — your link + stats (direct + L2)
- `/leaderboard` — top referrers

## Auto Reports
- On each new trade append, if `AUTO_REPORT_ON_TRADE=1`, a quick report + equity chart is sent.
- Daily report (once per UTC day) if `DAILY_REPORT_ENABLE=1`.

## Referrals
- Share deep link from `/referral`.
- New users joining with `/start ref=<code>` give you direct credit.
- If your referred user refers others, you get L2 credit.

## Withdrawals
- Users run `/withdraw <amount>` → bot sends inline Approve/Deny to `ADMIN_CHAT_ID`.
- Approve deducts balance and notifies the user. Deny sends a rejection notice.
- If no `ADMIN_CHAT_ID` is set, withdrawals auto-approve (demo mode).

## Deploy on Railway (Webhook)
- Set `POLLING_MODE=0` and configure `APP_BASE_URL` or rely on `RAILWAY_PUBLIC_DOMAIN`.
- Keep your token secret!
