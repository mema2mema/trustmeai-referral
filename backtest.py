import pandas as pd

def run_csv_backtest(filepath, initial_investment=150):
    try:
        df = pd.read_csv(filepath)
        df = df.dropna()  # ✅ remove bad rows


        if not all(col in df.columns for col in ['day', 'trade', 'profit']):
            raise ValueError("CSV must contain 'day', 'trade', 'profit' columns")

        investment = initial_investment
        history = []

        for day in sorted(df['day'].unique()):
            day_data = df[df['day'] == day]
            start = investment

            for _, row in day_data.iterrows():
                investment += row['profit']

            history.append({
                "day": day,
                "start_balance": round(start, 2),
                "end_balance": round(investment, 2),
                "daily_profit": round(investment - start, 2)
            })

        summary = {
            "Starting Balance": initial_investment,
            "Final Balance": round(investment, 2),
            "Total Days": len(history),
            "Total Trades": len(df)
        }

        return history, df.to_dict(orient="records"), summary

    except Exception as e:
        print("❌ Backtest failed:", e)
        return [], [], {}
