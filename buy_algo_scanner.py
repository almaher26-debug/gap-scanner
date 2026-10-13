# -*- coding: utf-8 -*-
"""
خوارزميات الشراء - ملف مستقل
================================
يراقب صفقات أسهم ناسداك لحظياً من ألباكا (sip = كل البورصات) ويدور على خوارزميات التقطيع:
    - الأسهم: ناسداك من 1$ إلى 10$ والفلوت من 200 ألف إلى 25 مليون سهم (الأنشط أول، أقصى 300)
    - صفقات سريعة حجم الواحدة 10 أسهم أو أقل، كلها بنفس الحجم بالضبط (1، 1، 1 ... أو 5، 5، 5 ...)
    - تنبيه عند 600 صفقة أو أكثر خلال 5 دقايق، و"قوي" عند 1200
    - يرسل بس لو الشراء 70% أو أكثر من الصفقات (تقدير من اتجاه السعر)
    - تنبيه واحد لكل سهم كل 24 ساعة

المتغيرات في Railway:
    ALPACAAPIKEY و ALPACASECRETKEY   (مفاتيح الحساب المشترك بالباقة المدفوعة)
    TELEGRAM_TOKEN و TELEGRAM_CHAT_ID (أكثر من محادثة: بينها فاصلة)
    اختياري: ALGO_DELAY_MIN = 16 لو رجعت للباقة المجانية | ALPACA_MIN_GAP_SEC = 0.35 للمجانية
             ALGO_BUY_MIN_PCT (نسبة الشراء، الافتراضي 70)

التشغيل:
    pip install yfinance pandas requests
    python buy_algo_scanner.py          # يشتغل باستمرار
    python buy_algo_scanner.py --test   # يجرب الكشف على صفقات وهمية (بدون نت)
"""
import os
import sys
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import requests

# ================== الإعدادات ==================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "ضع_توكن_البوت_هنا")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "ضع_رقم_المحادثة_هنا")

ALPACA_KEY = (os.environ.get("ALPACAAPIKEY") or os.environ.get("ALPACA_API_KEY")
              or os.environ.get("APCA_API_KEY_ID", ""))
ALPACA_SECRET = (os.environ.get("ALPACASECRETKEY") or os.environ.get("ALPACA_SECRET_KEY")
                 or os.environ.get("APCA_API_SECRET_KEY", ""))
ALGO_FEED = os.environ.get("ALGO_FEED", "sip").lower()
ALGO_DELAY_MIN = int(os.environ.get("ALGO_DELAY_MIN", "0"))   # الباقة المدفوعة = لحظي (0)
ALPACA_MIN_GAP_SEC = float(os.environ.get("ALPACA_MIN_GAP_SEC", "0.05"))

MIN_PRICE = 1                         # أقل سعر سهم
MAX_PRICE = 10                        # أعلى سعر سهم
MIN_FLOAT = 200_000                   # أقل فلوت (سهم)
MAX_FLOAT = 25_000_000                # أعلى فلوت (سهم)
MIN_DAY_VOLUME = 50_000               # يشيل الأسهم الميتة (حجم اليوم)
MAX_SYMBOLS = 300                     # أقصى عدد أسهم يراقبها (الأنشط أول)

MAX_SIZE = 10                         # حجم الصفقة 10 أسهم أو أقل
WINDOW_MIN = 5                        # يعد الصفقات المتكررة خلال آخر كذا دقيقة
MIN_STREAK = 600                      # تنبيه عند 600 صفقة أو أكثر بنفس الحجم
STRONG_STREAK = 1200                  # تنبيه قوي عند 1200 أو أكثر
MIN_VALUE = float(os.environ.get("ALGO_BUY_MIN_VALUE", "0"))    # أقل مبلغ بالدولار (0 = بدون شرط)
MIN_BUY_PCT = float(os.environ.get("ALGO_BUY_MIN_PCT", "70"))   # أقل نسبة شراء من الصفقات (%)
REALERT_MIN = 15                      # ما يعيد نفس مستوى التنبيه لنفس السهم والحجم قبل كذا دقيقة
ONCE_HOURS = 24                       # تنبيه واحد لكل سهم كل كذا ساعة (0 = بدون حد)
ONCE_FILE = "buy_algo_once.txt"       # يحفظ وقت آخر تنبيه لكل سهم لو البوت أعاد التشغيل
POLL_SEC = 15                         # كل كم ثانية يسحب الصفقات الجديدة
CHUNK = 30                            # كم سهم بكل طلب لألباكا
FLOAT_CACHE_SEC = 6 * 60 * 60         # الفلوت يتحدث كل 6 ساعات

