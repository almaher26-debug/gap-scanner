"""
بوت التنبيهات - يشتغل على Railway ويرسل على تيليجرام
=====================================================

(1) نموذج الـ Inversion Gap - فريم 4 ساعات
    الأسهم: كل أسهم ناسداك اللي قيمتها السوقية 2 مليار دولار وفوق (ميد كاب وأعلى)
    ⚠️ لون الشموع الثلاث ما يهم - المهم إن ذيل الشمعة الأولى والثالثة ما يلتقون

    🟢 صعودي (جاب تحت):
      - ثلاث شموع (أي لون)، وقاع الشمعة الأولى أعلى من قمة الشمعة الثالثة
      - الجاب = من قمة الشمعة الثالثة (تحت) إلى قاع الشمعة الأولى (فوق)
      - الشمعة الرابعة تجي من تحت وتطلع لين تلمس أعلى الجاب (قاع C1)  =>  تنبيه فوراً

    🔴 هبوطي (جاب فوق):
      - ثلاث شموع (أي لون)، وقمة الشمعة الأولى أقل من قاع الشمعة الثالثة
      - الجاب = من قمة الشمعة الأولى (تحت) إلى قاع الشمعة الثالثة (فوق)
      - الشمعة الرابعة تجي من فوق وتنزل لين تلمس أسفل الجاب (قمة C1)  =>  تنبيه فوراً

(2) فلتر الأخبار
    - كل الأسهم الأمريكية (ناسداك + نيويورك) اللي سعرها من 1 إلى 10 دولار
    - أي خبر ينزل من 11:00 الصبح إلى 4:30 العصر (توقيتك المحلي - الرياض)  =>  تنبيه
    - المصدر: ياهو فاينانس

التشغيل:
  pip install yfinance pandas requests lxml
  python gap_scanner.py          # يشتغل باستمرار ويفحص كل 5 دقايق
  python gap_scanner.py --once   # فحص مرة وحدة بس
"""

import io
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import pandas as pd
import requests

# ================== الإعدادات ==================
# على السيرفر تنحط كمتغيرات (Variables) عشان ما تنكشف في جيتهب
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "ضع_توكن_البوت_هنا")      # من @BotFather
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "ضع_رقم_المحادثة_هنا")  # من @userinfobot

CHECK_EVERY_MIN = 5          # كل كم دقيقة يفحص
NY = "America/New_York"
LOCAL_TZ = "Asia/Riyadh"     # توقيتك المحلي

# ---- (1) نموذج الجاب ----
ENABLE_GAP = True
MIN_MARKET_CAP = 2_000_000_000   # 2 مليار دولار = ميد كاب وفوق
ENABLE_BULLISH = True            # جاب تحت + شمعة تطلع وتلمس أعلى الجاب
ENABLE_BEARISH = True            # جاب فوق + شمعة تنزل وتلمس أسفل الجاب
REQUIRE_FOURTH_COLOR = False     # True = الرابعة لازم خضراء بالصعودي وحمراء بالهبوطي
                                 # False = ينبه أول ما تلمس الخط حتى لو الشمعة ما قفلت
TOUCH_TOLERANCE = 0.001          # 0.1% : يعتبرها لمست لو قربت من حد الجاب بهالنسبة
GAP_EXTENDED = True              # شمعة الـ4 ساعات تشمل ما قبل الفتح وبعد الإغلاق (4-8، 8-12، 12-4، 4-8)

USE_PRICE_FILTER = False         # True = يطبق فلتر السعر تحت مع فلتر القيمة السوقية
MIN_PRICE = 50
MAX_PRICE = 500

# ---- (2) فلتر الأخبار ----
ENABLE_NEWS = True
NEWS_MIN_PRICE = 1
NEWS_MAX_PRICE = 10
NEWS_START = "11:00"             # بداية الوقت (توقيتك المحلي)
NEWS_END = "16:30"               # نهاية الوقت (توقيتك المحلي)
NEWS_MIN_AVG_VOLUME = 100_000    # يشيل الأسهم الميتة اللي ما عليها تداول (عدد أسهم يومي)
NEWS_INCLUDE_NYSE = True         # يضيف أسهم بورصة نيويورك مع ناسداك
NEWS_WORKERS = 8                 # عدد الطلبات المتوازية على ياهو
# ===============================================

