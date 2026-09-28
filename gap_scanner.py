"""
ماسح نموذج الـ Inversion Gap - فريم 4 ساعات - أسهم ناسداك 100
-----------------------------------------------------------------
النموذج:
  1) ثلاث شموع حمراء متتالية (C1, C2, C3)
  2) جاب بين قاع الشمعة الأولى وقمة الشمعة الثالثة (ما التقوا)
       أسفل الجاب = قمة C3      أعلى الجاب = قاع C1
  3) شمعة رابعة خضراء (C4) ترتد وتحاول تلمس أعلى الجاب
  => يرسل تنبيه على تيليجرام أول ما C4 تلمس أعلى الجاب (حتى وهي لسه تتكون)

الفلتر: السهم سعره بين 50 و 500 دولار فقط.

التشغيل:
  pip install yfinance pandas requests lxml
  python gap_scanner.py          # يشتغل باستمرار ويفحص كل 5 دقايق
  python gap_scanner.py --once   # فحص مرة وحدة بس
"""

import io
import os
import sys
import time
from datetime import datetime

import pandas as pd
import requests

# ================== الإعدادات ==================
# على السيرفر تنحط كمتغيرات (Variables) عشان ما تنكشف في جيتهب
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "ضع_توكن_البوت_هنا")      # من @BotFather
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "ضع_رقم_المحادثة_هنا")  # من @userinfobot

MIN_PRICE = 50
MAX_PRICE = 500

TOUCH_TOLERANCE = 0.001     # 0.1% : يعتبرها لمست لو قربت من أعلى الجاب بهالنسبة
CHECK_EVERY_MIN = 5         # كل كم دقيقة يفحص
REQUIRE_GREEN_FOURTH = True # الشمعة الرابعة لازم تكون خضراء
ONLY_MARKET_HOURS = True    # يفحص بس وقت السوق الأمريكي
# ===============================================

# قائمة احتياطية لو ما قدر يجيب قائمة ناسداك 100 من النت
FALLBACK_TICKERS = """
AAPL MSFT NVDA AMZN META GOOGL GOOG AVGO TSLA COST NFLX AMD PEP ADBE CSCO TMUS
QCOM INTU TXN AMGN ISRG CMCSA HON BKNG AMAT VRTX ADP PANW GILD SBUX MU ADI LRCX
MELI REGN MDLZ KLAC INTC SNPS CDNS PYPL CRWD MAR CTAS ORLY ASML CEG ABNB FTNT
CSX MRVL ADSK PCAR ROP WDAY NXPI CPRT CHTR MNST PAYX AEP ODFL FAST KDP ROST DDOG
TTD EA BKR KHC VRSK EXC XEL CTSH GEHC LULU IDXX CCEP FANG DXCM TEAM ON ZS CSGP
BIIB CDW MDB GFS WBD ARM DASH PLTR APP MSTR AZN LIN TRI SHOP AXON
""".split()


def get_nasdaq100():
    """يجيب قائمة ناسداك 100 الحالية من ويكيبيديا، ولو فشل يستخدم الاحتياطية."""
    try:
        html = requests.get(
            "https://en.wikipedia.org/wiki/Nasdaq-100",
            headers={"User-Agent": "Mozilla/5.0"}, timeout=15,
        ).text
        for t in pd.read_html(io.StringIO(html)):
            for col in ("Ticker", "Symbol"):
                if col in t.columns and len(t) > 90:
                    return [s.replace(".", "-").strip() for s in t[col].astype(str)]
    except Exception as e:
        print("ما قدرت أجيب القائمة من النت، أستخدم الاحتياطية:", e)
    return FALLBACK_TICKERS


