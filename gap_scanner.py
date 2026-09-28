"""
بوت التنبيهات - يشتغل على Railway ويرسل على تيليجرام
=====================================================

(1) نموذج الـ Inversion Gap - فريم 4 ساعات
    الأسهم: كل أسهم ناسداك اللي قيمتها السوقية 2 مليار دولار وفوق (ميد كاب وأعلى)
    ⚠️ لون الشموع الثلاث ما يهم - المهم إن ذيل الشمعة الأولى والثالثة ما يلتقون

    🟢 صعودي (جاب تحت):
      - ثلاث شموع (أي لون)، وقاع الشمعة الأولى أعلى من قمة الشمعة الثالثة
      - الجاب = من قمة الشمعة الثالثة (تحت) إلى قاع الشمعة الأولى (فوق)
      - الشمعة الرابعة تجي من تحت وتطلع لين تلمس أعلى الجاب (قاع C1)  =>  تنبيه فوراً

    🔴 هبوطي (جاب فوق):
      - ثلاث شموع (أي لون)، وقمة الشمعة الأولى أقل من قاع الشمعة الثالثة
      - الجاب = من قمة الشمعة الأولى (تحت) إلى قاع الشمعة الثالثة (فوق)
      - الشمعة الرابعة تجي من فوق وتنزل لين تلمس أسفل الجاب (قمة C1)  =>  تنبيه فوراً

    فلتر: السهم سعره فوق 10$ ، وحجم الجاب (الفرق بين الحدين) أكبر من 0.50$
    ⏱️ آخر جاب بس: الجاب لازم يكون من آخر 3 شموع قبل الشمعة الحالية مباشرة،
       والتنبيه يطلع بس إذا اللمس صار الحين (آخر ساعة) والسعر لسا عند الجاب،
       عشان ما يرسل جاب قديم أو لمسة صارت من ساعات (مثلاً بعد إعادة تشغيل البوت)

(2) الأخبار - 24 ساعة
    - كل أسهم ناسداك (عليها تداول)
    - أي خبر جديد ينزل على أي سهم  =>  تنبيه، مع نوع الخبر:
      🟢 إيجابي / 🔴 سلبي / ⚪ محايد  (تصنيف تقريبي من كلمات العنوان، مو دقيق 100%)
    - المصدر: ياهو فاينانس

(3) نماذج الفريم اليومي - كل أسهم ناسداك - التنبيه عند اكتمال النموذج (كسر خط العنق)
    🟢 القاع المزدوج (W)        : قاعين متقاربين (فرق 3% أو أقل) + اختراق خط العنق لفوق
    🔴 القمة المزدوجة (M)       : قمتين متقاربتين (فرق 3% أو أقل) + كسر خط العنق لتحت
    🔴 الرأس والكتفين            : كتف + رأس أعلى + كتف + كسر خط العنق لتحت
    🟢 الرأس والكتفين المقلوب    : كتف + رأس أنزل + كتف + اختراق خط العنق لفوق

(4) الشورت صفر
    - أسهم ناسداك اللي سعرها من 1 إلى 6 دولار
    - إذا بيانات الشورت الرسمية (من ياهو) صارت صفر  =>  تنبيه
    - البيانات الرسمية تنزل مرتين بالشهر وبتأخير أسبوعين تقريباً، فيفحصها مرة باليوم

التشغيل:
  pip install yfinance pandas requests lxml
  python gap_scanner.py          # يشتغل باستمرار ويفحص كل 5 دقايق
  python gap_scanner.py --once   # فحص مرة وحدة بس
"""

import io
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import pandas as pd
import requests

# ================== الإعدادات ==================
# على السيرفر تنحط كمتغيرات (Variables) عشان ما تنكشف في جيتهب
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "ضع_توكن_البوت_هنا")      # من @BotFather
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "ضع_رقم_المحادثة_هنا")  # من @userinfobot
# تقدر تحط أكثر من رقم بينهم فاصلة، مثال:  123456789,-1001234567890
# وأي قروب أو قناة تضيف لها البوت، يلقط رقمها لحاله ويرسل لها التنبيهات
AUTO_ADD_GROUPS = True
CHATS_FILE = "chats.txt"     # يحفظ فيه أرقام القروبات اللي لقطها

CHECK_EVERY_MIN = 5          # كل كم دقيقة يفحص
NY = "America/New_York"
LOCAL_TZ = "Asia/Riyadh"     # توقيتك المحلي

# ---- (1) نموذج الجاب ----
ENABLE_GAP = True
MIN_MARKET_CAP = 2_000_000_000   # 2 مليار دولار = ميد كاب وفوق
ENABLE_BULLISH = True            # جاب تحت + شمعة تطلع وتلمس أعلى الجاب
ENABLE_BEARISH = True            # جاب فوق + شمعة تنزل وتلمس أسفل الجاب
REQUIRE_FOURTH_COLOR = False     # True = الرابعة لازم خضراء بالصعودي وحمراء بالهبوطي
                                 # False = ينبه أول ما تلمس الخط حتى لو الشمعة ما قفلت
