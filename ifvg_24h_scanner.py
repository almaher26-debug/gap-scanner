# -*- coding: utf-8 -*-
"""
سكانر الإنفيرجن جاب (IFVG) - فريم 4 ساعات على 24 ساعة (ملف مستقل)
=================================================================
- شمعة الأربع ساعات تنبني من 24 ساعة كاملة، نفس تريدنج فيو مع "خلال الليل":
  اليوم يبدأ 8 بالليل نيويورك، والشموع: 20-00 | 00-04 | 04-08 | 08-12 | 12-16 | 16-20
- بيانات النهار (4 الفجر - 8 بالليل): ألباكا SIP (الباقة المجانية: متأخر 15 دقيقة)
- بيانات الليل (8 بالليل - 4 الفجر): ألباكا BOATS (Blue Ocean) - بدون تينجو
- نفس شروط فريم الأربع ساعات اللي في gap_scanner.py (check_pattern_4h)
- يرسل على تيليجرام

متغيرات Railway المطلوبة (نفس اللي في worker):
    ALPACAAPIKEY  ALPACASECRETKEY  TELEGRAM_TOKEN  TELEGRAM_CHAT_ID

اختياري:
    SYMBOLS=AAPL,TSLA      يفحص هالأسهم بس بدل قائمة ناسداك
    GAP4H_STRICT=0         يطفي الشروط الإضافية (متراصة، لون الرابعة) ويخلي النموذج الأساسي بس
    NIGHT_FEED=boats       مصدر الليل في ألباكا (لو ما اشتغل جرّب overnight)

التشغيل:
    python ifvg_24h_scanner.py                 # يشتغل
    python ifvg_24h_scanner.py --test          # يجرب التقسيم والنموذج بدون نت
    python ifvg_24h_scanner.py --candles AAPL  # يطبع آخر شموع 4 ساعات للسهم عشان تقارنها بتريدنج فيو
    python ifvg_24h_scanner.py --once          # فحص واحد ويطلع
"""

import os
import sys
import time

import pandas as pd
import requests

# ================= الإعدادات =================
ALPACA_KEY = (os.environ.get("ALPACAAPIKEY") or os.environ.get("ALPACA_API_KEY")
              or os.environ.get("APCA_API_KEY_ID", ""))
ALPACA_SECRET = (os.environ.get("ALPACASECRETKEY") or os.environ.get("ALPACA_SECRET_KEY")
                 or os.environ.get("APCA_API_SECRET_KEY", ""))
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

DAY_FEED = os.environ.get("DAY_FEED", "sip").lower()        # 4 الفجر - 8 بالليل
NIGHT_FEED = os.environ.get("NIGHT_FEED", "boats").lower()  # 8 بالليل - 4 الفجر
SYMBOLS_ENV = [s.strip().upper() for s in os.environ.get("SYMBOLS", "").split(",") if s.strip()]

NY = "America/New_York"
LOCAL_TZ = "Asia/Riyadh"
BASE_MIN = 15                    # كل شي ينبني من شموع 15 دقيقة
FRAME_MIN = 240                  # 4 ساعات
FRAME_MIN_1H = 60                # ساعة
ANCHOR_MIN = 20 * 60             # اليوم يبدأ 8 بالليل نيويورك (نفس تريدنج فيو)
LOOKBACK_DAYS = 5                # كم يوم يرجع بالبيانات (يغطي الويكند)

MIN_STOCK_PRICE = 10             # يتجاهل الأسهم اللي سعرها أقل من كذا
MIN_MARKET_CAP = 2_000_000_000   # 2 مليار وفوق
NASDAQ_ONLY = True               # أسهم ناسداك بس (نفس البوت)
EXTRA_SYMBOLS = ["SPY", "QQQ",
                 "TSLA", "AAPL", "NVDA", "MSFT", "INTC", "MSTR", "COIN", "CRCL", "OKTA",
                 "META", "AVGO", "NOW", "ORCL", "LLY", "CRWD", "GOOGL", "ADBE", "SNDK", "AMD",
                 "MU", "DELL", "QCOM", "RKLB", "CRDO"]

