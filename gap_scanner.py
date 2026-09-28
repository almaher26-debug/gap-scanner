"""
بوت التنبيهات - يشتغل على Railway ويرسل على تيليجرام
=====================================================

(1) نموذج الـ Inversion Gap - فريم 4 ساعات - أسهم ناسداك 100 (سعر 50 إلى 500$)
    - ثلاث شموع حمراء (C1, C2, C3) وقمة الثالثة ما وصلت قاع الأولى (جاب)
    - شمعة رابعة خضراء تلمس أعلى الجاب  =>  تنبيه

(2) سيولة داخلة على الأسهم الصغيرة - فريم 5 دقايق (سعر 1 إلى 12$)
    - كل الأسهم الأمريكية (ناسداك + نيويورك) اللي سعرها بين 1 و 12 دولار
    - إذا شمعة 5 دقايق وحدة دخلها 200 ألف دولار أو أكثر  =>  تنبيه
      (السيولة = سعر السهم × عدد الأسهم المتداولة في الشمعة)

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

CHECK_EVERY_MIN = 5          # كل كم دقيقة يفحص
ONLY_MARKET_HOURS = True     # يفحص بس وقت السوق الأمريكي
INCLUDE_EXTENDED = True      # يفحص كمان قبل الفتح وبعد الإغلاق (4 الصبح - 8 بالليل نيويورك)

# ---- (1) نموذج الجاب ----
ENABLE_GAP = True
MIN_PRICE = 50
MAX_PRICE = 500
TOUCH_TOLERANCE = 0.001      # 0.1% : يعتبرها لمست لو قربت من أعلى الجاب بهالنسبة
REQUIRE_GREEN_FOURTH = True  # الشمعة الرابعة لازم تكون خضراء
GAP_EXTENDED = True          # شمعة الـ4 ساعات تشمل ما قبل الفتح وبعد الإغلاق (4-8، 8-12، 12-4، 4-8)

# ---- (2) سيولة الأسهم الصغيرة ----
ENABLE_PENNY = True
PENNY_MIN_PRICE = 1
PENNY_MAX_PRICE = 12
PENNY_MIN_DOLLARS = 200_000     # أقل سيولة في شمعة الـ 5 دقايق عشان يرسل تنبيه
PENNY_ONLY_GREEN = False        # True = ينبه بس إذا الشمعة خضراء (شراء)
PENNY_COOLDOWN_MIN = 30         # ما يكرر تنبيه نفس السهم قبل هالمدة (دقايق)
PENNY_MIN_AVG_VOLUME = 200_000  # فلتر مبدئي: متوسط التداول اليومي (عدد أسهم) عشان نخفف القائمة
PENNY_INCLUDE_NYSE = True       # يضيف أسهم بورصة نيويورك مع ناسداك
# ===============================================

NY = "America/New_York"

# قائمة احتياطية لو ما قدر يجيب قائمة ناسداك 100 من النت
FALLBACK_TICKERS = """
AAPL MSFT NVDA AMZN META GOOGL GOOG AVGO TSLA COST NFLX AMD PEP ADBE CSCO TMUS
QCOM INTU TXN AMGN ISRG CMCSA HON BKNG AMAT VRTX ADP PANW GILD SBUX MU ADI LRCX
MELI REGN MDLZ KLAC INTC SNPS CDNS PYPL CRWD MAR CTAS ORLY ASML CEG ABNB FTNT
CSX MRVL ADSK PCAR ROP WDAY NXPI CPRT CHTR MNST PAYX AEP ODFL FAST KDP ROST DDOG
TTD BKR KHC VRSK EXC XEL CTSH GEHC LULU IDXX CCEP FANG DXCM TEAM ON ZS CSGP
BIIB CDW MDB GFS WBD ARM DASH PLTR APP MSTR AZN LIN TRI SHOP AXON
""".split()


# ================== أدوات عامة ==================
def log(*a):
    print(*a, flush=True)


def send_telegram(text):
    log(text)
    if "ضع_" in TELEGRAM_TOKEN:
        return  # ما حطيت التوكن، يطبع بالشاشة بس
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=10,
        )
    except Exception as e:
        log("فشل إرسال التنبيه:", e)


def market_open():
    now = pd.Timestamp.now(tz=NY)
    if now.weekday() >= 5:
        return False
    if INCLUDE_EXTENDED:
        return now.replace(hour=4, minute=0) <= now <= now.replace(hour=20, minute=5)
    return now.replace(hour=9, minute=30) <= now <= now.replace(hour=16, minute=5)


def download_batches(tickers, batch_size, **kw):
    """يحمّل بيانات ياهو على دفعات، ويرجع (الرمز، البيانات) لكل سهم."""
    import yfinance as yf

    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i + batch_size]
        try:
            data = yf.download(batch, group_by="ticker", progress=False,
                               threads=True, auto_adjust=False, **kw)
        except Exception as e:
            log("فشل تحميل دفعة:", e)
            time.sleep(5)
            continue
        for t in batch:
            try:
                if isinstance(data.columns, pd.MultiIndex):
                    if t not in data.columns.get_level_values(0):
                        continue
                    df = data[t]
                else:
                    df = data
                df = df.dropna(subset=["Open", "High", "Low", "Close"])
                if not df.empty:
                    yield t, df
            except Exception:
                continue
        time.sleep(1)


# ================== (1) نموذج الجاب ==================
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
        log("ما قدرت أجيب قائمة ناسداك 100، أستخدم الاحتياطية:", e)
    return FALLBACK_TICKERS


def to_4h(df):
    """يحول شموع الساعة لشموع 4 ساعات بتوقيت نيويورك.
    السوق الممتد: 4-8، 8-12، 12-16، 16-20  (نفس تريدنج فيو مع تفعيل Extended Hours)
    السوق الرسمي: 9:30 - 13:30 ثم 13:30 - 16:00"""
    df = df.dropna(subset=["Open", "High", "Low", "Close"])
    if df.empty:
        return df
    idx = df.index
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
    df = df.set_index(idx.tz_convert(NY))
    first = 240 if GAP_EXTENDED else 570          # 4:00 أو 9:30 بالدقايق
    df = df.between_time("04:00", "19:59") if GAP_EXTENDED else df.between_time("09:30", "15:59")
    mins = df.index.hour * 60 + df.index.minute - first
    block = mins // 240
    start = df.index.normalize() + pd.Timedelta(minutes=first) + pd.to_timedelta(block * 240, unit="m")
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


def scan_gap(tickers, already_sent):
    hits = 0
    for t, df in download_batches(tickers, 100, period="30d", interval="1h", prepost=GAP_EXTENDED):
        try:
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
            log(f"{t}: خطأ - {e}")
    log(f"[{datetime.now():%H:%M}] الجاب: خلص الفحص - {hits} تنبيه جديد")


# ================== (2) سيولة الأسهم الصغيرة ==================
def get_all_us_symbols():
    """كل الأسهم المدرجة في ناسداك (وبورصة نيويورك) من ملفات ناسداك الرسمية،
    بدون صناديق ETF ولا وارنتات ولا حقوق ولا وحدات."""
    base = "https://www.nasdaqtrader.com/dynamic/SymDir/"
    bad_name = r"Warrant|Right|Unit|Preferred|Depositary Shares|Notes|Debenture|%"
    symbols = set()

    def read(fname):
        txt = requests.get(base + fname, headers={"User-Agent": "Mozilla/5.0"}, timeout=30).text
        df = pd.read_csv(io.StringIO(txt), sep="|", dtype=str)
        return df[~df.iloc[:, 0].str.startswith("File Creation", na=False)]

    try:
        n = read("nasdaqlisted.txt")
        n = n[(n["Test Issue"] == "N") & (n["ETF"] == "N")]
        n = n[~n["Security Name"].str.contains(bad_name, case=False, na=False)]
        symbols.update(n["Symbol"].dropna())
    except Exception as e:
        log("ما قدرت أجيب قائمة ناسداك:", e)

    if PENNY_INCLUDE_NYSE:
        try:
            o = read("otherlisted.txt")
            o = o[(o["Test Issue"] == "N") & (o["ETF"] == "N")]
            o = o[~o["Security Name"].str.contains(bad_name, case=False, na=False)]
            symbols.update(o["ACT Symbol"].dropna())
        except Exception as e:
            log("ما قدرت أجيب قائمة نيويورك:", e)

    # نشيل الرموز الغريبة (فيها $ أو . أو = ...)
    return sorted(s for s in symbols if s.isalpha() and len(s) <= 5)


def build_penny_universe():
    """فلتر مبدئي مرة باليوم: الأسهم اللي آخر سعر لها بين 1 و 12 دولار
    ومتوسط تداولها اليومي كافي."""
    all_syms = get_all_us_symbols()
    log(f"الأسهم الصغيرة: أفحص {len(all_syms)} سهم عشان أطلع اللي سعرها {PENNY_MIN_PRICE}-{PENNY_MAX_PRICE}$ ...")
    keep = []
    for t, df in download_batches(all_syms, 400, period="5d", interval="1d", prepost=False):
        try:
            last = float(df["Close"].iloc[-1])
            avg_vol = float(df["Volume"].mean())
            if PENNY_MIN_PRICE <= last <= PENNY_MAX_PRICE and avg_vol >= PENNY_MIN_AVG_VOLUME:
                keep.append(t)
        except Exception:
            continue
    log(f"الأسهم الصغيرة: {len(keep)} سهم داخل الفلتر")
    return keep


def check_liquidity(df):
    """يفحص آخر شمعتين 5 دقايق. يرجع قائمة الشموع اللي دخلها سيولة كافية."""
    out = []
    for ts, row in df.tail(2).iterrows():
        price = float(row["Close"])
        vol = float(row.get("Volume", 0) or 0)
        dollars = price * vol
        if not (PENNY_MIN_PRICE <= price <= PENNY_MAX_PRICE):
            continue
        if dollars < PENNY_MIN_DOLLARS:
            continue
        green = row["Close"] >= row["Open"]
        if PENNY_ONLY_GREEN and not green:
            continue
        chg = (row["Close"] / row["Open"] - 1) * 100 if row["Open"] else 0
        out.append({"time": ts, "price": price, "vol": vol, "dollars": dollars,
                    "green": green, "chg": chg})
    return out


def scan_penny(tickers, last_alert):
    hits = 0
    now = time.time()
    for t, df in download_batches(tickers, 200, period="1d", interval="5m", prepost=INCLUDE_EXTENDED):
        try:
            for h in check_liquidity(df):
                if now - last_alert.get(t, 0) < PENNY_COOLDOWN_MIN * 60:
                    break
                last_alert[t] = now
                hits += 1
                ts = h["time"]
                ts = ts.tz_convert(NY) if ts.tzinfo else ts
                icon = "🟢" if h["green"] else "🔴"
                send_telegram(
                    f"💰 سيولة داخلة - سهم صغير (فريم 5 دقايق)\n"
                    f"السهم: {t}\n"
                    f"السعر: {h['price']:.2f}  {icon} {h['chg']:+.1f}% في الشمعة\n"
                    f"السيولة في الشمعة: {h['dollars']:,.0f}$\n"
                    f"عدد الأسهم: {h['vol']:,.0f}\n"
                    f"وقت الشمعة: {ts:%H:%M} (نيويورك)"
                )
                break
        except Exception as e:
            log(f"{t}: خطأ - {e}")
    log(f"[{datetime.now():%H:%M}] السيولة: خلص الفحص - {hits} تنبيه جديد")


# ================== التشغيل ==================
def main():
    once = "--once" in sys.argv
    gap_tickers = get_nasdaq100() if ENABLE_GAP else []
    if ENABLE_GAP:
        log(f"الجاب: {len(gap_tickers)} سهم (الفلتر {MIN_PRICE}-{MAX_PRICE}$ يتطبق وقت الفحص)")

    gap_sent = set()
    penny_last = {}
    penny_tickers, penny_day = [], None

    while True:
        if not ONLY_MARKET_HOURS or market_open() or once:
            if ENABLE_GAP:
                scan_gap(gap_tickers, gap_sent)
            if ENABLE_PENNY:
                today = pd.Timestamp.now(tz=NY).date()
                if penny_day != today or not penny_tickers:
                    penny_tickers = build_penny_universe()
                    penny_day = today
                scan_penny(penny_tickers, penny_last)
        else:
            log(f"[{datetime.now():%H:%M}] السوق مسكر، أنتظر...")
        if once:
            break
        time.sleep(CHECK_EVERY_MIN * 60)


if __name__ == "__main__":
    main()