TOUCH_TOLERANCE = 0.0            # 0 = لازم تلمس الخط نفسه (كانت 0.1% وتنبه قبل ما توصل)
GAP_EXTENDED = True              # شمعة الـ4 ساعات تشمل ما قبل الفتح وبعد الإغلاق (4-8، 8-12، 12-4، 4-8)

GAP_MIN_STOCK_PRICE = 10         # يتجاهل الأسهم اللي سعرها أقل من كذا
GAP_MIN_SIZE = 0.50              # يتجاهل الجاب اللي حجمه أقل من كذا (دولار)
GAP_FRESH_BARS = 2               # اللمس لازم يكون صار في آخر كم شمعة نص ساعة (2 = آخر ساعة)
GAP_SENT_FILE = "gap_sent.txt"   # عشان ما يعيد نفس التنبيه لو البوت أعاد التشغيل

USE_PRICE_FILTER = False         # True = يطبق فلتر السعر تحت مع فلتر القيمة السوقية
MIN_PRICE = 50
MAX_PRICE = 500

# ---- (2) الأخبار - 24 ساعة ----
ENABLE_NEWS = True
NEWS_MIN_PRICE = 0               # 0 = كل الأسعار
NEWS_MAX_PRICE = 1_000_000
NEWS_MIN_AVG_VOLUME = 100_000    # يشيل الأسهم الميتة اللي ما عليها تداول (عدد أسهم يومي)
NEWS_INCLUDE_NYSE = False        # False = ناسداك بس
NEWS_EVERY_MIN = 10              # كل كم دقيقة يفحص الأخبار (الأسهم كثيرة، أقل من كذا ياهو ممكن يحظر)
NEWS_MAX_AGE_MIN = 90            # يتجاهل الأخبار الأقدم من كذا (عشان ما يرسل أخبار قديمة أول ما يشتغل)
NEWS_WORKERS = 8                 # عدد الطلبات المتوازية على ياهو
NEWS_SENT_FILE = "news_sent.txt" # عشان ما يعيد نفس الخبر لو البوت أعاد التشغيل

# ---- (3) نماذج الفريم اليومي ----
ENABLE_DAILY = True
ENABLE_DOUBLE_BOTTOM = True      # W
ENABLE_DOUBLE_TOP = True         # M
ENABLE_HS = True                 # الرأس والكتفين (هبوطي)
ENABLE_INV_HS = True             # الرأس والكتفين المقلوب (صعودي)
DAILY_MIN_PRICE = 1              # أقل سعر سهم
DAILY_MIN_AVG_VOLUME = 300_000   # يشيل الأسهم الميتة (عدد أسهم يومي)
DAILY_EVERY_MIN = 30             # كل كم دقيقة يفحص اليومي (وقت السوق الرسمي)
DOUBLE_TOLERANCE = 0.03          # 3% أقصى فرق بين القاعين أو القمتين
PATTERN_MIN_DEPTH = 0.04         # خط العنق لازم يبعد عن القاع/القمة 4% على الأقل (عشان يشيل النماذج الصغيرة)
SHOULDER_TOLERANCE = 0.05        # 5% أقصى فرق بين الكتفين
HEAD_MIN_DIFF = 0.02             # الرأس لازم يزيد عن الكتفين 2% على الأقل
PIVOT_BARS = 5                   # القمة/القاع لازم تكون أعلى/أنزل من 5 شموع قبلها و5 بعدها
PATTERN_MIN_BARS = 10            # أقل مسافة بين القاعين/القمتين (أيام تداول)
PATTERN_MAX_BARS = 120           # أقصى طول للنموذج (تقريباً 6 شهور)

# ---- (4) الشورت صفر ----
ENABLE_SHORT = True
SHORT_MIN_PRICE = 1
SHORT_MAX_PRICE = 6
SHORT_MIN_AVG_VOLUME = 50_000
SHORT_WORKERS = 6
SHORT_SENT_FILE = "short_sent.txt"   # عشان ما يعيد نفس التنبيه لو البوت أعاد التشغيل
# ===============================================

HEADERS = {"User-Agent": "Mozilla/5.0"}

# قائمة احتياطية لو ما قدر يجيب القيم السوقية من النت
FALLBACK_TICKERS = """
AAPL MSFT NVDA AMZN META GOOGL GOOG AVGO TSLA COST NFLX AMD PEP ADBE CSCO TMUS
QCOM INTU TXN AMGN ISRG CMCSA HON BKNG AMAT VRTX ADP PANW GILD SBUX MU ADI LRCX
MELI REGN MDLZ KLAC INTC SNPS CDNS PYPL CRWD MAR CTAS ORLY ASML CEG ABNB FTNT
CSX MRVL ADSK PCAR ROP WDAY NXPI CPRT CHTR MNST PAYX AEP ODFL FAST KDP ROST DDOG
TTD BKR KHC VRSK EXC XEL CTSH GEHC LULU IDXX CCEP FANG DXCM TEAM ON ZS CSGP
BIIB CDW MDB GFS WBD ARM DASH PLTR APP MSTR AZN LIN TRI SHOP AXON
""".split()


# ================== أدوات عامة ==================
def log(*a):
    print(*a, flush=True)


TG_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
CHATS = set()          # كل المحادثات اللي يرسل لها
_last_update_id = 0


