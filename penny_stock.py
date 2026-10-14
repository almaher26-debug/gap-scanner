"""
penny_stock.py - سكانر البيني ستوك على شمعة 5 دقائق (بيانات فورية من ألباكا)
==========================================================================
الشروط:
  1) السعر بين MIN_PRICE و MAX_PRICE (بيني ستوك)
  2) الفري فلوت بين 200 ألف و 20 مليون سهم
  3) آخر شمعة 5 دقائق مقفلة: الحجم 122,000 وفوق + خضراء (الإغلاق أعلى من الافتتاح)
  4) السهم كان راكد قبلها: آخر QUIET_BARS شمعات حجمها صغير والسعر ما تحرك
  5) أي سهم مرتفع فوق 20% اليوم ما ينضاف
  6) التنبيه مرة وحدة بس لكل سهم في اليوم

البيانات:
  - الأسعار والشموع: ألباكا (فيد SIP الفوري) - نفس مفاتيح الـ worker
  - الفري فلوت: ياهو فاينانس (للمرشحين بس، ويتخزن يوم كامل)
  - التنبيهات: تيليجرام

متغيرات البيئة (نفس أسماء الـ worker):
  ALPACAAPIKEY / ALPACA_API_KEY / APCA_API_KEY_ID
  ALPACASECRETKEY / ALPACA_SECRET_KEY / APCA_API_SECRET_KEY
  TELEGRAM_TOKEN, TELEGRAM_CHAT_ID (يقبل أكثر من رقم بينهم فاصلة)
"""

import os
import time
import logging
import datetime as dt
from zoneinfo import ZoneInfo

import requests

# ---------------- المفاتيح ----------------
ALPACA_KEY = (os.environ.get("ALPACAAPIKEY") or os.environ.get("ALPACA_API_KEY")
              or os.environ.get("APCA_API_KEY_ID", ""))
ALPACA_SECRET = (os.environ.get("ALPACASECRETKEY") or os.environ.get("ALPACA_SECRET_KEY")
                 or os.environ.get("APCA_API_SECRET_KEY", ""))
FEED = os.environ.get("PENNY_FEED", os.environ.get("ALGO_FEED", "sip")).lower()
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# ---------------- الشروط (تتغير من متغيرات البيئة) ----------------
MIN_PRICE = float(os.environ.get("PENNY_MIN_PRICE", "0.10"))
MAX_PRICE = float(os.environ.get("PENNY_MAX_PRICE", "5.00"))
MIN_FLOAT = int(os.environ.get("PENNY_MIN_FLOAT", "200000"))
MAX_FLOAT = int(os.environ.get("PENNY_MAX_FLOAT", "20000000"))
MIN_CANDLE_VOLUME = int(os.environ.get("PENNY_MIN_CANDLE_VOLUME", "122000"))
MAX_DAY_CHANGE_PCT = float(os.environ.get("PENNY_MAX_DAY_CHANGE_PCT", "20"))

# شرط الركود
QUIET_BARS = int(os.environ.get("PENNY_QUIET_BARS", "6"))
QUIET_MAX_BAR_VOLUME = int(os.environ.get("PENNY_QUIET_MAX_BAR_VOLUME", "30000"))
QUIET_MAX_RANGE_PCT = float(os.environ.get("PENNY_QUIET_MAX_RANGE_PCT", "3"))

# ساعات الفحص بتوقيت نيويورك (بري ماركت + السوق + أفتر ماركت)
SESSION_START = os.environ.get("PENNY_SESSION_START", "04:00")
SESSION_END = os.environ.get("PENNY_SESSION_END", "20:00")

SCAN_AFTER_CLOSE_SEC = 15      # يفحص بعد إغلاق الشمعة بكذا ثانية عشان تكتمل البيانات

ET = ZoneInfo("America/New_York")
DATA = "https://data.alpaca.markets"
HEADERS = {"APCA-API-KEY-ID": ALPACA_KEY, "APCA-API-SECRET-KEY": ALPACA_SECRET}
BAR_MS = 5 * 60 * 1000

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("penny_stock")
http = requests.Session()
http.headers.update(HEADERS)