ENABLE_BULLISH = True
ENABLE_BEARISH = True
REQUIRE_MIDDLE_COVER = True      # الشمعة الثانية تغطي الجاب كامل
STRICT_4H = os.environ.get("GAP4H_STRICT", "1") != "0"
GAP4H_MIN_SIZE = 0.20            # أقل حجم للجاب على فريم 4 ساعات (20 سنت)
GAP1H_MIN_SIZE = 0.80            # أقل حجم للجاب على فريم ساعة (80 سنت)
GAP4H_REQUIRE_STEP = True        # الشموع الثلاث متراصة
GAP4H_REQUIRE_COLOR4 = True      # الرابعة خضراء (صعودي) / حمراء (هبوطي)
# نسبة الاكتمال: بالليل الأسهم تتداول أقل فشموع الربع ساعة تجي متقطعة (ما فيه صفقات = ما فيه شمعة)
# وهذا طبيعي ونفس تريدنج فيو. فما نرفض الشمعة بسبب النقص (0 = بدون شرط)
GAP4H_MIN_FILL = 0

SCAN_AFTER_CLOSE_MIN = (17, 20, 25)   # يفحص بعد إغلاق كل شمعة 4 ساعات بكذا دقيقة (SIP متأخر 15 دقيقة)
MAX_ALERT_DELAY_MIN = 45            # ما ينبه على شمعة قفلت من أكثر من كذا دقيقة
SENT_FILE = "ifvg24_sent.txt"
SENT_KEEP_LINES = 20000
SHOW_CANDLES = True
DISCLAIMER = "⚠️ محتوى تعليمي فقط، وليس توصية بيع أو شراء."
HEADERS = {"User-Agent": "Mozilla/5.0"}
BARS_URL = "https://data.alpaca.markets/v2/stocks/bars"
OHLC = ["Open", "High", "Low", "Close"]
# =============================================


def log(*a):
    print(pd.Timestamp.now(tz=LOCAL_TZ).strftime("%H:%M:%S"), *a, flush=True)


# ---------- تيليجرام ----------
def chats():
    return [c.strip() for c in TELEGRAM_CHAT_ID.split(",") if c.strip()]


def send_telegram(text):
    text = "للمتابعة\n" + text + "\n\n" + DISCLAIMER
    log(text.replace("\n", " | "))
    if not TELEGRAM_TOKEN:
        return
    for chat_id in chats():
        try:
            r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                              data={"chat_id": chat_id, "text": text,
                                    "disable_web_page_preview": True}, timeout=10).json()
            if not r.get("ok"):
                log(f"فشل الإرسال لـ {chat_id}: {r.get('description')}")
        except Exception as e:
            log(f"فشل الإرسال لـ {chat_id}: {e}")


