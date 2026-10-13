# -*- coding: utf-8 -*-
"""
سكانر أخبار البيني ستوك (ملف مستقل)
====================================
- يسحب الأخبار الفورية من ألباكا كل كم ثانية (24 ساعة، كل الأيام)
- يرسل الأخبار الإيجابية بس (اندماج، FDA، عقود، نتائج قوية...) ويتجاهل السلبية
- فلتر السعر: من 1$ إلى 10$ (السعر اللحظي من ألباكا SIP)
- يرسل على تيليجرام

متغيرات Railway المطلوبة:
    ALPACAAPIKEY        مفتاح ألباكا
    ALPACASECRETKEY     السر حق ألباكا
    TELEGRAM_TOKEN      توكن البوت
    TELEGRAM_CHAT_ID    رقم المحادثة (أكثر من رقم بينهم فاصلة)

اختياري:
    NEWS_MIN_PRICE=1    NEWS_MAX_PRICE=10    NEWS_POLL_SEC=15
    NEWS_MAX_MARKET_CAP=0   (مثلاً 100000000 = يرسل بس الأسهم اللي قيمتها أقل من 100 مليون)

التشغيل:
    python news_scanner.py          # يشتغل
    python news_scanner.py --test   # يجرب التصنيف بدون نت
"""

import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests

# ================= الإعدادات =================
ALPACA_KEY = (os.environ.get("ALPACAAPIKEY") or os.environ.get("ALPACA_API_KEY")
              or os.environ.get("APCA_API_KEY_ID", ""))
ALPACA_SECRET = (os.environ.get("ALPACASECRETKEY") or os.environ.get("ALPACA_SECRET_KEY")
                 or os.environ.get("APCA_API_SECRET_KEY", ""))
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

NEWS_MIN_PRICE = float(os.environ.get("NEWS_MIN_PRICE", "1"))     # أقل سعر
NEWS_MAX_PRICE = float(os.environ.get("NEWS_MAX_PRICE", "10"))    # أعلى سعر
NEWS_POLL_SEC = int(os.environ.get("NEWS_POLL_SEC", "15"))        # كل كم ثانية يسحب
NEWS_MAX_AGE_MIN = 30          # يتجاهل الخبر اللي عمره أكثر من كذا دقيقة
NEWS_MAX_SYMBOLS = 3           # يتجاهل الخبر اللي فيه أكثر من كذا سهم (ملخصات السوق)
NEWS_MAX_MARKET_CAP = float(os.environ.get("NEWS_MAX_MARKET_CAP", "0"))   # 0 = بدون حد
PRICE_FEED = os.environ.get("ALGO_FEED", "sip").lower()   # sip = كل السوق (فوري مع Algo Trader Plus)

NEWS_URL = "https://data.alpaca.markets/v1beta1/news"
SNAP_URL = "https://data.alpaca.markets/v2/stocks/snapshots"
SENT_FILE = "news_sent.txt"
SENT_KEEP_LINES = 20000
LOCAL_TZ = ZoneInfo("Asia/Riyadh")
DISCLAIMER = "⚠️ محتوى تعليمي فقط، وليس توصية بيع أو شراء."
HEADERS = {"User-Agent": "Mozilla/5.0"}
# =============================================

NEWS_POSITIVE = [
    ("🤝 اندماج / استحواذ", r"\bmerger\b|\bmerge\b|\bto merge\b|\bacquir|\bacquisition\b|\bbuyout\b|"
                            r"\btakeover\b|\bdefinitive agreement\b|\btender offer\b|\bgo(ing)? private\b|"
                            r"\bto be acquired\b|\bbusiness combination\b"),
    ("💊 موافقة FDA", r"\bfda\b.*\b(approv|clear|grant)|\bapproval\b|\bapproved\b|\bclearance\b|"
                     r"\bbreakthrough therapy\b|\bfast track\b|\borphan drug\b|\bpriority review\b"),
    ("🧪 نتائج دراسة إيجابية", r"\bpositive (topline|results|data|phase)|\bmet (its |the )?primary endpoint|"
                              r"\bstatistically significant\b"),
    ("📝 عقد / شراكة", r"\bcontract\b|\bawarded\b|\bwins\b.*\b(order|deal|contract)|\bpartnership\b|"
                      r"\bpartners with\b|\bcollaboration\b|\bstrategic alliance\b|\bselected by\b|"
                      r"\bpurchase order\b|\blicens(e|ing) agreement\b|\bsupply agreement\b"),
    ("📈 نتائج / توقعات قوية", r"\bbeats?\b|\btops?\b.*\bestimates\b|\brecord (revenue|quarter|sales|results)|"
                              r"\braises?\b.*\b(guidance|outlook|forecast)|\bboosts?\b.*\b(guidance|outlook)|"
                              r"\bexceeds?\b.*\b(expectations|estimates)"),
    ("⬆️ ترقية محلل", r"\bupgrades?\b|\bupgraded\b|\braises?\b.*\bprice target\b|"
                     r"\binitiates?\b.*\b(buy|outperform|overweight)"),
    ("💵 إعادة شراء / توزيعات", r"\bbuyback\b|\b(share|stock) repurchase\b|\bspecial dividend\b|"
                               r"\b(raises|increases|boosts) (quarterly )?dividend\b"),
]
# لو العنوان فيه أي وحدة من هذي، يتجاهل الخبر حتى لو فيه كلمة إيجابية
NEWS_NEGATIVE = (r"\boffering\b|\bdilut|\bpriced\b|\bregistered direct\b|\bprivate placement\b|\bwarrants?\b|"
                 r"\breverse (stock )?split\b|\blawsuit\b|\bclass action\b|\binvestigat|\bshareholder alert\b|"
                 r"\blaw firm\b|\bfair to\b|\bdowngrad|\bmiss(es|ed)?\b|\b(cuts|lowers|slashes|withdraws)\b|"
                 r"\bbankrupt|\bchapter 11\b|\bdelist|\bterminat|\bhalt|\bwarning\b|\bfalls?\b|\bplunge|"
                 r"\bslump|\btumble|\bsinks?\b|\bshort (seller|report)\b|\bsec charges\b|\brecall\b|"
                 r"\bcomplete response letter\b|\bcrl\b|\brejects?\b|\bdenied\b|\bfails?\b|\bdelay")
