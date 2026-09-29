"""
بوت معلومات الأسهم - تيليجرام (تفاعلي)
=======================================
ترسل له رمز السهم (مثال: NVDA) ويرد عليك بمعلومات السهم بالعربي.
يرد على أي شخص يكلمه، في الخاص أو في القروبات.

المعلومات:
  - اسم الشركة والقطاع والسعر الحالي
  - القيمة السوقية وعدد الأسهم والفري فلوت
  - آخر إيرادات سنوية (مع تاريخها) + إيرادات آخر 12 شهر
  - تاريخ إعلان الأرباح القادم
  - مكرر الربحية - نسبة الشورت - نسبة الديون
  - متوسط السعر المستهدف للمحللين - ملكية المؤسسات
  - السعر مقارنة بأعلى وأقل سعر في السنة
  - آخر تجزئة، آخر تجزئة عكسية، وكم مرة جزّأ آخر سنة

المصدر: ياهو فاينانس (مجاناً)

التشغيل على Railway:
  - حط التوكن كمتغير اسمه TELEGRAM_BOT_TOKEN
  - أمر التشغيل: python stock_info_bot.py
"""

import os
import re
import time
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import requests
import yfinance as yf

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN", "")
API = f"https://api.telegram.org/bot{TOKEN}"
LOCAL_TZ = "Asia/Riyadh"
CACHE_MIN = 10          # لو أحد سأل عن نفس السهم خلال كذا دقيقة، يرد من الذاكرة
WORKERS = 4             # كم طلب يعالج بنفس الوقت

WELCOME = ("👋 هلا فيك!\n"
           "أرسل لي رمز أي سهم أمريكي وأعطيك معلوماته.\n"
           "مثال:  NVDA  أو  AAPL  أو  TSLA\n\n"
           "تقدر ترسل أكثر من رمز بنفس الرسالة (لين 5 رموز).")


def log(*a):
    print(*a, flush=True)


# ================== أدوات التنسيق ==================
def money(x):
    """رقم كبير بالدولار: 1.23 تريليون / مليار / مليون."""
    if x is None or pd.isna(x):
        return "غير معروف"
    x = float(x)
    sign = "-" if x < 0 else ""
    x = abs(x)
    for size, name in ((1e12, "تريليون"), (1e9, "مليار"), (1e6, "مليون")):
        if x >= size:
            return f"{sign}{x / size:.2f} {name} $"
    return f"{sign}{x:,.0f} $"


def count(x):
    """عدد أسهم: 2.45 مليار / 12.3 مليون."""
    if x is None or pd.isna(x):
        return "غير معروف"
    x = float(x)
    for size, name in ((1e9, "مليار"), (1e6, "مليون"), (1e3, "ألف")):
        if x >= size:
            return f"{x / size:.2f} {name}"
    return f"{x:,.0f}"


def pct(x, already_percent=False):
    if x is None or pd.isna(x):
        return "غير معروف"
    x = float(x) if already_percent else float(x) * 100
    return f"{x:.2f}%"


def num(x, digits=2):
    if x is None or pd.isna(x):
        return "غير معروف"
    return f"{float(x):,.{digits}f}"


def ratio_text(r):
    """نسبة التجزئة: 4.0 => 4 مقابل 1 ، 0.1 => 1 مقابل 10 (عكسية)."""
    r = float(r)
    if r >= 1:
        return f"{r:g} مقابل 1"
    return f"1 مقابل {1 / r:g}"


# ================== جلب البيانات ==================
def get_info(t):
    try:
        return yf.Ticker(t).info or {}
    except Exception as e:
        log(f"{t}: info خطأ - {e}")
        return {}


def last_annual_revenue(tk):
    """آخر إيرادات سنوية وتاريخ نهاية السنة المالية."""
    try:
        inc = tk.income_stmt
        if inc is None or inc.empty:
            return None, None
        for row in ("Total Revenue", "Operating Revenue"):
            if row in inc.index:
                s = inc.loc[row].dropna()
                if not s.empty:
                    s = s.sort_index()
                    return float(s.iloc[-1]), pd.Timestamp(s.index[-1])
    except Exception as e:
        log(f"الإيرادات خطأ - {e}")
    return None, None


def next_earnings(tk, info):
    """تاريخ إعلان الأرباح القادم."""
    now = pd.Timestamp.now(tz="UTC")
    dates = []
    try:
        cal = tk.calendar
        if isinstance(cal, dict):
            for d in cal.get("Earnings Date") or []:
                dates.append(pd.Timestamp(d))
    except Exception:
        pass
    for k in ("earningsTimestamp", "earningsTimestampStart"):
        if info.get(k):
            dates.append(pd.Timestamp(int(info[k]), unit="s"))
    fut = []
    for d in dates:
        d = d.tz_localize("UTC") if d.tzinfo is None else d
        if d >= now - pd.Timedelta(days=1):
            fut.append(d)
    return min(fut) if fut else None