NY = "America/New_York"
LOCAL_TZ = "Asia/Riyadh"
HEADERS = {"User-Agent": "Mozilla/5.0"}
ALGO_URL = "https://data.alpaca.markets/v2/stocks/trades"

EDUCATION = ("📚 للتعلّم - خوارزميات التقطيع:\n"
             "مئات الصفقات الصغيرة بنفس الحجم بالضبط (سهم، سهم، سهم...) علامة على برنامج "
             "يقسّم أمر كبير على قطع صغيرة عشان ما يحرك السعر ولا يبان.\n"
             "تقدير الشراء/البيع من اتجاه السعر تقريبي، وفي الأسهم الصغيرة ممكن يكون تلاعب أو صانع سوق.")
DISCLAIMER = "⚠️ محتوى تعليمي فقط، وليس توصية بيع أو شراء."
# ===============================================


def log(*a):
    print(*a, flush=True)


# ================== تيليجرام ==================
TG_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
CHATS = [c.strip() for c in TELEGRAM_CHAT_ID.split(",") if c.strip() and "ضع_" not in c]


def send_telegram(text):
    text = "للمتابعة\n" + text + "\n\n" + EDUCATION + "\n\n" + DISCLAIMER
    log(text)
    if "ضع_" in TELEGRAM_TOKEN:
        return
    for chat_id in CHATS:
        try:
            r = requests.post(f"{TG_API}/sendMessage",
                              data={"chat_id": chat_id, "text": text,
                                    "disable_web_page_preview": True}, timeout=10).json()
            if not r.get("ok"):
                log(f"فشل الإرسال لـ {chat_id}: {r.get('description')}")
        except Exception as e:
            log(f"فشل إرسال التنبيه لـ {chat_id}:", e)


# ================== قائمة الأسهم ==================
def _to_number(x):
    try:
        return float(str(x).replace("$", "").replace(",", "").strip())
    except Exception:
        return 0.0


def _nasdaq_rows():
    """كل أسهم ناسداك من السكرينر الرسمي: [(الرمز، القيمة السوقية، حجم اليوم، السعر)]."""
    url = ("https://api.nasdaq.com/api/screener/stocks"
           "?tableonly=true&limit=10000&exchange=nasdaq&download=true")
    r = requests.get(url, headers={**HEADERS, "Accept": "application/json"}, timeout=30)
    data = r.json().get("data") or {}
    rows = data.get("rows") or (data.get("table") or {}).get("rows") or []
    out = []
    for row in rows:
        sym = str(row.get("symbol", "")).strip().upper()
        if sym.isalpha() and len(sym) <= 5:
            out.append((sym, _to_number(row.get("marketCap")), _to_number(row.get("volume")),
                        _to_number(row.get("lastsale"))))
    return out


_float_cache = {}


def get_float(sym):
    now = time.time()
    old = _float_cache.get(sym)
    if old and now - old[0] < FLOAT_CACHE_SEC:
        return old[1]
    try:
        import yfinance as yf
        val = (yf.Ticker(sym).info or {}).get("floatShares")
        val = float(val) if val is not None else None
    except Exception:
        val = None
    _float_cache[sym] = (now, val)
    return val