_NEWS_POS = [(name, re.compile(rx, re.I)) for name, rx in NEWS_POSITIVE]
_NEWS_NEG = re.compile(NEWS_NEGATIVE, re.I)


def log(*a):
    print(datetime.now(LOCAL_TZ).strftime("%H:%M:%S"), *a, flush=True)


def classify_news(headline):
    """يرجع اسم التصنيف لو الخبر إيجابي، وإلا None."""
    h = headline or ""
    if _NEWS_NEG.search(h):
        return None
    for name, rx in _NEWS_POS:
        if rx.search(h):
            return name
    return None


# ---------- ملف المرسل (عشان ما يعيد نفس الخبر بعد إعادة التشغيل) ----------
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


# ---------- تيليجرام ----------
def chats():
    return [c.strip() for c in TELEGRAM_CHAT_ID.split(",") if c.strip()]


def send_telegram(text):
    text = text + "\n\n" + DISCLAIMER
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


# ---------- ألباكا ----------
def alpaca_headers():
    return {"APCA-API-KEY-ID": ALPACA_KEY, "APCA-API-SECRET-KEY": ALPACA_SECRET}


def fetch_news(start):
    """كل الأخبار من وقت start لين الحين. يرجع قائمة أو None لو فشل."""
    params = {"start": start.strftime("%Y-%m-%dT%H:%M:%SZ"), "limit": 50, "sort": "asc",
              "include_content": "false"}
    out = []
    for _ in range(10):
        try:
            r = requests.get(NEWS_URL, headers=alpaca_headers(), params=params, timeout=20)
        except Exception as e:
            log("الأخبار: فشل الاتصال -", e)
            return None
        if r.status_code == 429:
            time.sleep(5)
            continue
        if r.status_code != 200:
            log(f"الأخبار: خطأ {r.status_code} - {r.text[:200]}")
            return None
        data = r.json()
        out.extend(data.get("news") or [])
        token = data.get("next_page_token")
        if not token:
            break
        params["page_token"] = token
    return out


def fetch_prices(symbols):
    """آخر سعر لحظي لكل سهم: {الرمز: السعر}."""
    if not symbols:
        return {}
    try:
        r = requests.get(SNAP_URL, headers=alpaca_headers(),
                         params={"symbols": ",".join(symbols), "feed": PRICE_FEED}, timeout=15)
        if r.status_code != 200:
            log(f"الأسعار: خطأ {r.status_code} - {r.text[:150]}")
            return {}
        out = {}
        for sym, snap in (r.json() or {}).items():
            snap = snap or {}
            px = ((snap.get("latestTrade") or {}).get("p")
                  or (snap.get("dailyBar") or {}).get("c"))
            if px:
                out[sym] = float(px)
        return out
    except Exception as e:
        log("الأسعار: خطأ -", e)
        return {}


# ---------- القيم السوقية (اختياري) ----------
_caps = {"day": None, "caps": {}}


def _to_number(x):
    try:
        return float(str(x).replace("$", "").replace(",", "").strip())
    except Exception:
        return 0.0


def market_caps():
    """{الرمز: القيمة السوقية} من سكرينر ناسداك، تتجدد مرة باليوم."""
    today = datetime.now(timezone.utc).date()
    if _caps["day"] == today and _caps["caps"]:
        return _caps["caps"]
    caps = {}
    for ex in ("nasdaq", "nyse", "amex"):
        url = ("https://api.nasdaq.com/api/screener/stocks"
               f"?tableonly=true&limit=10000&exchange={ex}&download=true")
        try:
            r = requests.get(url, headers={**HEADERS, "Accept": "application/json"}, timeout=30)
            data = r.json().get("data") or {}
            rows = data.get("rows") or (data.get("table") or {}).get("rows") or []
            for row in rows:
                sym = str(row.get("symbol", "")).strip().upper()
                cap = _to_number(row.get("marketCap"))
                if sym.isalpha() and len(sym) <= 5 and 0 < cap:
                    caps[sym] = cap
        except Exception as e:
            log(f"ما قدرت أجيب القيم السوقية من {ex.upper()} -", e)
    if caps:
        _caps.update(day=today, caps=caps)
    return caps