def splits_info(tk):
    """(آخر تجزئة، آخر تجزئة عكسية، كم مرة جزّأ آخر سنة)."""
    try:
        s = tk.splits
        if s is None or s.empty:
            return None, None, 0
        s = s[s > 0].sort_index()
        idx = s.index if s.index.tz is not None else s.index.tz_localize("UTC")
        s.index = idx
        year_ago = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=365)
        last = (s.index[-1], s.iloc[-1]) if len(s) else None
        rev = s[s < 1]
        last_rev = (rev.index[-1], rev.iloc[-1]) if len(rev) else None
        return last, last_rev, int((s.index >= year_ago).sum())
    except Exception as e:
        log(f"التجزئة خطأ - {e}")
        return None, None, 0


_cache = {}   # الرمز -> (الوقت، الرد)


def stock_report(t):
    t = t.upper().strip()
    hit = _cache.get(t)
    if hit and time.time() - hit[0] < CACHE_MIN * 60:
        return hit[1]

    tk = yf.Ticker(t)
    info = get_info(t)
    price = info.get("currentPrice") or info.get("regularMarketPrice")
    if not info or (not price and not info.get("marketCap")):
        return f"❌ ما لقيت سهم بالرمز {t}\nتأكد من الرمز وجرب مرة ثانية."

    name = info.get("longName") or info.get("shortName") or t
    rev, rev_date = last_annual_revenue(tk)
    earn = next_earnings(tk, info)
    last_split, last_rev_split, splits_year = splits_info(tk)

    # مقارنة السعر بأعلى وأقل سعر في السنة
    hi52, lo52 = info.get("fiftyTwoWeekHigh"), info.get("fiftyTwoWeekLow")
    range_txt = "غير معروف"
    if price and hi52 and lo52:
        from_hi = (price / hi52 - 1) * 100
        from_lo = (price / lo52 - 1) * 100
        range_txt = (f"أعلى: {num(hi52)} ({from_hi:+.1f}%)\n"
                     f"   أقل: {num(lo52)} ({from_lo:+.1f}%)")

    # السعر المستهدف
    target = info.get("targetMeanPrice")
    target_txt = "غير معروف"
    if target:
        target_txt = num(target)
        if price:
            target_txt += f" ({(target / price - 1) * 100:+.1f}% عن السعر الحالي)"
        if info.get("numberOfAnalystOpinions"):
            target_txt += f" - {info['numberOfAnalystOpinions']} محلل"

    # الأرباح القادمة
    earn_txt = "غير معروف"
    if earn is not None:
        days = (earn.normalize() - pd.Timestamp.now(tz="UTC").normalize()).days
        earn_txt = f"{earn.tz_convert(LOCAL_TZ):%Y-%m-%d}"
        earn_txt += " (اليوم)" if days <= 0 else f" (بعد {days} يوم)"

    # الإيرادات
    rev_txt = money(rev) + (f" (السنة المالية المنتهية {rev_date:%Y-%m-%d})" if rev_date is not None else "")

    # الديون
    de = info.get("debtToEquity")
    de_txt = f"{float(de):.1f}%" if de is not None else "غير معروف"
    debt_txt = money(info.get("totalDebt"))

    # التجزئة
    def split_line(x):
        return f"{x[0]:%Y-%m-%d} ({ratio_text(x[1])})" if x else "ما فيه"

    pe = info.get("trailingPE")
    pe_txt = num(pe) if pe else "ما فيه (الشركة خسرانة أو ما فيه بيانات)"
    fpe = info.get("forwardPE")

    lines = [
        f"📊 {name} ({t})",
        f"🏷️ القطاع: {info.get('sector') or 'غير معروف'} - {info.get('industry') or ''}".rstrip(" -"),
        f"💵 السعر: {num(price)} $",
        "",
        f"🏦 القيمة السوقية: {money(info.get('marketCap'))}",
        f"🔢 عدد الأسهم: {count(info.get('sharesOutstanding'))}",
        f"🔓 الفري فلوت: {count(info.get('floatShares'))}",
        "",
        f"💰 آخر إيرادات سنوية: {rev_txt}",
        f"💰 إيرادات آخر 12 شهر: {money(info.get('totalRevenue'))}",
        f"📅 إعلان الأرباح القادم: {earn_txt}",
        "",
        f"📈 مكرر الربحية: {pe_txt}" + (f" | المتوقع: {num(fpe)}" if fpe else ""),
        f"🩳 نسبة الشورت من الفري فلوت: {pct(info.get('shortPercentOfFloat'))}",
        f"⚖️ نسبة الديون للملكية: {de_txt} | إجمالي الديون: {debt_txt}",
        f"🎯 متوسط سعر المحللين: {target_txt}",
        f"🏢 ملكية المؤسسات: {pct(info.get('heldPercentInstitutions'))}",
        "",
        f"📉 السعر مقارنة بالسنة:\n   {range_txt}",
        "",
        f"✂️ آخر تجزئة: {split_line(last_split)}",
        f"🔻 آخر تجزئة عكسية: {split_line(last_rev_split)}",
        f"🔁 عدد التجزئات آخر سنة: {splits_year}",
        "",
        "المصدر: ياهو فاينانس - للمعلومة فقط وليست توصية",
    ]
    text = "\n".join(lines)
    _cache[t] = (time.time(), text)
    return text


