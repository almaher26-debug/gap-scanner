# -*- coding: utf-8 -*-
"""
سكانر الأخبار الإيجابية — بوت سافونا
-----------------------------------
الفكرة:
  1) يجيب آخر الأخبار من Alpaca News لقائمة الأسهم
  2) يقرأ العنوان والملخص ويدور على كلمات إيجابية (نتائج أفضل من المتوقع، رفع توقعات، ترقية محلل...)
     وكلمات سلبية (خسارة، تخفيض، قضية، تحقيق...)
  3) لو الخبر طابعه إيجابي وما فيه إشارات سلبية واضحة => يرسل تنبيه تعليمي على تليجرام
  ⚠️ التنبيه تعليمي فقط: يوصف طابع الخبر، وما يقول اشترِ أو بع.

يشتغل لحاله:   python -u news_scanner.py
أو من داخل البوت (جنب سكانر الـ IFVG):
    import news_scanner
    threading.Thread(target=news_scanner.run_forever, kwargs={"send": send_telegram}, daemon=True).start()

المتغيرات (Railway Variables):
  ALPACAAPIKEY, ALPACASECRETKEY       نفس مفاتيح ألباكا
  TELEGRAM_TOKEN, TELEGRAM_CHAT_ID    نفس التليجرام
  NEWS_SYMBOLS        قائمة الأسهم (اختياري — لو فاضي ياخذ IFVG_SYMBOLS أو القائمة الافتراضية)
  NEWS_MAX_AGE_MIN    أقدم خبر نرسله بالدقايق (الافتراضي 30)
  NEWS_MIN_SCORE      أقل نقاط إيجابية للتنبيه (الافتراضي 2)
  NEWS_MAX_SYMBOLS    نتجاهل الأخبار العامة اللي تذكر أكثر من هذا العدد من الأسهم (الافتراضي 4)
  NEWS_SCAN_EVERY_SEC كل كم ثانية يفحص (الافتراضي 120)
"""
import json
import os
import re
import time
from datetime import datetime, timedelta, timezone

import requests

# ------------------------------------------------------------------ الإعدادات
DEFAULT_SYMBOLS = (
    "LITE,MU,NVDA,AMD,AVGO,TSLA,AAPL,MSFT,META,AMZN,GOOGL,NFLX,PLTR,SMCI,"
    "COIN,MSTR,ARM,TSM,ANET,CRWD,SHOP,UBER,QQQ,SPY"
)
_sym_env = os.getenv("NEWS_SYMBOLS") or os.getenv("IFVG_SYMBOLS") or DEFAULT_SYMBOLS
SYMBOLS = [s.strip().upper() for s in _sym_env.split(",") if s.strip()]
MAX_AGE_MIN = int(os.getenv("NEWS_MAX_AGE_MIN", "30"))
MIN_SCORE = float(os.getenv("NEWS_MIN_SCORE", "2"))
MAX_SYMBOLS_PER_NEWS = int(os.getenv("NEWS_MAX_SYMBOLS", "4"))
SCAN_EVERY_SEC = int(os.getenv("NEWS_SCAN_EVERY_SEC", "120"))
STATE_FILE = os.getenv("NEWS_STATE_FILE", "/data/news_state.json" if os.path.isdir("/data") else "news_state.json")

NEWS_URL = "https://data.alpaca.markets/v1beta1/news"