# ---------- ملف المرسل ----------
def load_sent():
    try:
        with open(SENT_FILE, encoding="utf-8") as f:
            lines = [x.strip() for x in f if x.strip()]
    except FileNotFoundError:
        return set()
    if len(lines) > SENT_KEEP_LINES:
        lines = lines[-SENT_KEEP_LINES:]
        with open(SENT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    return set(lines)


def mark_sent(key):
    try:
        with open(SENT_FILE, "a", encoding="utf-8") as f:
            f.write(key + "\n")
    except Exception:
        pass


# ---------- قائمة الأسهم ----------
def _to_number(x):
    try:
        return float(str(x).replace("$", "").replace(",", "").strip())
    except Exception:
        return 0.0


def get_universe():
    """أسهم ناسداك (وNYSE لو NASDAQ_ONLY=False) اللي قيمتها السوقية 2 مليار وفوق + القائمة الإضافية."""
    if SYMBOLS_ENV:
        return sorted(set(SYMBOLS_ENV))
    out = set(EXTRA_SYMBOLS)
    for ex in (("nasdaq",) if NASDAQ_ONLY else ("nasdaq", "nyse")):
        url = ("https://api.nasdaq.com/api/screener/stocks"
               f"?tableonly=true&limit=10000&exchange={ex}&download=true")
        try:
            r = requests.get(url, headers={**HEADERS, "Accept": "application/json"}, timeout=30)
            data = r.json().get("data") or {}
            rows = data.get("rows") or (data.get("table") or {}).get("rows") or []
            for row in rows:
                sym = str(row.get("symbol", "")).strip().upper()
                if (sym.isalpha() and len(sym) <= 5
                        and _to_number(row.get("marketCap")) >= MIN_MARKET_CAP
                        and _to_number(row.get("lastsale")) >= MIN_STOCK_PRICE):
                    out.add(sym)
        except Exception as e:
            log(f"ما قدرت أجيب أسهم {ex.upper()}:", e)
    log(f"قائمة الأسهم: {len(out)} سهم")
    return sorted(out)


# ---------- بيانات ألباكا ----------
def alpaca_headers():
    return {"APCA-API-KEY-ID": ALPACA_KEY, "APCA-API-SECRET-KEY": ALPACA_SECRET}


_feed_warned = set()


def fetch_bars(symbols, start, feed):
    """شموع 15 دقيقة لمجموعة أسهم من ألباكا. يرجع {الرمز: DataFrame بتوقيت نيويورك}."""
    out = {}
    for i in range(0, len(symbols), 100):
        chunk = symbols[i:i + 100]
        params = {"symbols": ",".join(chunk), "timeframe": f"{BASE_MIN}Min",
                  "start": start.tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
                  "limit": 10000, "feed": feed, "adjustment": "raw", "sort": "asc"}
        raw = {}
        for _ in range(200):
            try:
                r = requests.get(BARS_URL, headers=alpaca_headers(), params=params, timeout=30)
            except Exception as e:
                log(f"ألباكا ({feed}): فشل الاتصال -", e)
                break
            if r.status_code == 429:
                time.sleep(3)
                continue
            if r.status_code != 200:
                if feed not in _feed_warned:
                    _feed_warned.add(feed)
                    log(f"ألباكا ({feed}): خطأ {r.status_code} - {r.text[:200]}")
                break
            data = r.json()
            for sym, bars in (data.get("bars") or {}).items():
                raw.setdefault(sym, []).extend(bars or [])
            token = data.get("next_page_token")
            if not token:
                break
            params["page_token"] = token
        for sym, bars in raw.items():
            if not bars:
                continue
            df = pd.DataFrame(bars)
            idx = pd.to_datetime(df["t"], utc=True).dt.tz_convert(NY)
            df = pd.DataFrame({"Open": df["o"].astype(float), "High": df["h"].astype(float),
                               "Low": df["l"].astype(float), "Close": df["c"].astype(float)}).set_index(
                pd.DatetimeIndex(idx))
            out[sym] = df.sort_index()
    return out


def merge_day_night(day, night):
    """يدمج النهار (SIP) مع الليل (BOATS): الليل بس من 8 بالليل لين 4 الفجر، والباقي من SIP."""
    parts = []
    if day is not None and not day.empty:
        h = day.index.hour
        parts.append(day[(h >= 4) & (h < 20)])
    if night is not None and not night.empty:
        h = night.index.hour
        parts.append(night[(h >= 20) | (h < 4)])
    if not parts:
        return pd.DataFrame(columns=OHLC)
    df = pd.concat(parts).sort_index()
    return df[~df.index.duplicated(keep="first")]


# ---------- تقسيم الشموع (24 ساعة، نفس تريدنج فيو) ----------
def to_4h_24(df):
    """يحول شموع 15 دقيقة لشموع 4 ساعات على 24 ساعة، بداية اليوم 8 بالليل نيويورك.
    كل شمعة معها وقت إغلاقها (end) وعدد شموع الربع ساعة اللي فيها (n)."""
    df = df.dropna(subset=OHLC)
    if df.empty:
        return df
    if df.index.tz is None:
        df = df.tz_localize("UTC")
    df = df.tz_convert(NY)
    m = df.index.hour * 60 + df.index.minute
    offset = ((m - ANCHOR_MIN) % 1440) % FRAME_MIN
    start = df.index.floor("min") - pd.to_timedelta(offset, unit="m")
    out = df.groupby(start).agg(Open=("Open", "first"), High=("High", "max"),
                                Low=("Low", "min"), Close=("Close", "last"),
                                n=("Close", "size"))
    out["end"] = out.index + pd.Timedelta(minutes=FRAME_MIN)
    return out


def to_1h_24(df):
    """يحول شموع 15 دقيقة لشموع ساعة على 24 ساعة، نفس منطق to_4h_24 بس بإطار ساعة."""
    df = df.dropna(subset=OHLC)
    if df.empty:
        return df
    if df.index.tz is None:
        df = df.tz_localize("UTC")
    df = df.tz_convert(NY)
    m = df.index.hour * 60 + df.index.minute
    offset = ((m - ANCHOR_MIN) % 1440) % FRAME_MIN_1H
    start = df.index.floor("min") - pd.to_timedelta(offset, unit="m")
    out = df.groupby(start).agg(Open=("Open", "first"), High=("High", "max"),
                                Low=("Low", "min"), Close=("Close", "last"),
                                n=("Close", "size"))
    out["end"] = out.index + pd.Timedelta(minutes=FRAME_MIN_1H)
    return out


def only_closed(c, now):
    """يخلي الشموع المقفلة بس."""
    if c.empty:
        return c
    return c[(c["end"] <= now).values]


# ---------- النموذج (نفس gap_scanner.py) ----------
def check_pattern(c):
    """آخر 4 شموع مقفلة: جاب بين ذيل الأولى والثالثة، الثانية تغطيه، والرابعة تقفل وراه."""
    if len(c) < 4:
        return None
    c1, c2, c3, c4 = (c.iloc[i] for i in (-4, -3, -2, -1))
    info = {"price": c4["Close"], "open": c4["Open"], "candle_time": c.index[-1], "end": c4["end"]}

    if ENABLE_BULLISH and c1["Low"] > c3["High"]:
        gap_bottom, gap_top = c3["High"], c1["Low"]
        covered = c2["High"] >= gap_top and c2["Low"] <= gap_bottom
        if (covered or not REQUIRE_MIDDLE_COVER) and c4["Close"] > gap_top:
            return {"side": "bull", "gap_bottom": gap_bottom, "gap_top": gap_top, **info}

    if ENABLE_BEARISH and c1["High"] < c3["Low"]:
        gap_bottom, gap_top = c1["High"], c3["Low"]
        covered = c2["High"] >= gap_top and c2["Low"] <= gap_bottom
        if (covered or not REQUIRE_MIDDLE_COVER) and c4["Close"] < gap_bottom:
            return {"side": "bear", "gap_bottom": gap_bottom, "gap_top": gap_top, **info}
    return None


def check_pattern_4h(c):
    """شروط فريم 4 ساعات: متراصة، ذيولها تلتقي، والرابعة بلون الاتجاه."""
    res = check_pattern(c)
    if not res:
        return None
    res["candles"] = c.iloc[-4:]
    if not STRICT_4H:
        return res
    if res["gap_top"] - res["gap_bottom"] < GAP4H_MIN_SIZE:
        return None
    c1, c2, c3, c4 = (c.iloc[i] for i in (-4, -3, -2, -1))
    bull = res["side"] == "bull"

    if GAP4H_MIN_FILL:
        for i in (-4, -3, -2, -1):
            if c.iloc[i]["n"] / (FRAME_MIN / BASE_MIN) < GAP4H_MIN_FILL:
                return None

    for a, b in ((c1, c2), (c2, c3)):
        if b["Low"] > a["High"] or b["High"] < a["Low"]:
            return None

    if GAP4H_REQUIRE_STEP:
        if bull and not (c2["Low"] < c1["Low"] and c3["Low"] < c2["Low"]
                         and c2["High"] < c1["High"] and c3["High"] < c2["High"]):
            return None
        if not bull and not (c2["High"] > c1["High"] and c3["High"] > c2["High"]
                             and c2["Low"] > c1["Low"] and c3["Low"] > c2["Low"]):
            return None

    if GAP4H_REQUIRE_COLOR4:
        if bull and not c4["Close"] > c4["Open"]:
            return None
        if not bull and not c4["Close"] < c4["Open"]:
            return None
    return res


def check_pattern_1h(c):
    """نفس نموذج الجاب الأساسي على فريم ساعة، بحد أدنى لحجم الجاب 80 سنت."""
    res = check_pattern(c)
    if not res:
        return None
    if res["gap_top"] - res["gap_bottom"] < GAP1H_MIN_SIZE:
        return None
    res["candles"] = c.iloc[-4:]
    return res


def gap_message(t, res):
    lo, hi, px = (round(float(res[k]), 2) for k in ("gap_bottom", "gap_top", "price"))
    frame = res.get("frame", "فريم 4 ساعات (24 ساعة)")
    if res["side"] == "bull":
        head, line = f"🟢 Inversion Gap - {frame}", f"الشمعة قفلت فوق أعلى الـ IFVG ({hi})"
    else:
        head, line = f"🔴 Inversion Gap - {frame}", f"الشمعة قفلت تحت أسفل الـ IFVG ({lo})"
    closed_at = pd.Timestamp(res["end"]).tz_convert(LOCAL_TZ)
    msg = (f"{head}\n"
           f"السهم: ${t}\n"
           f"IFVG: {lo} ← {hi}  (حجمه {hi - lo:.2f}$)\n"
           f"{line}\n"
           f"سعر الإغلاق: {px}\n"
           f"وقت الإغلاق: {closed_at:%H:%M} (توقيتك)")
    cs = res.get("candles")
    if SHOW_CANDLES and cs is not None:
        rows = []
        for k, (ts, r) in enumerate(cs.iterrows(), 1):
            lt = pd.Timestamp(ts).tz_convert(LOCAL_TZ)
            col = "🟢" if r["Close"] > r["Open"] else "🔴"
            rows.append(f"{k}) {lt:%m/%d %H:%M} {col} أعلى {r['High']:.2f} | أقل {r['Low']:.2f}")
        msg += "\nالشموع (بتوقيتك):\n" + "\n".join(rows)
    return msg


# ---------- الفحص ----------
def load_candles(symbols, now):
    start = now - pd.Timedelta(days=LOOKBACK_DAYS)
    day = fetch_bars(symbols, start, DAY_FEED)
    night = fetch_bars(symbols, start, NIGHT_FEED)
    if not night:
        log(f"⚠️ ما جات بيانات ليل من ألباكا ({NIGHT_FEED}) - الشموع بتكون ناقصة")
    return {s: merge_day_night(day.get(s), night.get(s)) for s in symbols}


def scan(symbols, sent):
    now = pd.Timestamp.now(tz=NY)
    data = load_candles(symbols, now)
    hits = 0
    hits_1h = 0
    for t, df in data.items():
        try:
            if df.empty or float(df["Close"].iloc[-1]) < MIN_STOCK_PRICE:
                continue
            # ---- فريم 4 ساعات ----
            c4 = only_closed(to_4h_24(df), now)
            res = check_pattern_4h(c4)
            if res and (now - pd.Timestamp(res["end"])).total_seconds() / 60 <= MAX_ALERT_DELAY_MIN:
                key = f"{t}-4h24-{res['side']}-{res['candle_time']}"
                if key not in sent:
                    sent.add(key)
                    mark_sent(key)
                    res["frame"] = "فريم 4 ساعات (24 ساعة)"
                    send_telegram(gap_message(t, res))
                    hits += 1
            # ---- فريم ساعة ----
            c1 = only_closed(to_1h_24(df), now)
            res1 = check_pattern_1h(c1)
            if res1 and (now - pd.Timestamp(res1["end"])).total_seconds() / 60 <= MAX_ALERT_DELAY_MIN:
                key1 = f"{t}-1h24-{res1['side']}-{res1['candle_time']}"
                if key1 not in sent:
                    sent.add(key1)
                    mark_sent(key1)
                    res1["frame"] = "فريم ساعة (24 ساعة)"
                    send_telegram(gap_message(t, res1))
                    hits_1h += 1
        except Exception as e:
            log(f"{t}: خطأ -", e)
    log(f"فحص 24 ساعة: {len(data)} سهم، {hits} تنبيه (4 ساعات) + {hits_1h} تنبيه (ساعة)")


def market_closed(now):
    """الويكند: من 8:30 بالليل الجمعة لين 7:30 بالليل الأحد نيويورك ما فيه تداول."""
    wd, m = now.weekday(), now.hour * 60 + now.minute
    return (wd == 4 and m >= 20 * 60 + 30) or wd == 5 or (wd == 6 and m < 19 * 60 + 30)


def due_slots(now):
    """أوقات الفحص: بعد إغلاق كل شمعة ساعة بكذا دقيقة.
    لأن شمعة الساعة تقفل كل ساعة، والأربع ساعات تقفل على نفس الحدود، يكفي ننطلق من بداية كل ساعة."""
    base = now.floor("h")
    return [base + pd.Timedelta(minutes=d) for d in SCAN_AFTER_CLOSE_MIN]


def run(once=False):
    if not (ALPACA_KEY and ALPACA_SECRET):
        log("❌ يحتاج ALPACAAPIKEY و ALPACASECRETKEY")
        sys.exit(1)
    if not (TELEGRAM_TOKEN and chats()):
        log("⚠️ TELEGRAM_TOKEN أو TELEGRAM_CHAT_ID ناقص - بيطبع بالسجل بس")
    log(f"سكانر IFVG 4 ساعات (24 ساعة) بدأ - النهار {DAY_FEED.upper()}، الليل {NIGHT_FEED.upper()}"
        + ("" if STRICT_4H else " - الشروط الإضافية مطفية"))
    sent = load_sent()
    symbols, sym_day = get_universe(), pd.Timestamp.now(tz=NY).date()
    scan(symbols, sent)        # فحص أول ما يشتغل (ينبه بس لو الشمعة قفلت من أقل من 45 دقيقة)
    if once:
        return
    done = set()
    while True:
        now = pd.Timestamp.now(tz=NY)
        if now.date() != sym_day and now.hour == 19:   # نجدد القائمة مرة باليوم قبل بداية الليل
            symbols, sym_day = get_universe(), now.date()
        if not market_closed(now):
            for slot in due_slots(now):
                if slot <= now < slot + pd.Timedelta(minutes=4) and slot not in done:
                    done.add(slot)
                    scan(symbols, sent)
        done = {s for s in done if now - s < pd.Timedelta(hours=6)}
        time.sleep(20)


def show_candles(sym):
    """يطبع آخر شموع 4 ساعات (24 ساعة) لسهم عشان تقارنها بتريدنج فيو."""
    now = pd.Timestamp.now(tz=NY)
    df = load_candles([sym], now)[sym]
    c = to_4h_24(df)
    print(f"{sym} - شموع 4 ساعات على 24 ساعة (توقيت نيويورك | n = عدد شموع الربع ساعة من 16):")
    for ts, r in c.tail(12).iterrows():
        print(f"{ts:%m/%d %H:%M}  O {r['Open']:.2f}  H {r['High']:.2f}  L {r['Low']:.2f}  "
              f"C {r['Close']:.2f}  n {int(r['n'])}")
    res = check_pattern_4h(only_closed(c, now))
    print("نموذج 4 ساعات على آخر شمعة مقفلة:", res["side"] if res else "ما فيه")
    c1 = to_1h_24(df)
    res1 = check_pattern_1h(only_closed(c1, now))
    print("نموذج الساعة على آخر شمعة مقفلة:", res1["side"] if res1 else "ما فيه")


def self_test():
    """بيانات وهمية: يتأكد إن التقسيم يبدأ 8 بالليل، والليل ينضم، والنموذج يتعرف."""
    idx = pd.date_range("2026-10-12 20:00", periods=4 * 16, freq="15min", tz=NY)
    # 4 شموع 4 ساعات: هابطة متراصة بجاب بين الأولى والثالثة، والرابعة خضراء تقفل فوقه
    plan = [(110, 112, 108, 108.5), (108.5, 109, 105, 105.5), (105.5, 106, 103, 103.5),
            (103.5, 111, 103.4, 110)]
    rows = []
    for o, h, lo, cl in plan:
        for k in range(16):
            px = o + (cl - o) * k / 15
            rows.append({"Open": px, "High": max(px, o) + 0.01, "Low": min(px, o) - 0.01, "Close": px})
        rows[-16]["High"], rows[-15]["Low"] = h, lo
    full = pd.DataFrame(rows, index=idx)
    h = full.index.hour
    day, night = full[(h >= 4) & (h < 20)], full[(h >= 20) | (h < 4)]
    merged = merge_day_night(day, night)
    c = to_4h_24(merged)
    starts = [f"{t:%H:%M}" for t in c.index]
    print("بدايات الشموع:", starts)
    assert starts == ["20:00", "00:00", "04:00", "08:00"], starts
    assert list(c["n"]) == [16] * 4
    res = check_pattern_4h(only_closed(c, idx[-1] + pd.Timedelta(minutes=20)))
    assert res and res["side"] == "bull", res
    print(gap_message("TEST", res))
    c1 = to_1h_24(merged)
    print("عدد شموع الساعة:", len(c1))
    assert len(c1) == 16
    print("TEST OK")


if __name__ == "__main__":
    if "--test" in sys.argv:
        self_test()
    elif "--candles" in sys.argv:
        show_candles(sys.argv[sys.argv.index("--candles") + 1].upper())
    else:
        run(once="--once" in sys.argv)