HEADERS = {"User-Agent": "Mozilla/5.0"}

# قائمة احتياطية لو ما قدر يجيب القيم السوقية من النت
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
            data={"chat_id": TELEGRAM_CHAT_ID, "text": text,
                  "disable_web_page_preview": True},
            timeout=10,
        )
    except Exception as e:
        log("فشل إرسال التنبيه:", e)


def us_market_open():
    """السوق الأمريكي شامل ما قبل الفتح وبعد الإغلاق (4 الصبح - 8 بالليل نيويورك)."""
    now = pd.Timestamp.now(tz=NY)
    if now.weekday() >= 5:
        return False
    if GAP_EXTENDED:
        return now.replace(hour=4, minute=0) <= now <= now.replace(hour=20, minute=5)
    return now.replace(hour=9, minute=30) <= now <= now.replace(hour=16, minute=5)


def news_window():
    """يرجع (بداية، نهاية) نافذة الأخبار لليوم بتوقيتك، أو None لو برا الوقت."""
    now = pd.Timestamp.now(tz=LOCAL_TZ)
    if now.weekday() in (5, 6):  # السبت والأحد السوق الأمريكي مسكر
        return None
    h1, m1 = map(int, NEWS_START.split(":"))
    h2, m2 = map(int, NEWS_END.split(":"))
    start = now.replace(hour=h1, minute=m1, second=0, microsecond=0)
    end = now.replace(hour=h2, minute=m2, second=0, microsecond=0)
    if start <= now <= end:
        return start, end
    return None


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
def _to_number(x):
    try:
        return float(str(x).replace("$", "").replace(",", "").strip())
    except Exception:
        return 0.0


def get_nasdaq_midcap_plus():
    """كل أسهم ناسداك اللي قيمتها السوقية فوق الحد، من سكرينر ناسداك الرسمي."""
    url = ("https://api.nasdaq.com/api/screener/stocks"
           "?tableonly=true&limit=10000&exchange=nasdaq&download=true")
    try:
        r = requests.get(url, headers={**HEADERS, "Accept": "application/json"}, timeout=30)
        data = r.json().get("data") or {}
        rows = data.get("rows") or (data.get("table") or {}).get("rows") or []
        out = []
        for row in rows:
            sym = str(row.get("symbol", "")).strip().upper()
            cap = _to_number(row.get("marketCap"))
            if sym.isalpha() and len(sym) <= 5 and cap >= MIN_MARKET_CAP:
                out.append(sym)
        if len(out) > 50:
            return sorted(set(out))
        log("قائمة ناسداك رجعت فاضية تقريباً، أستخدم الاحتياطية")
    except Exception as e:
        log("ما قدرت أجيب القيم السوقية من ناسداك، أستخدم الاحتياطية:", e)
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


def red(x):
    return x["Close"] < x["Open"]


def green(x):
    return x["Close"] > x["Open"]


def check_pattern(c):
    """يفحص آخر 4 شموع بالاتجاهين. يرجع تفاصيل النموذج لو تحقق، وإلا None.
    الشمعة الرابعة هي الشمعة الحالية (لسا ما قفلت) عشان التنبيه يطلع أول ما تلمس."""
    if len(c) < 4:
        return None
    c1, c2, c3, c4 = (c.iloc[i] for i in (-4, -3, -2, -1))

    # 🟢 صعودي: قاع الأولى فوق قمة الثالثة (الذيول ما تلتقي) - لون الشموع ما يهم
    if ENABLE_BULLISH and c1["Low"] > c3["High"]:
        gap_bottom = c3["High"]   # قمة الشمعة الثالثة
        gap_top = c1["Low"]       # قاع الشمعة الأولى = الخط المطلوب
        came_from_below = c4["Open"] < gap_top
        touched = c4["High"] >= gap_top * (1 - TOUCH_TOLERANCE)
        color_ok = green(c4) or not REQUIRE_FOURTH_COLOR
        if came_from_below and touched and color_ok:
            return {"side": "bull", "gap_bottom": gap_bottom, "gap_top": gap_top,
                    "price": c4["Close"], "candle_time": c.index[-1]}

    # 🔴 هبوطي: قمة الأولى تحت قاع الثالثة (الذيول ما تلتقي) - لون الشموع ما يهم
    if ENABLE_BEARISH and c1["High"] < c3["Low"]:
        gap_bottom = c1["High"]   # قمة الشمعة الأولى = الخط المطلوب
        gap_top = c3["Low"]       # قاع الشمعة الثالثة
        came_from_above = c4["Open"] > gap_bottom
        touched = c4["Low"] <= gap_bottom * (1 + TOUCH_TOLERANCE)
        color_ok = red(c4) or not REQUIRE_FOURTH_COLOR
        if came_from_above and touched and color_ok:
            return {"side": "bear", "gap_bottom": gap_bottom, "gap_top": gap_top,
                    "price": c4["Close"], "candle_time": c.index[-1]}

    return None


