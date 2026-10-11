"""
Finviz Stock News -> Telegram alerts
- يسحب أخبار الأسهم من Finviz (Stocks News)
- يفلتر الأسهم اللي سعرها بين MIN_PRICE و MAX_PRICE (افتراضياً 1$ - 5$)
- يشتغل بس من START_TIME إلى END_TIME (افتراضياً 11:00 - 16:30 بتوقيت الرياض)
- يرسل تنبيه على تيليجرام لكل خبر جديد
"""

import os
import re
import sys
import json
import time
import html
import logging
import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo


# ===================== تثبيت المكتبات تلقائياً =====================
def _ensure(pkg, import_name=None):
    try:
        __import__(import_name or pkg)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", pkg])


_ensure("requests")
_ensure("beautifulsoup4", "bs4")
_ensure("yfinance")
_ensure("tzdata")

import requests
import yfinance as yf
from bs4 import BeautifulSoup

# ===================== الإعدادات =====================
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

MIN_PRICE = float(os.getenv("MIN_PRICE", "1"))
MAX_PRICE = float(os.getenv("MAX_PRICE", "5"))
START_TIME = os.getenv("START_TIME", "11:00")
END_TIME = os.getenv("END_TIME", "16:30")
TIMEZONE = ZoneInfo(os.getenv("TIMEZONE", "Asia/Riyadh"))
WEEKDAYS_ONLY = os.getenv("WEEKDAYS_ONLY", "true").lower() == "true"
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "60"))
SEEN_FILE = os.getenv("SEEN_FILE", "seen.json")

NEWS_URL = "https://finviz.com/news.ashx?v=3"  # Stocks News
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("finviz-bot")


# ===================== الوقت =====================
def _parse_hm(s):
    h, m = s.split(":")
    return int(h) * 60 + int(m)


def in_window():
    now = datetime.now(TIMEZONE)
    if WEEKDAYS_ONLY and now.weekday() >= 5:  # السبت والأحد
        return False
    minutes = now.hour * 60 + now.minute
    return _parse_hm(START_TIME) <= minutes <= _parse_hm(END_TIME)


# ===================== الأخبار المرسلة =====================
def load_seen():
    try:
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_seen(seen):
    try:
        with open(SEEN_FILE, "w") as f:
            json.dump(list(seen)[-5000:], f)
    except Exception as e:
        log.warning("Could not save seen file: %s", e)


# ===================== سحب الأخبار =====================
TICKER_RE = re.compile(r"quote\.ashx\?t=([A-Z0-9.\-]+)")


def fetch_news():
    r = requests.get(NEWS_URL, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    items, urls = [], set()
    for row in soup.find_all("tr"):
        if row.find("tr"):  # تجاهل الجداول الخارجية
            continue

        tickers = []
        for a in row.find_all("a", href=True):
            m = TICKER_RE.search(a["href"])
            if m and m.group(1) not in tickers:
                tickers.append(m.group(1))
        if not tickers:
            continue

        links = [a for a in row.find_all("a", href=True) if "quote.ashx" not in a["href"]]
        if not links:
            continue
        a = max(links, key=lambda x: len(x.get_text(strip=True)))
        title = a.get_text(" ", strip=True)
        if len(title) < 15:
            continue

        url = a["href"]
        if url.startswith("/"):
            url = "https://finviz.com" + url
        if url in urls:
            continue
        urls.add(url)

        tds = row.find_all("td")
        when = tds[0].get_text(" ", strip=True) if tds else ""
        items.append({"title": title, "url": url, "tickers": tickers, "when": when})
    return items


# ===================== الأسعار =====================
_price_cache = {}


def get_price(ticker):
    now = time.time()
    cached = _price_cache.get(ticker)
    if cached and now - cached[1] < 600:  # كاش 10 دقايق
        return cached[0]
    price = None
    try:
        price = float(yf.Ticker(ticker).fast_info["last_price"])
    except Exception as e:
        log.debug("Price error %s: %s", ticker, e)
    _price_cache[ticker] = (price, now)
    return price


# ===================== تيليجرام =====================
def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(
            url,
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": "true",
            },
            timeout=15,
        )
        if r.status_code != 200:
            log.warning("Telegram error: %s", r.text)
    except Exception as e:
        log.warning("Telegram send failed: %s", e)


def format_alert(item, matches):
    tick_str = " | ".join(f"<b>${t}</b> {p:.2f}$" for t, p in matches)
    return (
        f"📰 {tick_str}\n\n"
        f"{html.escape(item['title'])}\n\n"
        f"🔗 <a href=\"{html.escape(item['url'])}\">رابط الخبر</a>\n\n"
        f"⚠️ ليست توصية بيع أو شراء، محتوى تعليمي فقط"
    )


# ===================== التشغيل =====================
def main():
    seen = load_seen()
    first_run = not seen

    log.info("Bot started | price %.2f-%.2f | window %s-%s %s",
             MIN_PRICE, MAX_PRICE, START_TIME, END_TIME, TIMEZONE)
    send_telegram(f"✅ البوت اشتغل\nالسعر: {MIN_PRICE}$ - {MAX_PRICE}$\n"
                  f"الوقت: {START_TIME} - {END_TIME}")

    while True:
        try:
            if not in_window():
                time.sleep(POLL_SECONDS)
                continue

            news = fetch_news()

            # أول تشغيل: نعلّم الأخبار الموجودة كمقروءة عشان ما ينهال عليك سيل تنبيهات
            if first_run:
                seen.update(n["url"] for n in news)
                save_seen(seen)
                first_run = False
                log.info("Initial %d items marked as seen", len(news))
                time.sleep(POLL_SECONDS)
                continue

            new_items = [n for n in news if n["url"] not in seen]
            for item in reversed(new_items):  # الأقدم أولاً
                seen.add(item["url"])
                matches = []
                for t in item["tickers"]:
                    p = get_price(t)
                    if p is not None and MIN_PRICE <= p <= MAX_PRICE:
                        matches.append((t, p))
                if matches:
                    send_telegram(format_alert(item, matches))
                    log.info("Alert: %s %s", [m[0] for m in matches], item["title"])
                    time.sleep(1)

            if new_items:
                save_seen(seen)

        except Exception as e:
            log.error("Loop error: %s", e)

        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