def to_4h(df):
    """يحول شموع الساعة لشموع 4 ساعات بنفس تقسيم تريدنج فيو للأسهم الأمريكية
    (9:30 - 13:30 ثم 13:30 - 16:00 بتوقيت نيويورك)."""
    df = df.dropna(subset=["Open", "High", "Low", "Close"])
    if df.empty:
        return df
    idx = df.index
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
    df = df.set_index(idx.tz_convert("America/New_York"))
    df = df.between_time("09:30", "15:59")
    mins = df.index.hour * 60 + df.index.minute - 570
    block = mins // 240
    start = df.index.normalize() + pd.Timedelta(minutes=570) + pd.to_timedelta(block * 240, unit="m")
    return df.groupby(start).agg(
        {"Open": "first", "High": "max", "Low": "min", "Close": "last"}
    )


def check_pattern(c):
    """يفحص آخر 4 شموع. يرجع تفاصيل النموذج لو تحقق، وإلا None."""
    if len(c) < 4:
        return None
    c1, c2, c3, c4 = (c.iloc[i] for i in (-4, -3, -2, -1))

    def red(x):
        return x["Close"] < x["Open"]

    if not (red(c1) and red(c2) and red(c3)):
        return None

    gap_bottom = c3["High"]  # قمة الشمعة الثالثة
    gap_top = c1["Low"]      # قاع الشمعة الأولى
    if gap_bottom >= gap_top:  # ما فيه جاب
        return None

    if REQUIRE_GREEN_FOURTH and not (c4["Close"] > c4["Open"]):
        return None

    if c4["High"] >= gap_top * (1 - TOUCH_TOLERANCE):
        return {
            "gap_bottom": round(float(gap_bottom), 2),
            "gap_top": round(float(gap_top), 2),
            "price": round(float(c4["Close"]), 2),
            "candle_time": c.index[-1],
        }
    return None


def send_telegram(text):
    print(text)
    if "ضع_" in TELEGRAM_TOKEN:
        return  # ما حطيت التوكن، يطبع بالشاشة بس
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=10,
        )
    except Exception as e:
        print("فشل إرسال التنبيه:", e)


def market_open():
    now = pd.Timestamp.now(tz="America/New_York")
    if now.weekday() >= 5:
        return False
    return now.replace(hour=9, minute=30) <= now <= now.replace(hour=16, minute=5)


def scan(tickers, already_sent):
    import yfinance as yf

    data = yf.download(
        tickers, period="30d", interval="1h", group_by="ticker",
        prepost=False, progress=False, threads=True, auto_adjust=False,
    )
    hits = 0
    for t in tickers:
        try:
            df = data[t] if isinstance(data.columns, pd.MultiIndex) else data
            candles = to_4h(df)
            if candles.empty:
                continue
            last = float(candles["Close"].iloc[-1])
            if not (MIN_PRICE <= last <= MAX_PRICE):
                continue
            res = check_pattern(candles)
            if not res:
                continue
            key = f"{t}-{res['candle_time']}"
            if key in already_sent:
                continue
            already_sent.add(key)
            hits += 1
            send_telegram(
                f"🔔 Inversion Gap - فريم 4 ساعات\n"
                f"السهم: {t}\n"
                f"السعر: {res['price']}\n"
                f"الجاب: {res['gap_bottom']} ← {res['gap_top']}\n"
                f"الشمعة الخضراء لمست أعلى الجاب"
            )
        except Exception as e:
            print(f"{t}: خطأ - {e}")
    print(f"[{datetime.now():%H:%M}] خلص الفحص - {hits} تنبيه جديد")


def main():
    tickers = get_nasdaq100()
    print(f"عدد الأسهم: {len(tickers)} (الفلتر {MIN_PRICE}-{MAX_PRICE}$ يتطبق وقت الفحص)")
    sent = set()
    once = "--once" in sys.argv
    while True:
        if not ONLY_MARKET_HOURS or market_open() or once:
            scan(tickers, sent)
        else:
            print(f"[{datetime.now():%H:%M}] السوق مسكر، أنتظر...")
        if once:
            break
        time.sleep(CHECK_EVERY_MIN * 60)


if __name__ == "__main__":
    main()