# ---------------- أدوات ----------------
def get_json(url, params=None, retries=3):
    for i in range(retries):
        try:
            r = http.get(url, params=params, timeout=30)
            if r.status_code == 429:
                time.sleep(3 * (i + 1))
                continue
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            log.warning("طلب فشل %s: %s", url, e)
            time.sleep(2)
    return None


def send_telegram(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        log.info("تنبيه (بدون تيليجرام):\n%s", text)
        return
    for chat in [c.strip() for c in TELEGRAM_CHAT_ID.split(",") if c.strip()]:
        try:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                          json={"chat_id": chat, "text": text, "parse_mode": "HTML",
                                "disable_web_page_preview": True}, timeout=15)
        except requests.RequestException as e:
            log.error("فشل تيليجرام: %s", e)


def to_ms(ts):
    return int(dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp() * 1000)


def in_session(now):
    if now.weekday() >= 5:
        return False
    return (dt.time.fromisoformat(SESSION_START) <= now.time()
            <= dt.time.fromisoformat(SESSION_END))


# ---------------- قائمة الأسهم (تتحدث يومياً) ----------------
def load_universe():
    for base in ("https://api.alpaca.markets", "https://paper-api.alpaca.markets"):
        data = get_json(f"{base}/v2/assets", {"status": "active", "asset_class": "us_equity"})
        if isinstance(data, list) and data:
            syms = [a["symbol"] for a in data
                    if a.get("tradable") and a.get("exchange") != "OTC"
                    and "." not in a["symbol"] and "/" not in a["symbol"]]
            log.info("قائمة الأسهم: %d سهم", len(syms))
            return syms
    log.error("ما قدرت أجيب قائمة الأسهم من ألباكا")
    return []


# ---------------- الفري فلوت (ياهو، يتخزن يوم) ----------------
_float_cache = {}


def get_float(sym, today):
    hit = _float_cache.get(sym)
    if hit and hit[0] == today:
        return hit[1]
    val = None
    try:
        import yfinance as yf
        v = (yf.Ticker(sym).info or {}).get("floatShares")
        val = int(v) if v else None
    except Exception as e:
        log.debug("فلوت %s: %s", sym, e)
    _float_cache[sym] = (today, val)
    return val


# ---------------- الفلترة الأولية (سناب شوت فوري) ----------------
def prefilter(universe, now):
    today = now.date()
    out = []
    for i in range(0, len(universe), 1000):
        chunk = universe[i:i + 1000]
        data = get_json(f"{DATA}/v2/stocks/snapshots",
                        {"symbols": ",".join(chunk), "feed": FEED}) or {}
        for sym, s in data.items():
            if not s:
                continue
            price = (s.get("latestTrade") or {}).get("p") or 0
            daily, prev = s.get("dailyBar") or {}, s.get("prevDailyBar") or {}
            daily_is_today = daily.get("t") and \
                dt.datetime.fromisoformat(daily["t"].replace("Z", "+00:00")).astimezone(ET).date() == today
            # قبل الافتتاح ممكن يكون dailyBar حق أمس، فنحسب التغير من إغلاقه
            prev_close = prev.get("c") if daily_is_today else daily.get("c")
            if not price or not prev_close:
                continue
            if not (MIN_PRICE <= price <= MAX_PRICE):
                continue
            change = (price / prev_close - 1) * 100
            if change > MAX_DAY_CHANGE_PCT:          # فوق 20% → يُستبعد
                continue
            if daily_is_today and (daily.get("v") or 0) < MIN_CANDLE_VOLUME:
                continue                             # حجم اليوم كله أقل من الشمعة المطلوبة
            out.append({"symbol": sym, "price": price, "change": change})
    return out


# ---------------- شموع 5 دقائق ----------------
def get_bars(symbols, start):
    bars, token = {}, None
    while True:
        params = {"symbols": ",".join(symbols), "timeframe": "5Min", "feed": FEED,
                  "start": start.isoformat(), "limit": 10000, "sort": "asc"}
        if token:
            params["page_token"] = token
        data = get_json(f"{DATA}/v2/stocks/bars", params) or {}
        for sym, lst in (data.get("bars") or {}).items():
            bars.setdefault(sym, []).extend(lst)
        token = data.get("next_page_token")
        if not token:
            return bars


