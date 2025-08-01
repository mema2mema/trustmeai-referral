import pandas as pd
import matplotlib.pyplot as plt
import os

def generate_summary():
    if not os.path.exists("trade_log.csv"):
        return "No trades yet."
    df = pd.read_csv("trade_log.csv")
    total = df["pnl"].sum()
    trades = len(df)
    wins = (df["pnl"] > 0).sum()
    losses = (df["pnl"] <= 0).sum()
    return f"""📊 TrustMe AI Performance Summary:

Total Trades: {trades}
Wins: {wins}
Losses: {losses}
Net PnL: ${total:.2f}
Win Rate: {wins / trades * 100:.1f}%
"""

def generate_graph():
    if not os.path.exists("trade_log.csv"):
        return
    df = pd.read_csv("trade_log.csv")
    df["equity"] = df["pnl"].cumsum()
    plt.figure()
    plt.plot(df["equity"])
    plt.title("Equity Curve")
    plt.xlabel("Trades")
    plt.ylabel("PnL")
    plt.savefig("equity_curve.png")