def _load_chats():
    for c in TELEGRAM_CHAT_ID.split(","):
        c = c.strip()
        if c and "ضع_" not in c:
            CHATS.add(c)
    try:
        with open(CHATS_FILE, encoding="utf-8") as f:
            CHATS.update(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        pass


def _save_chat(chat_id):
    try:
        with open(CHATS_FILE, "a", encoding="utf-8") as f:
            f.write(chat_id + "\n")
    except Exception:
        pass


def discover_groups():
    """يشوف لو البوت انضاف لقروب أو قناة جديدة، ويضيف رقمها لقائمة الإرسال."""
    global _last_update_id
    if not AUTO_ADD_GROUPS or "ضع_" in TELEGRAM_TOKEN:
        return
    try:
        r = requests.get(f"{TG_API}/getUpdates",
                         params={"offset": _last_update_id + 1, "timeout": 0,
                                 "allowed_updates": '["message","channel_post","my_chat_member"]'},
                         timeout=15).json()
    except Exception as e:
        log("ما قدرت أشيك على القروبات:", e)
        return
    for u in r.get("result", []):
        _last_update_id = max(_last_update_id, u["update_id"])
        box = u.get("my_chat_member") or u.get("message") or u.get("channel_post") or {}
        chat = box.get("chat") or {}
        if chat.get("type") not in ("group", "supergroup", "channel"):
            continue
        cid = str(chat["id"])
        # لو البوت انطرد من القروب نشيله
        status = ((u.get("my_chat_member") or {}).get("new_chat_member") or {}).get("status")
        if status in ("left", "kicked"):
            CHATS.discard(cid)
            continue
        # القروب ترقّى لسوبر قروب وتغيّر رقمه
        new_id = (u.get("message") or {}).get("migrate_to_chat_id")
        if new_id:
            CHATS.discard(cid)
            cid = str(new_id)
        if cid not in CHATS:
            CHATS.add(cid)
            _save_chat(cid)
            title = chat.get("title", "")
            log(f"✅ انضاف قروب/قناة جديد: {title}  الرقم: {cid}")
            log(f"   عشان يثبت دايم، حط هالرقم في TELEGRAM_CHAT_ID على Railway")
            _send_one(cid, f"✅ البوت متصل هنا وبيرسل التنبيهات\nرقم المحادثة: {cid}")


def _send_one(chat_id, text):
    try:
        r = requests.post(f"{TG_API}/sendMessage",
                          data={"chat_id": chat_id, "text": text,
                                "disable_web_page_preview": True},
                          timeout=10).json()
        if not r.get("ok"):
            log(f"فشل الإرسال لـ {chat_id}: {r.get('description')}")
            params = r.get("parameters") or {}
            if params.get("migrate_to_chat_id"):   # القروب تغيّر رقمه
                CHATS.discard(chat_id)
                new_id = str(params["migrate_to_chat_id"])
                CHATS.add(new_id)
                _save_chat(new_id)
                _send_one(new_id, text)
    except Exception as e:
        log(f"فشل إرسال التنبيه لـ {chat_id}:", e)


def send_telegram(text):
    log(text)
    if "ضع_" in TELEGRAM_TOKEN:
        return  # ما حطيت التوكن، يطبع بالشاشة بس
    for chat_id in list(CHATS):
        _send_one(chat_id, text)


def us_market_open():
    """السوق الأمريكي شامل ما قبل الفتح وبعد الإغلاق (4 الصبح - 8 بالليل نيويورك)."""
    now = pd.Timestamp.now(tz=NY)
    if now.weekday() >= 5:
        return False
    if GAP_EXTENDED:
        return now.replace(hour=4, minute=0) <= now <= now.replace(hour=20, minute=5)
    return now.replace(hour=9, minute=30) <= now <= now.replace(hour=16, minute=5)


def download_batches(tickers, batch_size, **kw):
    """يحمّل بيانات ياهو على دفعات، ويرجع (الرمز، البيانات) لكل سهم."""
    import yfinance as yf

    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i + batch_size]
        try:
            data = yf.download(batch, group_by="ticker", progress=False,
                               threads=True, auto_adjust=False, **kw)
        except Exception as e:
            log("فشل تحميل دفعة:", e)
            time.sleep(5)
            continue
        for t in batch:
            try:
                if isinstance(data.columns, pd.MultiIndex):
                    if t not in data.columns.get_level_values(0):
                        continue
                    df = data[t]
                else:
                    df = data
                df = df.dropna(subset=["Open", "High", "Low", "Close"])
                if not df.empty:
                    yield t, df
            except Exception:
                continue
        time.sleep(1)


# ================== (1) نموذج الجاب ==================
def _to_number(x):
    try:
        return float(str(x).replace("$", "").replace(",", "").strip())
    except Exception:
        return 0.0