# ================== تيليجرام ==================
def send(chat_id, text, reply_to=None):
    data = {"chat_id": chat_id, "text": text, "disable_web_page_preview": True}
    if reply_to:
        data["reply_to_message_id"] = reply_to
        data["allow_sending_without_reply"] = True
    try:
        r = requests.post(f"{API}/sendMessage", data=data, timeout=15).json()
        if not r.get("ok"):
            log(f"فشل الإرسال لـ {chat_id}: {r.get('description')}")
    except Exception as e:
        log(f"فشل الإرسال لـ {chat_id}: {e}")


def typing(chat_id):
    try:
        requests.post(f"{API}/sendChatAction",
                      data={"chat_id": chat_id, "action": "typing"}, timeout=5)
    except Exception:
        pass


TICKER_RE = re.compile(r"^\$?[A-Za-z]{1,5}([.\-][A-Za-z]{1,2})?$")


def extract_tickers(text):
    """يطلع الرموز من الرسالة (NVDA أو $NVDA أو nvda, aapl)."""
    words = re.split(r"[\s,،]+", text.strip())
    out = []
    for w in words:
        if TICKER_RE.match(w):
            w = w.lstrip("$").upper().replace(".", "-")
            if w not in out:
                out.append(w)
    return out[:5]


def handle(msg):
    chat_id = msg["chat"]["id"]
    text = (msg.get("text") or "").strip()
    if not text:
        return
    who = (msg.get("from") or {}).get("username") or (msg.get("from") or {}).get("first_name", "")
    log(f"رسالة من {who} ({chat_id}): {text[:50]}")

    if text.startswith("/"):
        cmd = text.split()[0].split("@")[0].lower()
        if cmd in ("/start", "/help"):
            send(chat_id, WELCOME)
            return
        text = text[len(text.split()[0]):]       # مثل /s NVDA

    tickers = extract_tickers(text)
    is_private = msg["chat"].get("type") == "private"
    if not tickers:
        if is_private:
            send(chat_id, "ما فهمت الرمز 🤔\nأرسل رمز السهم بالإنجليزي، مثال: NVDA", msg.get("message_id"))
        return                                    # في القروبات يتجاهل الكلام العادي
    for t in tickers:
        typing(chat_id)
        try:
            send(chat_id, stock_report(t), msg.get("message_id"))
        except Exception as e:
            log(f"{t}: خطأ - {e}")
            send(chat_id, f"⚠️ صار خطأ وأنا أجيب بيانات {t}، جرب بعد شوي.", msg.get("message_id"))


def main():
    if not TOKEN:
        log("❌ ما لقيت التوكن. حطه في Railway كمتغير اسمه TELEGRAM_BOT_TOKEN")
        return
    me = requests.get(f"{API}/getMe", timeout=15).json()
    if not me.get("ok"):
        log(f"❌ التوكن غلط: {me.get('description')}")
        return
    log(f"✅ البوت شغال: @{me['result']['username']}")
    # يلغي أي webhook قديم عشان getUpdates يشتغل
    requests.get(f"{API}/deleteWebhook", timeout=15)

    offset = 0
    pool = ThreadPoolExecutor(max_workers=WORKERS)
    while True:
        try:
            r = requests.get(f"{API}/getUpdates",
                             params={"offset": offset, "timeout": 30,
                                     "allowed_updates": '["message"]'},
                             timeout=40).json()
        except Exception as e:
            log("خطأ في الاتصال بتيليجرام:", e)
            time.sleep(5)
            continue
        if not r.get("ok"):
            log("تيليجرام رجع خطأ:", r.get("description"))
            time.sleep(5)
            continue
        for u in r.get("result", []):
            offset = u["update_id"] + 1
            msg = u.get("message")
            if msg:
                pool.submit(handle, msg)


if __name__ == "__main__":
    main()
