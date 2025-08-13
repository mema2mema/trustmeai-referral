
import numpy as np, pandas as pd
def summarize_df(df: pd.DataFrame)->dict:
    out={}; n=len(df); out['trades']=int(n)
    if n==0:
        out.update({'wins':0,'losses':0,'win_rate':0.0,'net_pnl':0.0,'avg_win':0.0,'avg_loss':0.0,'max_drawdown':0.0,'profit_factor':0.0}); return out
    pnl=df['pnl'].fillna(0).astype(float); wins=pnl[pnl>0]; losses=pnl[pnl<0]
    net=float(pnl.sum()); win_rate=(len(wins)/n)*100.0
    avg_win=float(wins.mean()) if len(wins) else 0.0; avg_loss=float(losses.mean()) if len(losses) else 0.0
    cum=pnl.cumsum(); running_max=cum.cummax(); dd=cum-running_max; max_dd=float(dd.min()) if not dd.empty else 0.0
    gp=float(wins.sum()) if len(wins) else 0.0; gl=float(-losses.sum()) if len(losses) else 0.0
    pf=(gp/gl) if gl>0 else 0.0
    out.update({'wins':int((pnl>0).sum()),'losses':int((pnl<0).sum()),'win_rate':float(win_rate),'net_pnl':net,'avg_win':avg_win,'avg_loss':avg_loss,'max_drawdown':max_dd,'profit_factor':float(pf)})
    return out

def build_summary_text(df: pd.DataFrame, meta: dict)->str:
    s=summarize_df(df); hints=[]
    if s['profit_factor']<1.2: hints.append('Low profit factor; tighten stops or improve entries.')
    if s['win_rate']<50: hints.append('Win rate < 50%; review trade quality and R:R.')
    if abs(s['max_drawdown'])>abs(s['net_pnl'])*0.6: hints.append('Drawdown is large vs profits; reduce size or diversify.')
    if s['trades']<20: hints.append('Small sample; collect more trades.')
    text=(f"<b>Performance Summary</b>\nFile: <code>{meta.get('path','')}</code>\n"
          f"Trades: <b>{s['trades']}</b>\nWin Rate: <b>{s['win_rate']:.2f}%</b>\nNet PnL: <b>{s['net_pnl']:.2f}</b>\n"
          f"Avg Win: <code>{s['avg_win']:.2f}</code> | Avg Loss: <code>{s['avg_loss']:.2f}</code>\n"
          f"Max Drawdown: <code>{s['max_drawdown']:.2f}</code>\nProfit Factor: <b>{s['profit_factor']:.2f}</b>")
    if hints: text += "\n\n<b>Insights</b>\n" + "\n".join([f"• {h}" for h in hints])
    return text