def get_nasdaq_midcap_plus():
    """كل أسهم ناسداك اللي قيمتها السوقية فوق الحد، من سكرينر ناسداك الرسمي."""
    url = ("https://api.nasdaq.com/api/screener/stocks"
           "?tableonly=true&limit=10000&exchange=nasdaq&download=true")
    try:
        r = requests.get(url, headers={**HEADERS, "Accept": "application/json"}, timeout=30)
        data = r.json().get("data") or {}
        rows = data.get("rows") or (data.get("table") or {}).get("rows") or []
        out = []
        for row in rows:
            sym = str(row.get("symbol", "")).strip().upper()
            cap = _to_number(row.get("marketCap"))
            if sym.isalpha() and len(sym) <= 5 and cap >= MIN_MARKET_CAP:
                out.append(sym)
        if len(out) > 50:
            return sorted(set(out))
        log("قائمة ناسداك رجعت فاضية تقريباً، أستخدم الاحتياطية")
    except Exception as e:
        log("ما قدرت أجيب القيم السوقية من ناسداك، أستخدم الاحتياطية:", e)
    return FALLBACK_TICKERS


def to_ny(df):
    df = df.dropna(subset=["Open", "High", "Low", "Close"])
    idx = df.index
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
    return df.set_index(idx.tz_convert(NY))


def touch_is_fresh(bars, res):
    """يتأكد إن اللمس صار الحين مو من ساعات، وإن السعر لسا ما رجع وطلع من الجاب.
    bars = شموع النص ساعة، res = نتيجة check_pattern"""
    b = to_ny(bars)
    b = b[b.index >= res["candle_time"]]            # بس شموع الشمعة الرابعة الحالية
    if b.empty:
        return False
    if res["side"] == "bull":
        hits = b.index[b["High"] >= res["gap_top"] * (1 - TOUCH_TOLERANCE)]
        still_there = b["Close"].iloc[-1] >= res["gap_bottom"]   # ما نزل تحت الجاب مرة ثانية
    else:
        hits = b.index[b["Low"] <= res["gap_bottom"] * (1 + TOUCH_TOLERANCE)]
        still_there = b["Close"].iloc[-1] <= res["gap_top"]      # ما طلع فوق الجاب مرة ثانية
    if len(hits) == 0:
        return False
    recent = b.index[-GAP_FRESH_BARS:]
    return hits[0] >= recent[0] and still_there


def to_4h(df):
    """يحول شموع النص ساعة لشموع 4 ساعات بتوقيت نيويورك.
    السوق الممتد: 4-8، 8-12، 12-16، 16-20  (نفس تريدنج فيو مع تفعيل Extended Hours)
    السوق الرسمي: 9:30 - 13:30 ثم 13:30 - 16:00"""
    df = df.dropna(subset=["Open", "High", "Low", "Close"])
    if df.empty:
        return df
    idx = df.index
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
    df = df.set_index(idx.tz_convert(NY))
    first = 240 if GAP_EXTENDED else 570          # 4:00 أو 9:30 بالدقايق
    df = df.between_time("04:00", "19:59") if GAP_EXTENDED else df.between_time("09:30", "15:59")
    mins = df.index.hour * 60 + df.index.minute - first
    block = mins // 240
    start = df.index.normalize() + pd.Timedelta(minutes=first) + pd.to_timedelta(block * 240, unit="m")
    return df.groupby(start).agg(
        {"Open": "first", "High": "max", "Low": "min", "Close": "last"}
    )


def red(x):
    return x["Close"] < x["Open"]


def green(x):
    return x["Close"] > x["Open"]


def check_pattern(c):
    """يفحص آخر 4 شموع بالاتجاهين. يرجع تفاصيل النموذج لو تحقق، وإلا None.
    الشمعة الرابعة هي الشمعة الحالية (لسا ما قفلت) عشان التنبيه يطلع أول ما تلمس."""
    if len(c) < 4:
        return None
    c1, c2, c3, c4 = (c.iloc[i] for i in (-4, -3, -2, -1))

    # 🟢 صعودي: قاع الأولى فوق قمة الثالثة (الذيول ما تلتقي) - لون الشموع ما يهم
    if ENABLE_BULLISH and c1["Low"] > c3["High"]:
        gap_bottom = c3["High"]   # قمة الشمعة الثالثة
        gap_top = c1["Low"]       # قاع الشمعة الأولى = الخط المطلوب
        came_from_below = c4["Open"] < gap_top
        touched = c4["High"] >= gap_top * (1 - TOUCH_TOLERANCE)
        color_ok = green(c4) or not REQUIRE_FOURTH_COLOR
        if came_from_below and touched and color_ok:
            return {"side": "bull", "gap_bottom": gap_bottom, "gap_top": gap_top,
                    "price": c4["Close"], "candle_time": c.index[-1]}

    # 🔴 هبوطي: قمة الأولى تحت قاع الثالثة (الذيول ما تلتقي) - لون الشموع ما يهم
    if ENABLE_BEARISH and c1["High"] < c3["Low"]:
        gap_bottom = c1["High"]   # قمة الشمعة الأولى = الخط المطلوب
        gap_top = c3["Low"]       # قاع الشمعة الثالثة
        came_from_above = c4["Open"] > gap_bottom
        touched = c4["Low"] <= gap_bottom * (1 + TOUCH_TOLERANCE)
        color_ok = red(c4) or not REQUIRE_FOURTH_COLOR
        if came_from_above and touched and color_ok:
            return {"side": "bear", "gap_bottom": gap_bottom, "gap_top": gap_top,
                    "price": c4["Close"], "candle_time": c.index[-1]}

    return None