# (النمط, الوزن, الوصف بالعربي)
POSITIVE = [
    (r"\bbeats?\b|\btops? (estimates|expectations|views)\b|\bbetter[- ]than[- ]expected\b|\bahead of (estimates|expectations)\b",
     2, "نتائج أفضل من توقعات السوق"),
    (r"\b(raises?|boosts?|lifts?|hikes?|ups?) (its |full[- ]year |annual |fy |quarterly )?(guidance|outlook|forecast)\b",
     2, "رفع التوقعات المستقبلية للشركة"),
    (r"\bupgrade[sd]?\b", 2, "ترقية تصنيف من محلل"),
    (r"\b(raises?|lifts?|hikes?|boosts?) (price target|pt)\b|\bprice target (raised|increased|lifted)\b",
     2, "رفع السعر المستهدف من محلل"),
    (r"\brecord (revenue|sales|quarter|profit|earnings|deliveries)\b", 2, "إيرادات أو أرباح قياسية"),
    (r"\bfda (approval|approves|clears|grants)\b|\bapproved by (the )?fda\b", 2, "موافقة من FDA"),
    (r"\b(buyback|share repurchase|repurchase program|stock repurchase)\b", 2, "برنامج إعادة شراء أسهم"),
    (r"\b(raises?|increases?|hikes?|boosts?) (its |quarterly )?dividend\b|\bdividend (increase|hike)\b",
     2, "رفع التوزيعات النقدية"),
    (r"\b(wins?|won|awarded|secures?|lands?) .{0,40}\b(contract|deal|order)\b", 2, "عقد أو صفقة جديدة"),
    (r"\b(partnership|partners with|strategic alliance|collaboration with)\b", 1, "شراكة أو تعاون"),
    (r"\b(to be acquired|agrees to be acquired|takeover (offer|bid)|buyout offer)\b", 2, "عرض استحواذ على الشركة"),
    (r"\b(added to|joins|to join) (the )?s&p 500\b", 2, "انضمام لمؤشر S&P 500"),
    (r"\b(surges?|soars?|jumps?|rall(y|ies)|skyrockets?|climbs?)\b", 1, "ارتفاع قوي في السهم"),
]

NEGATIVE = [
    r"\bmiss(es|ed)?\b", r"\b(cuts?|lowers?|slashes?|trims?) (its |full[- ]year |annual )?(guidance|outlook|forecast)\b",
    r"\bdowngrade[sd]?\b", r"\b(cuts?|lowers?|slashes?) (price target|pt)\b", r"\bprice target (cut|lowered)\b",
    r"\b(lawsuit|sued|sues|class action)\b", r"\b(investigation|probe|subpoena|sec charges)\b",
    r"\brecalls?\b", r"\b(stock offering|share offering|secondary offering|dilution)\b",
    r"\blayoffs?\b|\bjob cuts\b", r"\bbankruptcy\b", r"\b(plunges?|tumbles?|slumps?|sinks?|falls?|drops?|crash(es)?)\b",
    r"\b(delays?|delayed|halts?|suspends?)\b", r"\b(warns?|warning)\b", r"\b(loss widens|wider loss)\b",
    r"\bworse[- ]than[- ]expected\b",
]
_POS = [(re.compile(p, re.I), w, lbl) for p, w, lbl in POSITIVE]
_NEG = [re.compile(p, re.I) for p in NEGATIVE]


# ------------------------------------------------------------------ البيانات
def fetch_news(symbols, since):
    """يرجع قائمة الأخبار من Alpaca من وقت since لين الحين."""
    headers = {
        "APCA-API-KEY-ID": os.getenv("ALPACAAPIKEY", ""),
        "APCA-API-SECRET-KEY": os.getenv("ALPACASECRETKEY", ""),
    }
    out = []
    for i in range(0, len(symbols), 50):
        params = {
            "symbols": ",".join(symbols[i:i + 50]),
            "start": since.isoformat().replace("+00:00", "Z"),
            "limit": 50,
            "sort": "desc",
            "include_content": "false",
        }
        for _ in range(10):  # حد أقصى للصفحات
            r = requests.get(NEWS_URL, headers=headers, params=params, timeout=30)
            r.raise_for_status()
            js = r.json()
            out.extend(js.get("news") or [])
            tok = js.get("next_page_token")
            if not tok:
                break
            params["page_token"] = tok
    # شيل المكرر
    seen, uniq = set(), []
    for n in out:
        if n.get("id") not in seen:
            seen.add(n.get("id"))
            uniq.append(n)
    return uniq


# ------------------------------------------------------------------ التحليل
def score(text):
    """يرجع (النقاط, الأسباب الإيجابية, عدد الإشارات السلبية)"""
    pos, reasons = 0, []
    for rx, w, lbl in _POS:
        if rx.search(text):
            pos += w
            reasons.append(lbl)
    neg = sum(1 for rx in _NEG if rx.search(text))
    return pos, reasons, neg