def scan_gap(tickers, already_sent):
    hits = 0
    for t, df in download_batches(tickers, 100, period="30d", interval="1h", prepost=GAP_EXTENDED):
        try:
            candles = to_4h(df)
            if candles.empty:
                continue
            if USE_PRICE_FILTER:
                last = float(candles["Close"].iloc[-1])
                if not (MIN_PRICE <= last <= MAX_PRICE):
                    continue
            res = check_pattern(candles)
            if not res:
                continue
            key = f"{t}-{res['side']}-{res['candle_time']}"
            if key in already_sent:
                continue
            already_sent.add(key)
            hits += 1
            lo, hi, px = (round(float(res[k]), 2) for k in ("gap_bottom", "gap_top", "price"))
            if res["side"] == "bull":
                send_telegram(
                    f"🟢 Inversion Gap صعودي - فريم 4 ساعات\n"
                    f"السهم: {t}\n"
                    f"السعر: {px}\n"
                    f"الجاب: {lo} ← {hi}\n"
                    f"الشمعة طلعت ولمست أعلى الجاب ({hi})"
                )
            else:
                send_telegram(
                    f"🔴 Inversion Gap هبوطي - فريم 4 ساعات\n"
                    f"السهم: {t}\n"
                    f"السعر: {px}\n"
                    f"الجاب: {lo} ← {hi}\n"
                    f"الشمعة نزلت ولمست أسفل الجاب ({lo})"
                )
        except Exception as e:
            log(f"{t}: خطأ - {e}")
    log(f"[{datetime.now():%H:%M}] الجاب: خلص الفحص - {hits} تنبيه جديد")


# ================== (2) فلتر الأخبار ==================
def get_all_us_symbols():
    """كل الأسهم المدرجة في ناسداك (وبورصة نيويورك) من ملفات ناسداك الرسمية،
    بدون صناديق ETF ولا وارنتات ولا حقوق ولا وحدات."""
    base = "https://www.nasdaqtrader.com/dynamic/SymDir/"
    bad_name = r"Warrant|Right|Unit|Preferred|Depositary Shares|Notes|Debenture|%"
    symbols = set()

    def read(fname):
        txt = requests.get(base + fname, headers=HEADERS, timeout=30).text
        df = pd.read_csv(io.StringIO(txt), sep="|", dtype=str)
        return df[~df.iloc[:, 0].str.startswith("File Creation", na=False)]

    try:
        n = read("nasdaqlisted.txt")
        n = n[(n["Test Issue"] == "N") & (n["ETF"] == "N")]
        n = n[~n["Security Name"].str.contains(bad_name, case=False, na=False)]
        symbols.update(n["Symbol"].dropna())
    except Exception as e:
        log("ما قدرت أجيب قائمة ناسداك:", e)

    if NEWS_INCLUDE_NYSE:
        try:
            o = read("otherlisted.txt")
            o = o[(o["Test Issue"] == "N") & (o["ETF"] == "N")]
            o = o[~o["Security Name"].str.contains(bad_name, case=False, na=False)]
            symbols.update(o["ACT Symbol"].dropna())
        except Exception as e:
            log("ما قدرت أجيب قائمة نيويورك:", e)

    return sorted(s for s in symbols if s.isalpha() and len(s) <= 5)