def scan_gap(tickers, already_sent):
    hits = 0
    for t, df in download_batches(tickers, 100, period="20d", interval="30m", prepost=GAP_EXTENDED):
        try:
            candles = to_4h(df)
            if candles.empty:
                continue
            if USE_PRICE_FILTER:
                last = float(candles["Close"].iloc[-1])
                if not (MIN_PRICE <= last <= MAX_PRICE):
                    continue
            if float(candles["Close"].iloc[-1]) < GAP_MIN_STOCK_PRICE:
                continue
            res = check_pattern(candles)
            if not res:
                continue
            if res["gap_top"] - res["gap_bottom"] < GAP_MIN_SIZE:
                continue
            key = f"{t}-{res['side']}-{res['candle_time']}"
            if key in already_sent:
                continue
            if not touch_is_fresh(df, res):
                continue                      # لمسة قديمة أو السعر رجع وطلع من الجاب
            already_sent.add(key)
            _append_line(GAP_SENT_FILE, key)
            hits += 1
            lo, hi, px = (round(float(res[k]), 2) for k in ("gap_bottom", "gap_top", "price"))
            if res["side"] == "bull":
                send_telegram(
                    f"🟢 Inversion Gap صعودي - فريم 4 ساعات\n"
                    f"السهم: {t}\n"
                    f"السعر: {px}\n"
                    f"الجاب: {lo} ← {hi}  (حجمه {hi - lo:.2f}$)\n"
                    f"الشمعة طلعت ولمست أعلى الجاب ({hi})"
                )
            else:
                send_telegram(
                    f"🔴 Inversion Gap هبوطي - فريم 4 ساعات\n"
                    f"السهم: {t}\n"
                    f"السعر: {px}\n"
                    f"الجاب: {lo} ← {hi}  (حجمه {hi - lo:.2f}$)\n"
                    f"الشمعة نزلت ولمست أسفل الجاب ({lo})"
                )
        except Exception as e:
            log(f"{t}: خطأ - {e}")
    log(f"[{datetime.now():%H:%M}] الجاب: خلص الفحص - {hits} تنبيه جديد")


# ================== (2) فلتر الأخبار ==================
def get_all_us_symbols(include_nyse=True):
    """كل الأسهم المدرجة في ناسداك (وبورصة نيويورك) من ملفات ناسداك الرسمية،
    بدون صناديق ETF ولا وارنتات ولا حقوق ولا وحدات."""
    base = "https://www.nasdaqtrader.com/dynamic/SymDir/"
    bad_name = r"Warrant|Right|Unit|Preferred|Depositary Shares|Notes|Debenture|%"
    symbols = set()

    def read(fname):
        txt = requests.get(base + fname, headers=HEADERS, timeout=30).text
        df = pd.read_csv(io.StringIO(txt), sep="|", dtype=str)
        return df[~df.iloc[:, 0].str.startswith("File Creation", na=False)]

    try:
        n = read("nasdaqlisted.txt")
        n = n[(n["Test Issue"] == "N") & (n["ETF"] == "N")]
        n = n[~n["Security Name"].str.contains(bad_name, case=False, na=False)]
        symbols.update(n["Symbol"].dropna())
    except Exception as e:
        log("ما قدرت أجيب قائمة ناسداك:", e)

    if include_nyse:
        try:
            o = read("otherlisted.txt")
            o = o[(o["Test Issue"] == "N") & (o["ETF"] == "N")]
            o = o[~o["Security Name"].str.contains(bad_name, case=False, na=False)]
            symbols.update(o["ACT Symbol"].dropna())
        except Exception as e:
            log("ما قدرت أجيب قائمة نيويورك:", e)

    return sorted(s for s in symbols if s.isalpha() and len(s) <= 5)


def build_universe(label, min_price, max_price, min_vol, include_nyse):
    """مرة باليوم: الأسهم اللي آخر سعر لها داخل النطاق وعليها تداول."""
    all_syms = get_all_us_symbols(include_nyse)
    log(f"{label}: أفحص {len(all_syms)} سهم عشان أطلع اللي سعرها {min_price}-{max_price}$ ...")
    keep = []
    for t, df in download_batches(all_syms, 400, period="5d", interval="1d", prepost=False):
        try:
            last = float(df["Close"].iloc[-1])
            avg_vol = float(df["Volume"].mean())
            if min_price <= last <= max_price and avg_vol >= min_vol:
                keep.append(t)
        except Exception:
            continue
    log(f"{label}: {len(keep)} سهم داخل الفلتر")
    return keep


def build_news_universe():
    return build_universe("الأخبار", NEWS_MIN_PRICE, NEWS_MAX_PRICE,
                          NEWS_MIN_AVG_VOLUME, NEWS_INCLUDE_NYSE)