def is_positive(news):
    text = f"{news.get('headline', '')} {news.get('summary', '')}"
    pos, reasons, neg = score(text)
    ok = neg == 0 and pos >= MIN_SCORE and any(w >= 2 for rx, w, lbl in _POS if lbl in reasons)
    return ok, reasons


# ------------------------------------------------------------------ الرسالة
def _riyadh(ts):
    t = datetime.fromisoformat(ts.replace("Z", "+00:00")) + timedelta(hours=3)
    return t.strftime("%m-%d %H:%M")


def format_msg(sym, news, reasons):
    others = [s for s in news.get("symbols", []) if s != sym]
    lines = [
        "🤖 بوت سافونا — 📰 خبر إيجابي على السهم",
        "⚠️ محتوى تعليمي فقط، وليس توصية بيع أو شراء. القرار مسؤوليتك.",
        "",
        f"السهم: ${sym}",
        f"العنوان: {news.get('headline', '').strip()}",
        "طابع الخبر: إيجابي",
        "النقاط الإيجابية في الخبر:",
        *[f"  • {r}" for r in reasons],
    ]
    if others:
        lines.append(f"أسهم ثانية مذكورة: {', '.join('$' + s for s in others)}")
    lines += [
        f"المصدر: {news.get('source', 'Alpaca')}",
        f"وقت الخبر: {_riyadh(news['created_at'])} (توقيتك)",
    ]
    if news.get("url"):
        lines.append(f"الرابط: {news['url']}")
    lines += [
        "",
        "📚 الخبر الإيجابي ما يعني إن السهم لازم يصعد — أحياناً يكون الخبر متوقع ومسعّر مسبقاً. "
        "اقرأ الخبر كامل وشوف ردة فعل السعر قبل أي قرار.",
    ]
    return "\n".join(lines)


# ------------------------------------------------------------------ التليجرام والحالة
def _default_send(text):
    token = os.getenv("TELEGRAM_TOKEN", "")
    for chat in [c.strip() for c in os.getenv("TELEGRAM_CHAT_ID", "").split(",") if c.strip()]:
        try:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          data={"chat_id": chat, "text": text, "disable_web_page_preview": "true"}, timeout=15)
        except Exception as e:
            print(f"NEWS: ما قدرت أرسل لـ {chat}: {e}")


def _load_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_state(st):
    if len(st) > 5000:
        st = dict(sorted(st.items(), key=lambda kv: kv[1])[-5000:])
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(st, f)
    except Exception as e:
        print(f"NEWS: ما قدرت أحفظ الحالة: {e}")
    return st


def scan_once(send=None):
    send = send or _default_send
    state = _load_state()
    since = datetime.now(timezone.utc) - timedelta(minutes=MAX_AGE_MIN)
    new = 0
    try:
        items = fetch_news(SYMBOLS, since)
    except Exception as e:
        print(f"NEWS: خطأ بالبيانات: {e}")
        return 0
    watch = set(SYMBOLS)
    for n in sorted(items, key=lambda x: x.get("created_at", "")):
        syms = n.get("symbols") or []
        if len(syms) > MAX_SYMBOLS_PER_NEWS:
            continue  # خبر عام يذكر أسهم كثيرة
        ok, reasons = is_positive(n)
        if not ok:
            continue
        for sym in syms:
            if sym not in watch:
                continue
            key = f"{n.get('id')}|{sym}"
            if key in state:
                continue
            send(format_msg(sym, n, reasons))
            state[key] = int(time.time())
            new += 1
    _save_state(state)
    print(f"[{datetime.now(timezone.utc) + timedelta(hours=3):%H:%M}] الأخبار: خلص الفحص - {new} تنبيه جديد")
    return new


def run_forever(send=None):
    print(f"الأخبار: بدأ المراقبة — {len(SYMBOLS)} سهم، كل {SCAN_EVERY_SEC} ثانية")
    while True:
        try:
            scan_once(send)
        except Exception as e:
            print(f"NEWS: خطأ: {e}")
        time.sleep(SCAN_EVERY_SEC)


if __name__ == "__main__":
    run_forever()
