"""
سكانر أسهم البيني ستوك - شمعة 5 دقائق
=========================================
الشروط:
  1) سعر السهم بين MIN_PRICE و MAX_PRICE (بيني ستوك)
  2) الفري فلوت بين 200 ألف و 20 مليون سهم
  3) شمعة 5 دقائق (آخر شمعة مقفلة): حجم التداول >= 122,000 وخضراء (الإغلاق > الافتتاح)
  4) السهم كان راكد قبلها: آخر QUIET_BARS شمعات حجمها صغير وسعرها ما تحرك
  5) أي سهم مرتفع فوق 20% اليوم يُستبعد
  6) التنبيه يجي مرة وحدة بس لكل سهم في اليوم

مصادر البيانات:
  - Polygon.io  : الأسعار والشموع (يحتاج اشتراك فيه Snapshot)
  - FMP         : بيانات الفري فلوت
  - Telegram    : إرسال التنبيهات
"""

import os
import time
import logging
import datetime as dt
from zoneinfo import ZoneInfo

import requests

# ---------------- الإعدادات (تتغير من متغيرات البيئة) ----------------
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "")
FMP_API_KEY = os.getenv("FMP_API_KEY", "")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

MIN_PRICE = float(os.getenv("MIN_PRICE", "0.10"))
MAX_PRICE = float(os.getenv("MAX_PRICE", "5.00"))

MIN_FLOAT = int(os.getenv("MIN_FLOAT", "200000"))
MAX_FLOAT = int(os.getenv("MAX_FLOAT", "20000000"))

MIN_CANDLE_VOLUME = int(os.getenv("MIN_CANDLE_VOLUME", "122000"))
MAX_DAY_CHANGE_PCT = float(os.getenv("MAX_DAY_CHANGE_PCT", "20"))

# شرط الركود
QUIET_BARS = int(os.getenv("QUIET_BARS", "6"))                 # عدد الشمعات اللي قبل
QUIET_MAX_BAR_VOLUME = int(os.getenv("QUIET_MAX_BAR_VOLUME", "30000"))  # أقصى حجم لكل شمعة راكدة
QUIET_MAX_RANGE_PCT = float(os.getenv("QUIET_MAX_RANGE_PCT", "3"))     # أقصى تحرك سعري خلال فترة الركود %

# ساعات التشغيل بتوقيت نيويورك (يشمل البري ماركت والأفتر ماركت)
SESSION_START = os.getenv("SESSION_START", "04:00")
SESSION_END = os.getenv("SESSION_END", "20:00")

ET = ZoneInfo("America/New_York")
POLY = "https://api.polygon.io"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("scanner")
http = requests.Session()


# ---------------- أدوات مساعدة ----------------
def get_json(url, params=None, retries=3):
    for i in range(retries):
        try:
            r = http.get(url, params=params, timeout=30)
            if r.status_code == 429:
                time.sleep(2 * (i + 1))
                continue
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            log.warning("طلب فشل (%s): %s", url, e)
            time.sleep(2)
    return None


def send_telegram(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        log.info("تنبيه (بدون تيليجرام):\n%s", text)
        return
    try:
        http.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML",
                  "disable_web_page_preview": True},
            timeout=15,
        )
    except requests.RequestException as e:
        log.error("فشل إرسال تيليجرام: %s", e)


def in_session(now_et):
    if now_et.weekday() >= 5:
        return False
    start = dt.time.fromisoformat(SESSION_START)
    end = dt.time.fromisoformat(SESSION_END)
    return start <= now_et.time() <= end


# ---------------- الفري فلوت (يتحدث مرة يومياً) ----------------
def load_float_map():
    """يرجع قاموس {الرمز: عدد أسهم الفري فلوت}"""
    floats = {}
    # الواجهة الجديدة لـ FMP مع صفحات
    page = 0
    while True:
        data = get_json(
            "https://financialmodelingprep.com/stable/shares-float-all",
            {"page": page, "limit": 5000, "apikey": FMP_API_KEY},
        )
        if not data or not isinstance(data, list):
            break
        for row in data:
            sym, fl = row.get("symbol"), row.get("floatShares")
            if sym and fl:
                floats[sym] = int(fl)
        if len(data) < 5000:
            break
        page += 1

    # احتياط: الواجهة القديمة
    if not floats:
        data = get_json(
            "https://financialmodelingprep.com/api/v4/shares_float/all",
            {"apikey": FMP_API_KEY},
        )
        for row in data or []:
            sym, fl = row.get("symbol"), row.get("floatShares")
            if sym and fl:
                floats[sym] = int(fl)

    log.info("تم تحميل الفري فلوت لـ %d سهم", len(floats))
    return floats