def _parse_news_item(item):
    """ياهو غيّر شكل الأخبار أكثر من مرة، هذي تقرأ الشكلين القديم والجديد."""
    c = item.get("content") if isinstance(item.get("content"), dict) else item
    news_id = item.get("id") or c.get("id") or item.get("uuid")
    title = c.get("title") or ""
    # الوقت
    ts = None
    if c.get("pubDate"):
        ts = pd.Timestamp(c["pubDate"])
    elif c.get("providerPublishTime"):
        ts = pd.Timestamp(int(c["providerPublishTime"]), unit="s")
    if ts is not None and ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    # الرابط والمصدر
    link = ""
    for k in ("canonicalUrl", "clickThroughUrl"):
        if isinstance(c.get(k), dict) and c[k].get("url"):
            link = c[k]["url"]
            break
    link = link or c.get("link") or ""
    provider = c.get("provider")
    source = provider.get("displayName") if isinstance(provider, dict) else (c.get("publisher") or "")
    summary = c.get("summary") or c.get("description") or ""
    return {"id": news_id or f"{title}-{ts}", "title": title, "time": ts,
            "link": link, "source": source, "summary": summary}


POSITIVE_WORDS = """
beat beats surpass surpasses exceeded tops record soar soars soared surge surges surged jump jumps
jumped rally rallies rallied gain gains climb climbs rise rises rose upgrade upgraded upgrades
outperform buy raises raised raise boost boosts boosted strong stronger growth profit profitable
approval approved approves fda-approved clearance cleared breakthrough partnership partners
collaboration agreement contract awarded wins win won acquire acquisition acquires merger buyback
repurchase dividend expands expansion launch launches launched positive success successful
milestone higher bullish upbeat optimistic tops beat-and-raise guidance-raise order orders deal
""".split()
NEGATIVE_WORDS = """
miss misses missed plunge plunges plunged plummet plummets sink sinks sank drop drops dropped fall
falls fell slump slumps tumble tumbles tumbled decline declines declined downgrade downgraded
downgrades underperform sell cut cuts lowers lowered weak weaker loss losses lawsuit sued sues
probe investigation subpoena sec fraud recall recalls halt halted delisting delist delisted
bankruptcy bankrupt chapter default offering dilution dilutive reverse-split warning warns layoffs
layoff resign resigns resigned rejected rejects rejection fails failed failure crl negative bearish
concern concerns downbeat disappointing disappoints suspend suspended short-seller shortfall lower
""".split()


def news_sentiment(text):
    """تصنيف تقريبي: يعد الكلمات الإيجابية والسلبية في العنوان."""
    import re
    words = re.findall(r"[a-z][a-z\-]*", text.lower())
    pos = sum(w in POSITIVE_WORDS for w in words)
    neg = sum(w in NEGATIVE_WORDS for w in words)
    if pos > neg:
        return "🟢 إيجابي"
    if neg > pos:
        return "🔴 سلبي"
    return "⚪ محايد"


def fetch_news(t):
    import yfinance as yf
    try:
        return t, [_parse_news_item(n) for n in (yf.Ticker(t).news or [])]
    except Exception:
        return t, []


def scan_news(tickers, already_sent):
    hits = 0
    now = pd.Timestamp.now(tz="UTC")
    oldest = now - pd.Timedelta(minutes=NEWS_MAX_AGE_MIN)
    with ThreadPoolExecutor(max_workers=NEWS_WORKERS) as pool:
        for t, items in pool.map(fetch_news, tickers):
            for n in items:
                if not n["title"] or n["time"] is None or n["time"] < oldest:
                    continue
                key = f"{t}-{n['id']}"
                if key in already_sent:
                    continue
                already_sent.add(key)
                _append_line(NEWS_SENT_FILE, key)
                hits += 1
                local_time = n["time"].tz_convert(LOCAL_TZ)
                send_telegram(
                    f"📰 خبر جديد - {news_sentiment(n['title'])}\n"
                    f"السهم: {t}\n"
                    f"الخبر: {n['title']}\n"
                    f"المصدر: {n['source']}\n"
                    f"الوقت: {local_time:%H:%M} (توقيتك)\n"
                    f"{n['link']}"
                )
    log(f"[{datetime.now():%H:%M}] الأخبار: خلص الفحص - {hits} خبر جديد")


# ================== (3) نماذج الفريم اليومي ==================
def find_pivots(hi, lo, n):
    """القمم والقيعان المؤكدة، متناوبة (قمة، قاع، قمة ...)."""
    pts = []
    for i in range(n, len(hi) - n):
        if hi[i] == max(hi[i - n:i + n + 1]):
            pts.append((i, "H", hi[i]))
        if lo[i] == min(lo[i - n:i + n + 1]):
            pts.append((i, "L", lo[i]))
    pts.sort(key=lambda x: (x[0], x[1] == "L"))
    out = []
    for p in pts:
        if out and out[-1][1] == p[1]:
            # نفس النوع ورا بعض: نخلي الأقوى
            if (p[1] == "H" and p[2] >= out[-1][2]) or (p[1] == "L" and p[2] <= out[-1][2]):
                out[-1] = p
        else:
            out.append(p)
    return out