def get_universe():
    """ناسداك 1$-10$ والفلوت من 200 ألف إلى 25 مليون، الأنشط أول. يرجع {الرمز: (القيمة السوقية، الفلوت)}."""
    try:
        picks = [(vol, sym, cap) for sym, cap, vol, px in _nasdaq_rows()
                 if MIN_PRICE <= px <= MAX_PRICE and vol >= MIN_DAY_VOLUME]
        picks.sort(reverse=True)
        log(f"أفحص الفلوت لـ {len(picks)} سهم سعرها {MIN_PRICE:g}$-{MAX_PRICE:g}$ ...")
        out = {}
        with ThreadPoolExecutor(max_workers=8) as pool:
            for i in range(0, len(picks), 40):        # مرتبة بالأنشط، نوقف لما نوصل الحد
                part = picks[i:i + 40]
                for (_, sym, cap), flt in zip(part, pool.map(lambda x: get_float(x[1]), part)):
                    if flt and MIN_FLOAT <= flt <= MAX_FLOAT and len(out) < MAX_SYMBOLS:
                        out[sym] = (cap, flt)
                if len(out) >= MAX_SYMBOLS:
                    break
        return out
    except Exception as e:
        log("ما قدرت أجيب قائمة الأسهم -", e)
        return {}


# ================== ألباكا ==================
_alpaca_lock = threading.Lock()
_alpaca_next = [0.0]


def _alpaca_wait():
    with _alpaca_lock:
        now = time.time()
        wait = _alpaca_next[0] - now
        _alpaca_next[0] = max(now, _alpaca_next[0]) + ALPACA_MIN_GAP_SEC
    if wait > 0:
        time.sleep(wait)


def fetch_trades(symbols, start, end):
    """الصفقات بين start و end لمجموعة أسهم. يرجع {الرمز: [صفقات]} أو None لو فشل."""
    headers = {"APCA-API-KEY-ID": ALPACA_KEY, "APCA-API-SECRET-KEY": ALPACA_SECRET}
    params = {"symbols": ",".join(symbols), "feed": ALGO_FEED, "limit": 10000, "sort": "asc",
              "start": start.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
              "end": end.strftime("%Y-%m-%dT%H:%M:%S.%fZ")}
    out = {}
    for _ in range(20):                          # صفحات (لو الصفقات كثيرة)
        _alpaca_wait()
        try:
            r = requests.get(ALGO_URL, headers=headers, params=params, timeout=20)
        except Exception as e:
            log("ألباكا: فشل الاتصال -", e)
            return None
        if r.status_code == 403 and "subscription" in r.text.lower():
            log("ألباكا: الاشتراك ما يسمح ببيانات sip اللحظية - تأكد إن المفاتيح من الحساب المشترك،"
                " أو حط ALGO_DELAY_MIN = 16 في Railway")
            return None
        if r.status_code in (401, 403):
            log(f"ألباكا: المفاتيح مرفوضة ({r.status_code}) - تأكد من ALPACAAPIKEY و ALPACASECRETKEY")
            return None
        if r.status_code == 429:
            log("ألباكا: طلبات كثيرة، أستنى شوي")
            time.sleep(10)
            continue
        if r.status_code != 200:
            log(f"ألباكا: خطأ {r.status_code} - {r.text[:200]}")
            return None
        data = r.json()
        for sym, trades in (data.get("trades") or {}).items():
            out.setdefault(sym, []).extend(trades or [])
        token = data.get("next_page_token")
        if not token:
            break
        params["page_token"] = token
    return out


