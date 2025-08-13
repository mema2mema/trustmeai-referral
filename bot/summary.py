import numpy as np
import pandas as pd

def summarize_df(df: pd.DataFrame) -> dict:
    out = {}
    n = len(df)
    out["trades"] = int(n)
    if n == 0:
        out.update({
            "wins": 0, "losses": 0, "win_rate": 0.0, "net_pnl": 0.0,
            "avg_win": 0.0, "avg_loss": 0.0, "max_drawdown": 0.0, "profit_factor": 0.0
        })
        return out

    pnl = df["pnl"].fillna(0).astype(float)
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]

    net = pnl.sum()
    win_rate = (len(wins) / n) * 100.0
    avg_win = wins.mean() if len(wins) else 0.0
    avg_loss = losses.mean() if len(losses) else 0.0
    cum = pnl.cumsum()
    running_max = cum.cummax()
    drawdown = cum - running_max
    max_dd = drawdown.min() if not drawdown.empty else 0.0
    gross_profit = wins.sum() if len(wins) else 0.0
    gross_loss = -losses.sum() if len(losses) else 0.0
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else np.inf

    out.update({
        "wins": int((pnl > 0).sum()),
        "losses": int((pnl < 0).sum()),
        "win_rate": float(win_rate),
        "net_pnl": float(net),
        "avg_win": float(avg_win if not np.isnan(avg_win) else 0.0),
        "avg_loss": float(avg_loss if not np.isnan(avg_loss) else 0.0),
        "max_drawdown": float(max_dd),
        "profit_factor": float(profit_factor if np.isfinite(profit_factor) else 0.0)
    })
    return out

def build_summary_text(df: pd.DataFrame, meta: dict) -> str:
    s = summarize_df(df)
    hints = []

    if s["profit_factor"] < 1.2:
        hints.append("Low profit factor; consider tightening stops or improving entry filters.")
    if s["win_rate"] < 50:
        hints.append("Win rate below 50%; review trade quality and risk-reward ratio.")
    if abs(s["max_drawdown"]) > abs(s["net_pnl"])*0.6:
        hints.append("Drawdown is large relative to profits; reduce position size or add diversification.")
    if s["trades"] < 20:
        hints.append("Sample size is small; collect more trades for reliable stats.")

    text = (
        f"<b>Performance Summary</b>\n"
        f"File: <code>{meta.get('path','')}</code>\n"
        f"Trades: <b>{s['trades']}</b>\n"
        f"Win Rate: <b>{s['win_rate']:.2f}%</b>\n"
        f"Net PnL: <b>{s['net_pnl']:.2f}</b>\n"
        f"Avg Win: <code>{s['avg_win']:.2f}</code> | Avg Loss: <code>{s['avg_loss']:.2f}</code>\n"
        f"Max Drawdown: <code>{s['max_drawdown']:.2f}</code>\n"
        f"Profit Factor: <b>{s['profit_factor']:.2f}</b>\n"
    )
    if hints:
        text += "\n<b>Insights</b>\n" + "\n".join([f"• {h}" for h in hints])
    return text