def _double_bottom(hi, lo, cl):
    """قاع مزدوج (W) واخترق خط العنق في آخر شمعة. يشتغل بالمقلوب للقمة المزدوجة."""
    t = len(cl) - 1
    piv = [p for p in find_pivots(hi, lo, PIVOT_BARS) if p[0] < t]
    tried = 0
    for j in range(len(piv) - 1, 0, -1):
        if piv[j][1] != "H":
            continue
        tried += 1
        if tried > 4:
            break
        h, neck = piv[j][0], piv[j][2]
        if piv[j - 1][1] != "L" or h + 1 >= t:
            continue
        l1, b1 = piv[j - 1][0], piv[j - 1][2]
        if t - l1 > PATTERN_MAX_BARS:
            break
        if max(cl[h + 1:t]) > neck:          # كسر الخط قبل كذا = مو تنبيه جديد
            continue
        l2 = h + 1 + int(pd.Series(lo[h + 1:t]).values.argmin())
        b2 = lo[l2]
        if l2 - l1 < PATTERN_MIN_BARS:
            continue
        if abs(b2 - b1) / min(abs(b1), abs(b2)) > DOUBLE_TOLERANCE:
            continue
        if (neck - max(b1, b2)) / abs(neck) < PATTERN_MIN_DEPTH:
            continue
        if cl[t] > neck:
            return {"b1": b1, "b2": b2, "neck": neck, "d1": l1, "d2": l2}
    return None


def _inv_head_shoulders(hi, lo, cl):
    """رأس وكتفين مقلوب واخترق خط العنق في آخر شمعة. يشتغل بالمقلوب للعادي."""
    t = len(cl) - 1
    piv = [p for p in find_pivots(hi, lo, PIVOT_BARS) if p[0] < t]
    for k in range(len(piv) - 4, max(len(piv) - 7, -1), -1):
        seq = piv[k:k + 4]
        if [p[1] for p in seq] != ["L", "H", "L", "H"]:
            continue
        (a, _, ls), (b, _, p1), (c, _, head), (d, _, p2) = seq
        if d + 1 >= t or t - a > PATTERN_MAX_BARS:
            continue
        r = d + 1 + int(pd.Series(lo[d + 1:t]).values.argmin())
        rs = lo[r]
        # الرأس أنزل من الكتفين
        if min(ls, rs) - head < HEAD_MIN_DIFF * abs(head):
            continue
        if abs(ls - rs) / min(abs(ls), abs(rs)) > SHOULDER_TOLERANCE:
            continue

        def neck_at(i):
            return p1 + (p2 - p1) * (i - b) / (d - b)

        if (min(p1, p2) - max(ls, rs)) / abs(min(p1, p2)) < PATTERN_MIN_DEPTH / 2:
            continue
        if any(cl[i] > neck_at(i) for i in range(d + 1, t)):
            continue                          # كسر الخط قبل كذا
        if cl[t] > neck_at(t):
            return {"ls": ls, "head": head, "rs": rs, "neck": neck_at(t)}
    return None


def check_daily_patterns(df):
    """يرجع قائمة النماذج اللي اكتملت اليوم (في آخر شمعة يومية)."""
    df = df.dropna(subset=["High", "Low", "Close"])
    if len(df) < 40:
        return []
    hi, lo, cl = (df[k].astype(float).values for k in ("High", "Low", "Close"))
    found = []
    if ENABLE_DOUBLE_BOTTOM:
        r = _double_bottom(hi, lo, cl)
        if r:
            found.append(("🟢 قاع مزدوج (W) - فريم يومي",
                          f"القاع الأول: {r['b1']:.2f}\nالقاع الثاني: {r['b2']:.2f}\n"
                          f"اخترق خط العنق لفوق: {r['neck']:.2f}"))
    if ENABLE_DOUBLE_TOP:
        r = _double_bottom(-lo, -hi, -cl)        # نفس الشي بالمقلوب
        if r:
            found.append(("🔴 قمة مزدوجة (M) - فريم يومي",
                          f"القمة الأولى: {-r['b1']:.2f}\nالقمة الثانية: {-r['b2']:.2f}\n"
                          f"كسر خط العنق لتحت: {-r['neck']:.2f}"))
    if ENABLE_INV_HS:
        r = _inv_head_shoulders(hi, lo, cl)
        if r:
            found.append(("🟢 رأس وكتفين مقلوب - فريم يومي",
                          f"الكتف الأيسر: {r['ls']:.2f}\nالرأس: {r['head']:.2f}\n"
                          f"الكتف الأيمن: {r['rs']:.2f}\nاخترق خط العنق لفوق: {r['neck']:.2f}"))
    if ENABLE_HS:
        r = _inv_head_shoulders(-lo, -hi, -cl)   # نفس الشي بالمقلوب
        if r:
            found.append(("🔴 رأس وكتفين - فريم يومي",
                          f"الكتف الأيسر: {-r['ls']:.2f}\nالرأس: {-r['head']:.2f}\n"
                          f"الكتف الأيمن: {-r['rs']:.2f}\nكسر خط العنق لتحت: {-r['neck']:.2f}"))
    return found


def scan_daily(tickers, already_sent):
    hits = 0
    today = pd.Timestamp.now(tz=NY).date()
    for t, df in download_batches(tickers, 200, period="1y", interval="1d", prepost=False):
        try:
            for title, details in check_daily_patterns(df):
                key = f"{t}-{title}-{today}"
                if key in already_sent:
                    continue
                already_sent.add(key)
                hits += 1
                send_telegram(f"{title}\nالسهم: {t}\nالسعر: {float(df['Close'].iloc[-1]):.2f}\n{details}")
        except Exception as e:
            log(f"{t}: خطأ يومي - {e}")
    log(f"[{datetime.now():%H:%M}] اليومي: خلص الفحص - {hits} تنبيه جديد")


