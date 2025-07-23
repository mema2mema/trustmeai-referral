from utils.logger import setup_logger
from bot.strategy import run_redhawk_strategy
from utils.config import config, telegram_settings
from utils.telegram_alert import send_telegram_message

def main():
    logger = setup_logger()

    try:
        history, trade_log, summary = run_redhawk_strategy(config, logger)

        # Safe fetch values
        balance = summary.get("Final Balance") or summary.get("final_balance", 0)
        days = summary.get("Total Days") or summary.get("total_days", 0)
        trades = summary.get("Total Trades") or summary.get("total_trades", 0)


        # Prepare alert message
        msg = (
            f"✅ RedHawk Simulation Complete!\n\n"
            f"💰 Final Balance: ${balance:,.2f}\n"
            f"📆 Days: {days}\n"
            f"🔁 Trades: {trades}\n"
            f"💼 Mode: {config.get('mode', 'N/A').capitalize()}"

        )

        success = send_telegram_message(
            telegram_settings["bot_token"],
            telegram_settings["chat_id"],
            msg
        )

        if success:
            print("Telegram alert sent successfully!")
        else:
            print("Failed to send Telegram message.")

    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"ERROR: {e}")

if __name__ == "__main__":
    main()
