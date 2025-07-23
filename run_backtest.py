from backtest import run_csv_backtest
import pandas as pd

history, trade_log, summary = run_csv_backtest("backtest.csv")

print("✅ Backtest Complete")
print(summary)

print("\n📊 Daily Summary:")
print(pd.DataFrame(history))

print("\n🧾 Trade Log:")
print(pd.DataFrame(trade_log))