def regular_session_open():
    now = pd.Timestamp.now(tz=NY)
    if now.weekday() >= 5:
        return False
    return now.replace(hour=9, minute=30) <= now <= now.replace(hour=16, minute=10)


# ================== (4) الشورت صفر ==================
def _load_set(path):
    try:
        with open(path, encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()


def _append_line(path, line):
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def fetch_short(t):
    import yfinance as yf
    try:
        info = yf.Ticker(t).info or {}
        return t, info.get("sharesShort"), info.get("sharesShortPriorMonth"), \
            info.get("dateShortInterest"), info.get("currentPrice") or info.get("regularMarketPrice")
    except Exception:
        return t, None, None, None, None


def scan_short(tickers, already_sent):
    hits = 0
    with ThreadPoolExecutor(max_workers=SHORT_WORKERS) as pool:
        for t, short, prior, date, price in pool.map(fetch_short, tickers):
            # لازم الرقم موجود ويساوي صفر (مو ناقص) - كثير مواقع تعرض صفر وهو بس ما عندها بيانات
            if short is None or short != 0:
                continue
            key = f"{t}-{date}"
            if key in already_sent:
                continue
            already_sent.add(key)
            _append_line(SHORT_SENT_FILE, key)
            hits += 1
            d = pd.Timestamp(int(date), unit="s").strftime("%Y-%m-%d") if date else "غير معروف"
            prior_txt = f"{int(prior):,}" if prior is not None else "غير معروف"
            send_telegram(
                f"🩳 الشورت صفر\n"
                f"السهم: {t}\n"
                f"السعر: {price}\n"
                f"الشورت الحالي: 0\n"
                f"الشورت الشهر اللي قبله: {prior_txt}\n"
                f"تاريخ البيانات: {d}"
            )
    log(f"[{datetime.now():%H:%M}] الشورت: خلص الفحص - {hits} تنبيه جديد")


# ================== التشغيل ==================
def main():
    once = "--once" in sys.argv
    _load_chats()
    discover_groups()
    log(f"التنبيهات بتروح لـ {len(CHATS)} محادثة: {', '.join(CHATS) or 'ولا وحدة'}")

    gap_tickers, gap_day = [], None
    gap_sent = _load_set(GAP_SENT_FILE)
    news_tickers, news_day, news_last = [], None, 0.0
    news_sent = _load_set(NEWS_SENT_FILE)
    daily_tickers, daily_day, daily_last = [], None, 0.0
    daily_sent = set()
    short_day = None
    short_sent = _load_set(SHORT_SENT_FILE)

    while True:
        discover_groups()
        # (1) الجاب - وقت السوق الأمريكي
        if ENABLE_GAP and (us_market_open() or once):
            today = pd.Timestamp.now(tz=NY).date()
            if gap_day != today or not gap_tickers:
                gap_tickers = get_nasdaq_midcap_plus()
                gap_day = today
                log(f"الجاب: {len(gap_tickers)} سهم ناسداك قيمتها السوقية {MIN_MARKET_CAP/1e9:.0f} مليار وفوق")
            scan_gap(gap_tickers, gap_sent)

        # (2) الأخبار - 24 ساعة
        if ENABLE_NEWS and time.time() - news_last >= NEWS_EVERY_MIN * 60:
            today = pd.Timestamp.now(tz=NY).date()
            if news_day != today or not news_tickers:
                news_tickers = build_news_universe()
                news_day = today
            scan_news(news_tickers, news_sent)
            news_last = time.time()

        # (3) النماذج اليومية - وقت السوق الرسمي، كل نص ساعة
        if ENABLE_DAILY and (regular_session_open() or once) \
                and time.time() - daily_last >= DAILY_EVERY_MIN * 60:
            today = pd.Timestamp.now(tz=NY).date()
            if daily_day != today or not daily_tickers:
                daily_tickers = build_universe("اليومي", DAILY_MIN_PRICE, 100_000,
                                               DAILY_MIN_AVG_VOLUME, include_nyse=False)
                daily_day = today
                daily_sent.clear()
            scan_daily(daily_tickers, daily_sent)
            daily_last = time.time()

        # (4) الشورت صفر - مرة باليوم
        if ENABLE_SHORT:
            today = pd.Timestamp.now(tz=LOCAL_TZ).date()
            if short_day != today:
                short_tickers = build_universe("الشورت", SHORT_MIN_PRICE, SHORT_MAX_PRICE,
                                               SHORT_MIN_AVG_VOLUME, include_nyse=False)
                scan_short(short_tickers, short_sent)
                short_day = today

        if not us_market_open():
            log(f"[{datetime.now():%H:%M}] السوق مسكر (الأخبار شغالة)، أنتظر...")

        if once:
            break
        time.sleep(CHECK_EVERY_MIN * 60)


if __name__ == "__main__":
    main()