# ================== الكشف ==================
class AlgoDetector:
    """يعد الصفقات الصغيرة اللي بنفس الحجم بالضبط خلال آخر WINDOW_MIN دقيقة لكل سهم.
    ويقدّر الشراء/البيع من اتجاه السعر: صفقة أعلى من اللي قبلها = شراء، أقل = بيع (تقريبي)."""
    def __init__(self):
        self.win = {}         # (الرمز، الحجم) -> deque[(الوقت، السعر، الجهة)]
        self.seen = {}
        self.last_px = {}
        self.last_side = {}
        self.alerted = {}

    def add(self, sym, trade):
        tid = trade.get("i")
        seen = self.seen.setdefault(sym, deque(maxlen=50000))
        if tid is not None:
            if tid in seen:
                return None
            seen.append(tid)
        size = float(trade.get("s") or 0)
        price = float(trade.get("p") or 0)
        if size <= 0 or price <= 0:
            return None
        prev = self.last_px.get(sym)
        side = self.last_side.get(sym, 0)
        if prev is not None and price != prev:
            side = 1 if price > prev else -1          # نفس السعر = نفس جهة اللي قبلها
        self.last_px[sym], self.last_side[sym] = price, side
        if size > MAX_SIZE:
            return None
        ts = pd.Timestamp(trade["t"])
        q = self.win.setdefault((sym, size), deque())
        q.append((ts, price, side))
        cutoff = ts - pd.Timedelta(minutes=WINDOW_MIN)
        while q and q[0][0] < cutoff:
            q.popleft()
        n = len(q)
        level = "strong" if n >= STRONG_STREAK else "normal" if n >= MIN_STREAK else None
        if level is None:
            return None
        if MIN_VALUE and sum(x[1] for x in q) * size < MIN_VALUE:
            return None
        buys = sum(1 for x in q if x[2] > 0)
        if buys * 100 < MIN_BUY_PCT * n:
            return None                                # غالبها مو شراء: ما ينبه
        k = (sym, size, level)
        last = self.alerted.get(k)
        if last is not None and ts - last < pd.Timedelta(minutes=REALERT_MIN):
            return None
        self.alerted[k] = ts
        prices = [x[1] for x in q]
        sells = sum(1 for x in q if x[2] < 0)
        return {"size": size, "count": n, "first_t": q[0][0], "last_t": ts,
                "low": min(prices), "high": max(prices), "last": price,
                "buys": buys, "sells": sells, "level": level}


def _cap_txt(cap):
    return f"{cap / 1e9:.2f} مليار$" if cap >= 1e9 else f"{cap / 1e6:.1f} مليون$"


def make_message(sym, a, cap=None, flt=None):
    strength = "🔥 قوي" if a["level"] == "strong" else "⚡ رصد"
    mins = max((a["last_t"] - a["first_t"]).total_seconds() / 60, 0.1)
    b, s_, total, size = a["buys"], a["sells"], a["count"], a["size"]
    pct = lambda x: f"{x / total * 100:.0f}%" if total else "0%"
    n = total - b - s_
    return (f"🟢 خوارزمية شراء (تقطيع) — {strength}\n"
            f"القسم: شراء فقط | {MIN_PRICE:g}$-{MAX_PRICE:g}$ | فلوت "
            f"{MIN_FLOAT / 1e3:g} ألف - {MAX_FLOAT / 1e6:g} مليون\n"
            f"السهم: ${sym}\n"
            f"السعر: ${a['last']:.4g} (من {a['low']:.4g} إلى {a['high']:.4g})\n"
            f"الحجم المتكرر: {size:g} سهم\n"
            f"التكرار: {total:,} صفقة خلال {mins:.1f} دقيقة\n"
            f"🟢 شراء: {b:,} صفقة ({pct(b)}) = {b * size:,.0f} سهم\n"
            f"🔴 بيع: {s_:,} صفقة ({pct(s_)}) = {s_ * size:,.0f} سهم\n"
            + (f"⚪ بدون اتجاه: {n:,} صفقة\n" if n else "")
            + (f"القيمة السوقية: {_cap_txt(cap)}\n" if cap else "")
            + (f"الفلوت: {int(flt):,} سهم\n" if flt else "")
            + f"المصدر: {ALGO_FEED.upper()} عبر Alpaca"
            + (f" (متأخر {ALGO_DELAY_MIN - 1} دقيقة)" if ALGO_DELAY_MIN else "") + "\n"
            f"وقت آخر صفقة: {a['last_t'].tz_convert(LOCAL_TZ):%H:%M:%S} (توقيتك)")


# ================== التشغيل ==================
def trading_hours(now=None):
    """4 الفجر - 8 بالليل نيويورك، أيام الأسبوع."""
    now = now or pd.Timestamp.now(tz=NY)
    m = now.hour * 60 + now.minute
    return now.weekday() < 5 and 4 * 60 <= m <= 20 * 60


