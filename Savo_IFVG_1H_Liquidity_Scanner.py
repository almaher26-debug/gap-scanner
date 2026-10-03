#!/usr/bin/env python3
# Savo IFVG 1H Liquidity Scanner — Alpaca + Telegram
import os, time, json, requests
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pandas as pd

KEY=os.getenv("ALPACA_API_KEY","").strip()
SECRET=os.getenv("ALPACA_SECRET_KEY","").strip()
TOKEN=os.getenv("TELEGRAM_BOT_TOKEN","").strip()
CHAT=os.getenv("TELEGRAM_CHAT_ID","").strip()
FEED=os.getenv("ALPACA_FEED","iex").strip()
HEAD={"APCA-API-KEY-ID":KEY,"APCA-API-SECRET-KEY":SECRET}
DATA="https://data.alpaca.markets/v2"
TRADE="https://api.alpaca.markets/v2"
STATE=Path("ifvg_1h_sent.json")

def send(msg):
    r=requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id":CHAT,"text":msg},timeout=20); r.raise_for_status()

def sent_load():
    try:return set(json.loads(STATE.read_text()))
    except:return set()

def sent_save(s): STATE.write_text(json.dumps(sorted(s)[-20000:]))

def symbols():
    r=requests.get(f"{TRADE}/assets",headers=HEAD,
        params={"status":"active","asset_class":"us_equity"},timeout=30); r.raise_for_status()
    return sorted({x["symbol"] for x in r.json()
        if x.get("tradable") and x.get("exchange")=="NASDAQ" and "/" not in x.get("symbol","")})

def bars(batch,start,end):
    out={s:[] for s in batch}; token=None
    while True:
        p={"symbols":",".join(batch),"timeframe":"1Hour",
           "start":start.isoformat().replace("+00:00","Z"),
           "end":end.isoformat().replace("+00:00","Z"),
           "limit":10000,"adjustment":"raw","feed":FEED,"sort":"asc"}
        if token:p["page_token"]=token
        r=requests.get(f"{DATA}/stocks/bars",headers=HEAD,params=p,timeout=45)
        if r.status_code==429: time.sleep(10); continue
        r.raise_for_status(); q=r.json()
        for s,b in q.get("bars",{}).items():out.setdefault(s,[]).extend(b)
        token=q.get("next_page_token")
        if not token:break
    ans={}
    for s,b in out.items():
        if not b:continue
        d=pd.DataFrame(b); d["t"]=pd.to_datetime(d["t"],utc=True)
        d=d.rename(columns={"o":"open","h":"high","l":"low","c":"close","v":"volume"})
        ans[s]=d.drop_duplicates("t").sort_values("t").reset_index(drop=True)
    return ans

def sweep(d,i):
    # Liquidity = previous 20 hourly lows; setup must sweep it and close back above.
    a=max(0,i-22); z=i-2
    if z<=a:return False,None
    old=d.iloc[a:z]
    if len(old)<5:return False,None
    L=float(old.low.min()); setup=d.iloc[max(0,i-2):i+1]
    return (float(setup.low.min())<=L*1.003 and float(setup.iloc[-1].close)>L),L

def signals(d,cutoff):
    out=[]
    for i in range(2,len(d)-1):
        left=d.iloc[i-2]; right=d.iloc[i]
        # User condition: left candle green.
        if not left.close>left.open:continue
        # Original bearish FVG; later close above it = bullish IFVG.
        lo=float(right.high); hi=float(left.low)
        if not lo<hi:continue
        ok,L=sweep(d,i)
        if not ok:continue
        for j in range(i+1,len(d)):
            c=d.iloc[j]
            if float(c.close)>hi:
                t=c.t.to_pydatetime()
                if t>=cutoff:
                    out.append({"t":t,"fvg":right.t.to_pydatetime(),"lo":lo,"hi":hi,
                                "liq":L,"close":float(c.close)})
                break
    return out

def sid(sym,x):return f'{sym}|{x["t"].isoformat()}|{x["lo"]:.6f}|{x["hi"]:.6f}'

def message(sym,x,mode):
    return (f"🚨 1H LIQUIDITY IFVG — {mode}\n"
            f"Symbol: {sym}\n"
            f"Confirmed: {x['t']:%Y-%m-%d %H:%M UTC}\n"
            f"IFVG zone: {x['lo']:.4f} — {x['hi']:.4f}\n"
            f"Liquidity low: {x['liq']:.4f}\n"
            f"Close: {x['close']:.4f}\n"
            "✓ left candle green\n✓ liquidity sweep\n✓ bullish IFVG")

def scan(syms,cutoff,mode,sent):
    now=datetime.now(timezone.utc); start=now-timedelta(days=14); found=[]
    for k in range(0,len(syms),100):
        batch=syms[k:k+100]
        try:
            for sym,d in bars(batch,start,now).items():
                for x in signals(d,cutoff):
                    q=sid(sym,x)
                    if q not in sent:found.append((x["t"],sym,x,q))
        except Exception as e: print("Batch error:",e)
        time.sleep(.25)
    found.sort()
    for _,sym,x,q in found:
        send(message(sym,x,mode)); sent.add(q); sent_save(sent); time.sleep(.35)
    return len(found)

def main():
    if not all([KEY,SECRET,TOKEN,CHAT]):
        raise SystemExit("Set ALPACA_API_KEY, ALPACA_SECRET_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID")
    syms=symbols(); sent=sent_load()
    send("✅ Savo IFVG 1H scanner started — scanning previous 7 days.")
    n=scan(syms,datetime.now(timezone.utc)-timedelta(days=7),"LAST 7 DAYS",sent)
    send(f"✅ Historical scan finished. Alerts sent: {n}")
    while True:
        scan(syms,datetime.now(timezone.utc)-timedelta(hours=3),"LIVE",sent)
        time.sleep(300)

if __name__=="__main__": main()
