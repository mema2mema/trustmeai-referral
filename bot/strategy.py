import random

def run_redhawk_strategy(config, logger):
    logger.info("Starting RedHawk Simulation...")

    investment = config["initial_investment"]
    days = config["days"]
    profit_percent = config["daily_profit_percent"]
    trades_per_day = config["trades_per_day"]
    mode = config["mode"].lower()
    cap_limit = config.get("cap_limit", None)
    realism = config.get("realism", True)

    history = []
    trade_log = []
    day = 0

    while day < days:
        day += 1
        daily_summary = {"day": day, "start_balance": investment}

        for trade in range(trades_per_day):
            if realism:
                # Inject some realism: ±15% variation, possible losses
                rand_factor = random.uniform(0.85, 1.15)
                profit = investment * (profit_percent / 100) / trades_per_day * rand_factor

                # Random chance to lose
                if random.random() < 0.15:  # 15% chance of loss
                    profit *= -random.uniform(0.5, 1.0)
            else:
                # Pure compounding
                profit = investment * (profit_percent / 100) / trades_per_day

            trade_log.append({
                "day": day,
                "trade": trade + 1,
                "profit": round(profit, 2)
            })

            if mode == "reinvest":
                investment += profit

        daily_summary["end_balance"] = investment
        history.append(daily_summary)

        if cap_limit and investment >= cap_limit:
            logger.info("Cap limit reached!")
            break

    summary = {
        "Final Balance": round(investment, 2),
        "Total Days": day,
        "Total Trades": len(trade_log)
    }

    return history, trade_log, summary