def _once_load():
    out = {}
    try:
        with open(ONCE_FILE, encoding="utf-8") as f:
            for line in f:
                try:
                    sym, ts = line.strip().split("|")
                    ts = pd.Timestamp(ts)
                    out[sym] = max(ts, out.get(sym, ts))
                except Exception:
                    continue
    except FileNotFoundError:
        pass
    return out


def _once_save(sym, ts):
    try:
        with open(ONCE_FILE, "a", encoding="utf-8") as f:
            f.write(f"{sym}|{ts.isoformat()}\n")
    except Exception:
        pass


def main_loop():
    if not (ALPACA_KEY and ALPACA_SECRET):
        log("مطفي: حط ALPACAAPIKEY و ALPACASECRETKEY في Railway")
        return
    det = AlgoDetector()
    once_last = _once_load() if ONCE_HOURS else {}
    last_end, was_on = None, None
    caps, caps_day = {}, None
    log(f"خوارزميات الشراء: ألباكا ({ALGO_FEED}"
        + (f"، متأخر {ALGO_DELAY_MIN - 1} دقيقة" if ALGO_DELAY_MIN else "، لحظي") + ")")
    while True:
        try:
            now = pd.Timestamp.now(tz="UTC")
            end = now - pd.Timedelta(minutes=ALGO_DELAY_MIN)
            on = trading_hours(end.tz_convert(NY))
            if on != was_on:
                log("بدأ المراقبة" if on else "السوق مسكر، أنتظر")
                was_on = on
            if not on:
                last_end = None
                time.sleep(60)
                continue
            today = pd.Timestamp.now(tz=NY).date()
            if caps_day != today or not caps:
                caps = get_universe()
                caps_day = today
                log(f"يراقب {len(caps)} سهم: " + ", ".join(list(caps)[:30])
                    + (" ..." if len(caps) > 30 else ""))
                if not caps:
                    time.sleep(600)               # ما لقى أسهم، يعيد المحاولة بعد 10 دقايق
                    caps_day = None
                    continue
            syms = list(caps)
            # نرجع شوي لورا عشان الصفقات المتأخرة، والتكرار ينشال بأرقام الصفقات
            start = (last_end or end - pd.Timedelta(seconds=60)) - pd.Timedelta(seconds=5)
            got = None
            for i in range(0, len(syms), CHUNK):
                part = fetch_trades(syms[i:i + CHUNK], start, end)
                if part is not None:
                    got = got or {}
                    got.update(part)
            if got is not None:
                last_end = end
                for sym, trades in got.items():
                    for tr in sorted(trades, key=lambda x: x.get("t", "")):
                        res = det.add(sym, tr)
                        if not res:
                            continue
                        if ONCE_HOURS:
                            now_utc = pd.Timestamp.now(tz="UTC")
                            prev = once_last.get(sym)
                            if prev is not None and now_utc - prev < pd.Timedelta(hours=ONCE_HOURS):
                                continue
                            once_last[sym] = now_utc
                            _once_save(sym, now_utc)
                        cap, flt = caps.get(sym, (None, None))
                        send_telegram(make_message(sym, res, cap, flt))
        except Exception as e:
            log("خطأ -", e)
        time.sleep(POLL_SEC)


def self_test():
    """صفقات وهمية: 700 صفقة شراء لازم ينبه، و700 صفقة بيع ما ينبه."""
    t0 = pd.Timestamp("2026-01-02T15:00:00Z")
    for label, step, expect in (("شراء", 0.0001, True), ("بيع", -0.0001, False)):
        det, hit = AlgoDetector(), None
        for k in range(700):
            r = det.add("TEST", {"i": k, "s": 2, "p": round(5 + step * k, 4),
                                 "t": str(t0 + pd.Timedelta(milliseconds=300 * k))})
            hit = hit or r
        assert bool(hit) == expect, (label, hit)
        if hit:
            assert hit["count"] == MIN_STREAK, hit
            log(make_message("TEST", hit, 50e6, 3_000_000))
        log(f"✅ تجربة {label}: " + ("نبّه" if hit else "ما نبّه"))
    log("✅ التجربة نجحت")


if __name__ == "__main__":
    if "--test" in sys.argv:
        self_test()
    else:
        main_loop()
