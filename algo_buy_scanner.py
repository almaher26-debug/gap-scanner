"""
سكنر قاب أب + سيولة شراء ضخمة — السوق الأمريكي
الشروط:
  - السعر بين 1 و 10 دولار
  - القيمة السوقية تحت 100 مليون دولار
  - قاب أب (افتتاح اليوم أعلى من إغلاق أمس)
  - حجم شراء فوق 200 ألف سهم في شمعة الدقيقة
يرسل التنبيه على تيليجرام.
"""

import os
import time
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

# ===== المتغيرات (من إعدادات السيرفر) =====
POLYGON_API_KEY = os.environ["POLYGON_API_KEY"]
TG_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TG_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

MIN_PRICE = float(os.getenv("MIN_PRICE", "1"))
MAX_PRICE = float(os.getenv("MAX_PRICE", "10"))
MAX_MCAP = float(os.getenv("MAX_MCAP", "100000000"))      # 100 مليون $
MIN_GAP_PCT = float(os.getenv("MIN_GAP_PCT", "2"))         # أقل نسبة قاب %
MIN_BUY = float(os.getenv("MIN_BUY", "200000"))            # أقل شراء في الدقيقة
BUY_MODE = os.getenv("BUY_MODE", "shares")                 # shares أو dollars
SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", "15"))      # ثواني بين كل فحص
EXTENDED_HOURS = os.getenv("EXTENDED_HOURS", "true").lower() == "true"

BASE = "https://api.polygon.io"
ET = ZoneInfo("America/New_York")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("gap-scanner")
http = requests.Session()

shares_cache: dict[str, float | None] = {}
alerted: set[tuple[str, int]] = set()
current_day = None


# ===== أدوات =====
def market_is_open() -> bool:
    now = datetime.now(ET)
    if now.weekday() >= 5:
        return False
    minutes = now.hour * 60 + now.minute
    if EXTENDED_HOURS:
        return 4 * 60 <= minutes < 20 * 60          # 4:00 ص – 8:00 م بتوقيت نيويورك
    return 9 * 60 + 30 <= minutes < 16 * 60          # 9:30 ص – 4:00 م


def send_telegram(text: str) -> None:
    try:
        http.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "HTML",
                  "disable_web_page_preview": True},
            timeout=15,
        )
    except requests.RequestException as e:
        log.error("Telegram error: %s", e)


def get_snapshot() -> list[dict]:
    r = http.get(f"{BASE}/v2/snapshot/locale/us/markets/stocks/tickers",
                 params={"apiKey": POLYGON_API_KEY}, timeout=30)
    r.raise_for_status()
    return r.json().get("tickers", []) or []


def get_market_cap(ticker: str, price: float) -> float | None:
    """القيمة السوقية = السعر الحالي × عدد الأسهم (عدد الأسهم يُحفظ في الكاش)."""
    if ticker not in shares_cache:
        try:
            r = http.get(f"{BASE}/v3/reference/tickers/{ticker}",
                         params={"apiKey": POLYGON_API_KEY}, timeout=15)
            res = r.json().get("results", {}) if r.ok else {}
            shares = res.get("share_class_shares_outstanding") or res.get("weighted_shares_outstanding")
            if not shares and res.get("market_cap") and price:
                shares = res["market_cap"] / price
            shares_cache[ticker] = shares
        except requests.RequestException as e:
            log.warning("market cap error %s: %s", ticker, e)
            return None
    shares = shares_cache.get(ticker)
    return shares * price if shares else None


def estimate_buy(bar: dict) -> float:
    """تقدير حجم الشراء: كلما أغلقت الشمعة قرب أعلاها زادت حصة المشترين."""
    h, l, c, v = bar.get("h", 0), bar.get("l", 0), bar.get("c", 0), bar.get("v", 0)
    rng = h - l
    buy_vol = v * (c - l) / rng if rng > 0 else v * 0.5
    return buy_vol * c if BUY_MODE == "dollars" else buy_vol


def fmt(n: float) -> str:
    if n >= 1e9:
        return f"{n / 1e9:.2f}B"
    if n >= 1e6:
        return f"{n / 1e6:.2f}M"
    if n >= 1e3:
        return f"{n / 1e3:.1f}K"
    return f"{n:.0f}"


# ===== الفحص =====
def scan() -> int:
    hits = 0
    for t in get_snapshot():
        sym = t.get("ticker")
        day = t.get("day") or {}
        prev = t.get("prevDay") or {}
        bar = t.get("min") or {}

        last = (t.get("lastTrade") or {}).get("p") or bar.get("c") or day.get("c")
        prev_close = prev.get("c")
        if not sym or not last or not prev_close:
            continue

        # 1) السعر
        if not (MIN_PRICE <= last <= MAX_PRICE):
            continue

        # 2) القاب أب
        day_open = day.get("o") or last          # قبل الافتتاح نستخدم آخر سعر
        gap_pct = (day_open - prev_close) / prev_close * 100
        if gap_pct < MIN_GAP_PCT:
            continue

        # 3) الشراء في الدقيقة
        if not bar.get("v"):
            continue
        buy = estimate_buy(bar)
        if buy < MIN_BUY:
            continue

        # 4) القيمة السوقية (آخر شرط لأنه يحتاج طلب إضافي)
        mcap = get_market_cap(sym, last)
        if mcap is None or mcap > MAX_MCAP:
            continue

        key = (sym, bar.get("t", 0))
        if key in alerted:
            continue
        alerted.add(key)
        hits += 1

        change = t.get("todaysChangePerc", 0) or 0
        unit = "$" if BUY_MODE == "dollars" else "سهم"
        msg = (
            f"🚨 <b>دخول شراء قوي — {sym}</b>\n"
            f"💵 السعر: {last:.2f}$ ({change:+.1f}%)\n"
            f"📈 قاب أب: {gap_pct:+.1f}%\n"
            f"🟢 شراء بالدقيقة: {fmt(buy)} {unit}\n"
            f"📊 حجم الدقيقة: {fmt(bar.get('v', 0))}\n"
            f"🏷 القيمة السوقية: {fmt(mcap)}$\n"
            f"🔗 https://www.tradingview.com/chart/?symbol={sym}"
        )
        send_telegram(msg)
        log.info("ALERT %s gap=%.1f%% buy=%s mcap=%s", sym, gap_pct, fmt(buy), fmt(mcap))
    return hits


def main() -> None:
    global current_day
    log.info("Gap scanner started")
    send_telegram(
        f"✅ السكنر اشتغل\nالسعر {MIN_PRICE:g}–{MAX_PRICE:g}$ | قيمة سوقية &lt; {fmt(MAX_MCAP)}$\n"
        f"قاب ≥ {MIN_GAP_PCT:g}% | شراء ≥ {fmt(MIN_BUY)} بالدقيقة"
    )
    while True:
        today = datetime.now(ET).date()
        if today != current_day:          # تصفير يومي
            current_day = today
            alerted.clear()
            shares_cache.clear()

        if market_is_open():
            try:
                hits = scan()
                log.info("scan done, %d alerts", hits)
            except Exception as e:
                log.exception("scan error: %s", e)
            time.sleep(SCAN_INTERVAL)
        else:
            time.sleep(60)


if __name__ == "__main__":
    main()