def cap_txt(cap):
    return f"{cap / 1e9:.2f} مليار$" if cap >= 1e9 else f"{cap / 1e6:.1f} مليون$"


# ---------- الرسالة ----------
def news_message(item, cat, syms, prices, caps):
    try:
        t = datetime.fromisoformat(item["created_at"].replace("Z", "+00:00")).astimezone(LOCAL_TZ)
        t_txt = t.strftime("%H:%M")
    except Exception:
        t_txt = "-"
    stocks = " | ".join(f"${s} ({prices[s]:.2f}$)" if s in prices else f"${s}" for s in syms)
    cap_line = ""
    if caps and any(s in caps for s in syms):
        cap_line = "القيمة السوقية: " + " | ".join(cap_txt(caps[s]) for s in syms if s in caps) + "\n"
    return (f"📰 خبر إيجابي — {cat}\n"
            f"السهم: {stocks}\n"
            + cap_line
            + f"العنوان: {(item.get('headline') or '').strip()}\n"
            f"المصدر: {item.get('source') or item.get('author') or 'غير معروف'}\n"
            f"الوقت: {t_txt} (توقيتك)"
            + (f"\nالرابط: {item['url']}" if item.get("url") else ""))


# ---------- الحلقة الرئيسية ----------
def run():
    if not (ALPACA_KEY and ALPACA_SECRET):
        log("❌ يحتاج ALPACAAPIKEY و ALPACASECRETKEY في Railway")
        sys.exit(1)
    if not (TELEGRAM_TOKEN and chats()):
        log("⚠️ TELEGRAM_TOKEN أو TELEGRAM_CHAT_ID ناقص — بيطبع بالسجل بس")

    sent = load_sent()
    last = datetime.now(timezone.utc) - timedelta(minutes=NEWS_MAX_AGE_MIN)
    log(f"سكانر الأخبار بدأ — أسهم {NEWS_MIN_PRICE:g}$ إلى {NEWS_MAX_PRICE:g}$، "
        f"فحص كل {NEWS_POLL_SEC} ثانية، أسعار {PRICE_FEED.upper()}")

    while True:
        try:
            now = datetime.now(timezone.utc)
            items = fetch_news(last - timedelta(minutes=2))   # نرجع شوي عشان الأخبار المتأخرة
            if items is not None:
                last = now
                hits = []
                for it in items:
                    key = str(it.get("id"))
                    if key in sent:
                        continue
                    try:
                        created = datetime.fromisoformat(it["created_at"].replace("Z", "+00:00"))
                    except Exception:
                        continue
                    if (now - created).total_seconds() / 60 > NEWS_MAX_AGE_MIN:
                        continue
                    syms = [s for s in (it.get("symbols") or []) if s.isalpha() and len(s) <= 5]
                    if not syms or len(syms) > NEWS_MAX_SYMBOLS:
                        continue
                    cat = classify_news(it.get("headline"))
                    if not cat:
                        continue
                    sent.add(key)
                    mark_sent(key)
                    hits.append((it, cat, syms))

                if hits:
                    prices = fetch_prices(sorted({s for _, _, ss in hits for s in ss}))
                    caps = market_caps() if NEWS_MAX_MARKET_CAP else {}
                    for it, cat, syms in hits:
                        ok = [s for s in syms if s in prices
                              and NEWS_MIN_PRICE <= prices[s] <= NEWS_MAX_PRICE]
                        if NEWS_MAX_MARKET_CAP:
                            ok = [s for s in ok if 0 < caps.get(s, 0) < NEWS_MAX_MARKET_CAP]
                        if ok:
                            send_telegram(news_message(it, cat, ok, prices, caps))
        except Exception as e:
            log("خطأ -", e)
        time.sleep(NEWS_POLL_SEC)


def self_test():
    cases = [
        ("Acme Therapeutics Receives FDA Approval For Lead Drug", True),
        ("Acme Corp Enters Definitive Agreement To Be Acquired By BigCo", True),
        ("Acme Awarded $20M Contract From US Army", True),
        ("Acme Announces Pricing Of $10M Public Offering", False),
        ("Acme Announces 1-for-20 Reverse Stock Split", False),
        ("Acme Shares Fall After Earnings Miss", False),
    ]
    bad = 0
    for h, want in cases:
        got = classify_news(h)
        ok = bool(got) == want
        bad += not ok
        print("✅" if ok else "❌", got or "-", "|", h)
    print(news_message({"headline": cases[0][0], "source": "test", "created_at": "2026-10-13T10:00:00Z",
                        "url": "https://example.com"}, classify_news(cases[0][0]),
                       ["ACME"], {"ACME": 3.45}, {}))
    print("TEST OK" if not bad else f"TEST FAILED ({bad})")


if __name__ == "__main__":
    if "--test" in sys.argv:
        self_test()
    else:
        run()
