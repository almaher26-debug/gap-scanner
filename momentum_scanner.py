"""
سكنر أسهم الزخم (Momentum Scanner)
يفحص أكثر الأسهم حركة وتداولاً عبر Alpaca، ويرسل تنبيه تيليجرام
لما يتحقق: ارتفاع قوي + فوليوم نسبي عالي + قريب من أعلى سعر لليوم.

المتغيرات المطلوبة (نفس سكنراتك الحالية):
  ALPACAAPIKEY, ALPACASECRETKEY, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

إعدادات اختيارية (لها قيم افتراضية):
  MIN_PRICE=1  MAX_PRICE=50  MIN_CHANGE=10  MIN_RVOL=2
  MIN_VOLUME=500000  NEAR_HIGH_PCT=2  SCAN_EVERY=60
"""

import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo

API_KEY = os.environ.get("ALPACAAPIKEY", "")
API_SECRET = os.environ.get("ALPACASECRETKEY", "")
TG_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID", "")

MIN_PRICE = float(os.environ.get("MIN_PRICE", 1))
MAX_PRICE = float(os.environ.get("MAX_PRICE", 50))
MIN_CHANGE = float(os.environ.get("MIN_CHANGE", 10))        # % فوق إغلاق أمس
MIN_RVOL = float(os.environ.get("MIN_RVOL", 2))             # فوليوم نسبي
MIN_VOLUME = float(os.environ.get("MIN_VOLUME", 500_000))   # فوليوم اليوم
NEAR_HIGH_PCT = float(os.environ.get("NEAR_HIGH_PCT", 2))   # بُعد السعر عن قمة اليوم %
SCAN_EVERY = int(os.environ.get("SCAN_EVERY", 60))          # ثواني بين كل فحص

DATA_URL = "https://data.alpaca.markets"
ET = ZoneInfo("America/New_York")
RIYADH = ZoneInfo("Asia/Riyadh")
MARKET_OPEN = dtime(9, 30)
MARKET_CLOSE = dtime(16, 0)

# آخر مستوى تنبيه لكل سهم اليوم (10%، 20%، 30%...) عشان ما يتكرر التنبيه
alerted_levels: dict[str, int] = {}
current_day = None


def log(msg: str) -> None:
    print(f"{datetime.now(RIYADH):%H:%M:%S} {msg}", flush=True)


def alpaca_get(path: str, params: dict | None = None) -> dict:
    url = DATA_URL + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "APCA-API-KEY-ID": API_KEY,
        "APCA-API-SECRET-KEY": API_SECRET,
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def send_telegram(text: str) -> None:
    if not TG_TOKEN or not TG_CHAT:
        log("⚠️ متغيرات تيليجرام ناقصة")
        return
    data = urllib.parse.urlencode({
        "chat_id": TG_CHAT, "text": text, "disable_web_page_preview": "true",
    }).encode()
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        urllib.request.urlopen(url, data=data, timeout=20).read()
    except Exception as e:
        log(f"خطأ تيليجرام: {e}")


def market_is_open(now_et: datetime) -> bool:
    if now_et.weekday() >= 5:
        return False
    return MARKET_OPEN <= now_et.time() < MARKET_CLOSE


def session_fraction(now_et: datetime) -> float:
    """نسبة الوقت المنقضي من الجلسة (لحساب الفوليوم النسبي بعدل)."""
    start = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
    elapsed = (now_et - start).total_seconds() / 60
    return min(max(elapsed / 390, 0.03), 1.0)


def get_candidates() -> list[str]:
    """أكثر الأسهم ارتفاعاً + أكثرها تداولاً."""
    symbols: set[str] = set()
    try:
        movers = alpaca_get("/v1beta1/screener/stocks/movers", {"top": 50})
        for g in movers.get("gainers", []):
            symbols.add(g["symbol"])
    except Exception as e:
        log(f"خطأ movers: {e}")
    try:
        actives = alpaca_get("/v1beta1/screener/stocks/most-actives",
                             {"by": "volume", "top": 100})
        for a in actives.get("most_actives", []):
            symbols.add(a["symbol"])
    except Exception as e:
        log(f"خطأ most-actives: {e}")
    # نستبعد الوارنتس والرايتس واليونتس
    return [s for s in symbols if s.isalpha() and len(s) <= 5]