def build_news_universe():
    """مرة باليوم: الأسهم اللي آخر سعر لها بين 1 و 10 دولار وعليها تداول."""
    all_syms = get_all_us_symbols()
    log(f"الأخبار: أفحص {len(all_syms)} سهم عشان أطلع اللي سعرها {NEWS_MIN_PRICE}-{NEWS_MAX_PRICE}$ ...")
    keep = []
    for t, df in download_batches(all_syms, 400, period="5d", interval="1d", prepost=False):
        try:
            last = float(df["Close"].iloc[-1])
            avg_vol = float(df["Volume"].mean())
            if NEWS_MIN_PRICE <= last <= NEWS_MAX_PRICE and avg_vol >= NEWS_MIN_AVG_VOLUME:
                keep.append(t)
        except Exception:
            continue
    log(f"الأخبار: {len(keep)} سهم داخل الفلتر")
    return keep


def _parse_news_item(item):
    """ياهو غيّر شكل الأخبار أكثر من مرة، هذي تقرأ الشكلين القديم والجديد."""
    c = item.get("content") if isinstance(item.get("content"), dict) else item
    news_id = item.get("id") or c.get("id") or item.get("uuid")
    title = c.get("title") or ""
    # الوقت
    ts = None
    if c.get("pubDate"):
        ts = pd.Timestamp(c["pubDate"])
    elif c.get("providerPublishTime"):
        ts = pd.Timestamp(int(c["providerPublishTime"]), unit="s")
    if ts is not None and ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    # الرابط والمصدر
    link = ""
    for k in ("canonicalUrl", "clickThroughUrl"):
        if isinstance(c.get(k), dict) and c[k].get("url"):
            link = c[k]["url"]
            break
    link = link or c.get("link") or ""
    provider = c.get("provider")
    source = provider.get("displayName") if isinstance(provider, dict) else (c.get("publisher") or "")
    return {"id": news_id or f"{title}-{ts}", "title": title, "time": ts,
            "link": link, "source": source}


def fetch_news(t):
    import yfinance as yf
    try:
        return t, [_parse_news_item(n) for n in (yf.Ticker(t).news or [])]
    except Exception:
        return t, []


def scan_news(tickers, window, already_sent):
    start, end = window
    hits = 0
    with ThreadPoolExecutor(max_workers=NEWS_WORKERS) as pool:
        for t, items in pool.map(fetch_news, tickers):
            for n in items:
                if not n["title"] or n["time"] is None:
                    continue
                local_time = n["time"].tz_convert(LOCAL_TZ)
                if not (start <= local_time <= end):
                    continue
                key = f"{t}-{n['id']}"
                if key in already_sent:
                    continue
                already_sent.add(key)
                hits += 1
                send_telegram(
                    f"📰 خبر جديد - سهم صغير\n"
                    f"السهم: {t}\n"
                    f"الخبر: {n['title']}\n"
                    f"المصدر: {n['source']}\n"
                    f"الوقت: {local_time:%H:%M} (توقيتك)\n"
                    f"{n['link']}"
                )
    log(f"[{datetime.now():%H:%M}] الأخبار: خلص الفحص - {hits} خبر جديد")


# ================== التشغيل ==================
def main():
    once = "--once" in sys.argv

    gap_tickers, gap_day = [], None
    gap_sent = set()
    news_tickers, news_day = [], None
    news_sent = set()

    while True:
        # (1) الجاب - وقت السوق الأمريكي
        if ENABLE_GAP and (us_market_open() or once):
            today = pd.Timestamp.now(tz=NY).date()
            if gap_day != today or not gap_tickers:
                gap_tickers = get_nasdaq_midcap_plus()
                gap_day = today
                log(f"الجاب: {len(gap_tickers)} سهم ناسداك قيمتها السوقية {MIN_MARKET_CAP/1e9:.0f} مليار وفوق")
            scan_gap(gap_tickers, gap_sent)

        # (2) الأخبار - من 11 الصبح إلى 4:30 العصر بتوقيتك
        window = news_window()
        if ENABLE_NEWS and window:
            today = pd.Timestamp.now(tz=LOCAL_TZ).date()
            if news_day != today or not news_tickers:
                news_tickers = build_news_universe()
                news_day = today
                news_sent.clear()
            scan_news(news_tickers, window, news_sent)

        if not us_market_open() and not window:
            log(f"[{datetime.now():%H:%M}] برا وقت الفحص، أنتظر...")

        if once:
            break
        time.sleep(CHECK_EVERY_MIN * 60)


if __name__ == "__main__":
    main()