# ---------------- الفلترة الأولية من سناب شوت السوق ----------------
def prefilter(float_map):
    data = get_json(f"{POLY}/v2/snapshot/locale/us/markets/stocks/tickers",
                    {"apiKey": POLYGON_API_KEY})
    if not data:
        return []
    out = []
    for t in data.get("tickers", []):
        sym = t.get("ticker", "")
        price = (t.get("lastTrade") or {}).get("p") or (t.get("min") or {}).get("c") \
            or (t.get("day") or {}).get("c") or 0
        change = t.get("todaysChangePerc") or 0
        day_vol = (t.get("day") or {}).get("v") or 0
        fl = float_map.get(sym)

        if not (MIN_PRICE <= price <= MAX_PRICE):
            continue
        if change > MAX_DAY_CHANGE_PCT:          # مرتفع فوق 20% → يُستبعد
            continue
        if fl is None or not (MIN_FLOAT <= fl <= MAX_FLOAT):
            continue
        if day_vol < MIN_CANDLE_VOLUME:          # مستحيل تكون فيه شمعة بالحجم المطلوب
            continue
        out.append({"symbol": sym, "price": price, "change": change, "float": fl})
    return out


# ---------------- فحص الشموع ----------------
def get_5min_bars(sym, day):
    d = day.isoformat()
    data = get_json(
        f"{POLY}/v2/aggs/ticker/{sym}/range/5/minute/{d}/{d}",
        {"adjusted": "true", "sort": "asc", "limit": 500, "apiKey": POLYGON_API_KEY},
    )
    return (data or {}).get("results", []) or []


def check_signal(sym, now_et):
    bars = get_5min_bars(sym, now_et.date())
    now_ms = int(now_et.timestamp() * 1000)
    # الشموع المقفلة فقط (بداية الشمعة + 5 دقائق <= الآن)
    closed = [b for b in bars if b["t"] + 5 * 60 * 1000 <= now_ms]
    if len(closed) < QUIET_BARS + 1:
        return None

    last = closed[-1]
    # لازم تكون الشمعة جديدة (آخر 5 دقائق)، مو شمعة قديمة
    if now_ms - (last["t"] + 5 * 60 * 1000) > 5 * 60 * 1000:
        return None

    # الشرط: حجم 122 ألف وفوق + شمعة خضراء
    if last["v"] < MIN_CANDLE_VOLUME or last["c"] <= last["o"]:
        return None

    # شرط الركود: الشمعات اللي قبل هادية
    prev = closed[-(QUIET_BARS + 1):-1]
    if any(b["v"] > QUIET_MAX_BAR_VOLUME for b in prev):
        return None
    hi, lo = max(b["h"] for b in prev), min(b["l"] for b in prev)
    if lo <= 0 or (hi - lo) / lo * 100 > QUIET_MAX_RANGE_PCT:
        return None

    return last


def format_alert(c, bar):
    t = dt.datetime.fromtimestamp(bar["t"] / 1000, ET).strftime("%H:%M")
    move = (bar["c"] - bar["o"]) / bar["o"] * 100
    return (
        f"🟢 <b>{c['symbol']}</b> انفجار حجم بعد ركود\n"
        f"شمعة 5د ({t} نيويورك)\n"
        f"الحجم: {int(bar['v']):,}\n"
        f"افتتاح {bar['o']} ← إغلاق {bar['c']} (+{move:.1f}%)\n"
        f"التغير اليومي: {c['change']:.1f}%\n"
        f"الفري فلوت: {c['float']:,}\n"
        f"https://www.tradingview.com/chart/?symbol={c['symbol']}"
    )


# ---------------- الحلقة الرئيسية ----------------
def sleep_to_next_candle():
    """ينام لين تقفل الشمعة الجاية + 10 ثواني عشان تتحدث البيانات"""
    now = dt.datetime.now(ET)
    nxt = (now.replace(second=0, microsecond=0)
           + dt.timedelta(minutes=5 - now.minute % 5, seconds=10))
    time.sleep(max(5, (nxt - now).total_seconds()))


def main():
    if not POLYGON_API_KEY or not FMP_API_KEY:
        raise SystemExit("لازم تحط POLYGON_API_KEY و FMP_API_KEY في متغيرات البيئة")

    float_map, float_day = {}, None
    alerted, alerted_day = set(), None
    send_telegram("✅ السكانر اشتغل")

    while True:
        now = dt.datetime.now(ET)
        today = now.date()

        if alerted_day != today:            # يوم جديد → نصفّر التنبيهات
            alerted, alerted_day = set(), today
        if float_day != today:              # تحديث الفري فلوت يومياً
            float_map = load_float_map() or float_map
            float_day = today

        if in_session(now):
            try:
                cands = [c for c in prefilter(float_map) if c["symbol"] not in alerted]
                log.info("مرشحين: %d", len(cands))
                for c in cands:
                    bar = check_signal(c["symbol"], now)
                    if bar:
                        alerted.add(c["symbol"])     # مرة وحدة بس لكل سهم
                        send_telegram(format_alert(c, bar))
                        log.info("تنبيه: %s", c["symbol"])
            except Exception as e:
                log.exception("خطأ في الدورة: %s", e)

        sleep_to_next_candle()


if __name__ == "__main__":
    main()
