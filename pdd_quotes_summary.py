# -*- coding: utf-8 -*-
"""
ملخص الطلب والعرض (Bid / Ask) لسهم خلال فترة معينة - من ألباكا - ويرسله برسالة وحدة على تيليجرام
=====================================================================================
الافتراضي: سهم PDD يوم الإثنين 12 أكتوبر 2026، من 4:30 العصر لين 11 بالليل بتوقيت السعودية.

متغيرات البيئة (نفس اللي عندك في Railway):
    ALPACAAPIKEY  ALPACASECRETKEY  TELEGRAM_TOKEN  TELEGRAM_CHAT_ID

التشغيل:
    python pdd_quotes_summary.py
    python pdd_quotes_summary.py PDD 2026-10-12 16:30 23:00
    python pdd_quotes_summary.py NVDA 2026-10-13 16:30 23:00
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
FEED = os.environ.get("QUOTES_FEED", "sip").lower()

SYMBOL = "PDD"
DATE = "2026-10-12"        # يوم الإثنين
FROM_TIME = "16:30"        # بتوقيت السعودية
TO_TIME = "23:00"          # بتوقيت السعودية
LOCAL_TZ = "Asia/Riyadh"
QUOTES_URL = "https://data.alpaca.markets/v2/stocks/{sym}/quotes"
DISCLAIMER = "⚠️ محتوى تعليمي فقط، وليس توصية بيع أو شراء."
# =============================================


def log(*a):
    print(pd.Timestamp.now(tz=LOCAL_TZ).strftime("%H:%M:%S"), *a, flush=True)


def fetch_quotes(sym, start, end, on_page):
    """يسحب كل اقتباسات الطلب والعرض صفحة صفحة، ويمرر كل صفحة لـ on_page بدون ما يخزنها كلها."""
    headers = {"APCA-API-KEY-ID": ALPACA_KEY, "APCA-API-SECRET-KEY": ALPACA_SECRET}
    params = {"start": start.tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
              "end": end.tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
              "limit": 10000, "feed": FEED, "sort": "asc"}
    url, pages = QUOTES_URL.format(sym=sym), 0
    while True:
        r = requests.get(url, headers=headers, params=params, timeout=30)
        if r.status_code == 429:
            time.sleep(3)
            continue
        if r.status_code != 200:
            raise RuntimeError(f"ألباكا: خطأ {r.status_code} - {r.text[:200]}")
        data = r.json()
        on_page(data.get("quotes") or [])
        pages += 1
        if pages % 50 == 0:
            log(f"سحبت {pages} صفحة...")
        token = data.get("next_page_token")
        if not token:
            return
        params["page_token"] = token


class Summary:
    """يجمّع الملخص أول بأول (يشتغل حتى لو الاقتباسات ملايين)."""

    def __init__(self):
        self.count = 0
        self.first = self.last = None
        self.max_bid = self.min_ask = None
        self.spread_sum = 0.0
        self.spread_n = 0
        self.big_bid = self.big_ask = None    # أكبر كمية طلب / عرض
        self.bid_size_sum = self.ask_size_sum = 0

    def add(self, quotes):
        for q in quotes:
            bp, ap = float(q.get("bp") or 0), float(q.get("ap") or 0)
            bs, as_ = int(q.get("bs") or 0), int(q.get("as") or 0)
            t = q.get("t")
            if bp <= 0 or ap <= 0 or ap < bp:      # اقتباس ناقص أو مقلوب - نتجاهله
                continue
            self.count += 1
            if self.first is None:
                self.first = (t, bp, ap)
            self.last = (t, bp, ap)
            if self.max_bid is None or bp > self.max_bid[1]:
                self.max_bid = (t, bp)
            if self.min_ask is None or ap < self.min_ask[1]:
                self.min_ask = (t, ap)
            self.spread_sum += ap - bp
            self.spread_n += 1
            self.bid_size_sum += bs
            self.ask_size_sum += as_
            if self.big_bid is None or bs > self.big_bid[2]:
                self.big_bid = (t, bp, bs)
            if self.big_ask is None or as_ > self.big_ask[2]:
                self.big_ask = (t, ap, as_)


def tlocal(t):
    return pd.Timestamp(t).tz_convert(LOCAL_TZ).strftime("%H:%M")


def build_message(sym, date, frm, to, s):
    if not s.count:
        return f"📊 {sym} - {date} ({frm} ← {to})\nما فيه بيانات طلب وعرض في هالفترة."
    bid_pct = 100 * s.bid_size_sum / max(1, s.bid_size_sum + s.ask_size_sum)
    lines = [
        f"📊 الطلب والعرض - ${sym}",
        f"{date} | {frm} ← {to} (توقيتك)",
        f"عدد الاقتباسات: {s.count:,}",
        "",
        f"البداية ({tlocal(s.first[0])}): طلب {s.first[1]:.2f} | عرض {s.first[2]:.2f}",
        f"النهاية ({tlocal(s.last[0])}): طلب {s.last[1]:.2f} | عرض {s.last[2]:.2f}",
        f"🟢 أعلى طلب: {s.max_bid[1]:.2f} ({tlocal(s.max_bid[0])})",
        f"🔴 أقل عرض: {s.min_ask[1]:.2f} ({tlocal(s.min_ask[0])})",
        f"متوسط السبريد: {s.spread_sum / s.spread_n:.3f}$",
        "",
        f"أكبر طلب: {s.big_bid[2]:,} سهم عند {s.big_bid[1]:.2f} ({tlocal(s.big_bid[0])})",
        f"أكبر عرض: {s.big_ask[2]:,} سهم عند {s.big_ask[1]:.2f} ({tlocal(s.big_ask[0])})",
        f"قوة الطلب: {bid_pct:.0f}% طلب | {100 - bid_pct:.0f}% عرض",
    ]
    return "\n".join(lines)


def send_telegram(text):
    text = text + "\n\n" + DISCLAIMER
    print(text)
    if not TELEGRAM_TOKEN:
        log("⚠️ TELEGRAM_TOKEN ناقص - طبعت الرسالة بس")
        return
    for chat_id in [c.strip() for c in TELEGRAM_CHAT_ID.split(",") if c.strip()]:
        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                          data={"chat_id": chat_id, "text": text}, timeout=10).json()
        if not r.get("ok"):
            log(f"فشل الإرسال لـ {chat_id}: {r.get('description')}")


def main():
    args = sys.argv[1:]
    sym = (args[0] if len(args) > 0 else SYMBOL).upper()
    date = args[1] if len(args) > 1 else DATE
    frm = args[2] if len(args) > 2 else FROM_TIME
    to = args[3] if len(args) > 3 else TO_TIME
    if not (ALPACA_KEY and ALPACA_SECRET):
        log("❌ يحتاج ALPACAAPIKEY و ALPACASECRETKEY")
        sys.exit(1)
    start = pd.Timestamp(f"{date} {frm}", tz=LOCAL_TZ)
    end = pd.Timestamp(f"{date} {to}", tz=LOCAL_TZ)
    log(f"أسحب الطلب والعرض لـ {sym} من {start} إلى {end} (feed={FEED})...")
    s = Summary()
    fetch_quotes(sym, start, end, s.add)
    send_telegram(build_message(sym, date, frm, to, s))


if __name__ == "__main__":
    main()