def check_signal(bars, now):
    """bars = شموع سهم واحد. يرجع الشمعة لو تحققت الشروط."""
    now_ms = int(now.timestamp() * 1000)
    last_start = (now_ms // BAR_MS) * BAR_MS - BAR_MS     # الشمعة اللي قفلت توها
    by_t = {to_ms(b["t"]): b for b in bars}
    last = by_t.get(last_start)
    if not last:
        return None

    # حجم 122 ألف وفوق + خضراء
    if last["v"] < MIN_CANDLE_VOLUME or last["c"] <= last["o"]:
        return None

    # الركود: الشمعات اللي قبل (الشمعة الناقصة = ما فيها تداول = راكدة)
    prev = [by_t[t] for t in (last_start - k * BAR_MS for k in range(1, QUIET_BARS + 1))
            if t in by_t]
    if any(b["v"] > QUIET_MAX_BAR_VOLUME for b in prev):
        return None
    if prev:
        hi, lo = max(b["h"] for b in prev), min(b["l"] for b in prev)
        if lo <= 0 or (hi - lo) / lo * 100 > QUIET_MAX_RANGE_PCT:
            return None
    return last


def format_alert(c, bar, flt):
    t = dt.datetime.fromtimestamp(to_ms(bar["t"]) / 1000, ET).strftime("%H:%M")
    move = (bar["c"] - bar["o"]) / bar["o"] * 100
    return (f"🟢 <b>{c['symbol']}</b> بيني ستوك - انفجار حجم بعد ركود\n"
            f"شمعة 5د ({t} نيويورك)\n"
            f"الحجم: {int(bar['v']):,}\n"
            f"افتتاح {bar['o']} ← إغلاق {bar['c']} (+{move:.1f}%)\n"
            f"التغير اليومي: {c['change']:.1f}%\n"
            f"الفري فلوت: {flt:,}\n"
            f"https://www.tradingview.com/chart/?symbol={c['symbol']}")


# ---------------- الدورة ----------------
def scan_once(universe, alerted, now):
    cands = [c for c in prefilter(universe, now) if c["symbol"] not in alerted]
    log.info("مرشحين بعد السعر والتغير والحجم: %d", len(cands))
    if not cands:
        return
    start = now - dt.timedelta(minutes=5 * (QUIET_BARS + 3))
    all_bars = {}
    for i in range(0, len(cands), 200):
        all_bars.update(get_bars([c["symbol"] for c in cands[i:i + 200]], start))
    for c in cands:
        bar = check_signal(all_bars.get(c["symbol"], []), now)
        if not bar:
            continue
        flt = get_float(c["symbol"], now.date())     # الفلوت للي نجح بس (أسرع)
        if flt is None or not (MIN_FLOAT <= flt <= MAX_FLOAT):
            continue
        alerted.add(c["symbol"])                       # مرة وحدة بس
        send_telegram(format_alert(c, bar, flt))
        log.info("تنبيه: %s", c["symbol"])


def sleep_to_next_candle():
    now = dt.datetime.now(ET)
    nxt = (now.replace(second=0, microsecond=0)
           + dt.timedelta(minutes=5 - now.minute % 5, seconds=SCAN_AFTER_CLOSE_SEC))
    time.sleep(max(5, (nxt - now).total_seconds()))


def main():
    if not ALPACA_KEY or not ALPACA_SECRET:
        raise SystemExit("لازم مفاتيح ألباكا: ALPACAAPIKEY و ALPACASECRETKEY")
    log.info("سكانر البيني ستوك اشتغل (ألباكا %s)", FEED)
    universe, uni_day = [], None
    alerted, alerted_day = set(), None
    while True:
        now = dt.datetime.now(ET)
        if alerted_day != now.date():
            alerted, alerted_day = set(), now.date()
        if uni_day != now.date() or not universe:
            universe = load_universe() or universe
            uni_day = now.date()
        if in_session(now):
            try:
                scan_once(universe, alerted, now)
            except Exception as e:
                log.exception("خطأ في الدورة: %s", e)
        sleep_to_next_candle()


if __name__ == "__main__":
    main()