def get_snapshots(symbols: list[str]) -> dict:
    out: dict = {}
    for i in range(0, len(symbols), 100):
        chunk = symbols[i:i + 100]
        try:
            out.update(alpaca_get("/v2/stocks/snapshots",
                                  {"symbols": ",".join(chunk), "feed": "sip"}))
        except Exception as e:
            log(f"خطأ snapshots: {e}")
    return out


def check_symbol(sym: str, snap: dict, frac: float) -> str | None:
    daily = snap.get("dailyBar") or {}
    prev = snap.get("prevDailyBar") or {}
    trade = snap.get("latestTrade") or {}
    minute = snap.get("minuteBar") or {}

    price = trade.get("p") or daily.get("c")
    prev_close = prev.get("c")
    if not price or not prev_close:
        return None
    if not (MIN_PRICE <= price <= MAX_PRICE):
        return None

    change = (price - prev_close) / prev_close * 100
    if change < MIN_CHANGE:
        return None

    vol = daily.get("v", 0)
    if vol < MIN_VOLUME:
        return None

    prev_vol = prev.get("v") or 0
    rvol = vol / (prev_vol * frac) if prev_vol else 99.0
    if rvol < MIN_RVOL:
        return None

    high = daily.get("h") or price
    from_high = (high - price) / high * 100 if high else 0
    if from_high > NEAR_HIGH_PCT:
        return None

    # تنبيه مرة لكل مستوى: 10% ثم 20% ثم 30%...
    level = int(change // 10) * 10
    previous = alerted_levels.get(sym, 0)
    if previous >= level:
        return None
    alerted_levels[sym] = level

    first = "🆕 أول تنبيه اليوم" if previous == 0 else f"🔼 كسر مستوى +{level}%"
    now_local = datetime.now(RIYADH)
    return (
        f"🚀 زخم - ${sym}\n"
        f"{first}\n\n"
        f"السعر: {price:.2f}$\n"
        f"التغير: +{change:.1f}%\n"
        f"قمة اليوم: {high:.2f}$ (يبعد {from_high:.1f}%)\n"
        f"الفوليوم: {vol:,.0f}\n"
        f"الفوليوم النسبي: {rvol:.1f}x\n"
        f"فوليوم آخر دقيقة: {minute.get('v', 0):,.0f}\n"
        f"الوقت: {now_local:%H:%M} (توقيتك)\n\n"
        f"⚠️ محتوى تعليمي فقط، وليس توصية بيع أو شراء."
    )


def scan_once() -> None:
    now_et = datetime.now(ET)
    frac = session_fraction(now_et)
    symbols = get_candidates()
    if not symbols:
        log("ما فيه مرشحين")
        return
    snaps = get_snapshots(symbols)
    hits = 0
    for sym, snap in snaps.items():
        msg = check_symbol(sym, snap, frac)
        if msg:
            send_telegram(msg)
            hits += 1
            time.sleep(0.5)
    log(f"فحصت {len(snaps)} سهم — {hits} تنبيه")


def main() -> None:
    global current_day
    if not API_KEY or not API_SECRET:
        log("❌ مفاتيح Alpaca ناقصة")
        return
    log("✅ سكنر الزخم بدأ")
    send_telegram("✅ سكنر الزخم اشتغل")
    waiting_logged = False
    while True:
        now_et = datetime.now(ET)
        if current_day != now_et.date():
            current_day = now_et.date()
            alerted_levels.clear()
        if market_is_open(now_et):
            waiting_logged = False
            try:
                scan_once()
            except Exception as e:
                log(f"خطأ في الفحص: {e}")
            time.sleep(SCAN_EVERY)
        else:
            if not waiting_logged:
                log("السوق مسكر — أنتظر الافتتاح")
                waiting_logged = True
            time.sleep(60)


if __name__ == "__main__":
    main()
