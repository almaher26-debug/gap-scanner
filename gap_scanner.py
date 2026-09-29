"""
بوت التنبيهات - يشتغل على Railway ويرسل على تيليجرام
=====================================================

(1) نموذج الـ Inversion Gap - فريمين: 4 ساعات + ساعة
    الأسهم: كل أسهم ناسداك اللي قيمتها السوقية 2 مليار دولار وفوق (ميد كاب وأعلى)
    ⚠️ لون الشموع الثلاث ما يهم - المهم إن ذيل الشمعة الأولى والثالثة ما يلتقون

    🟢 صعودي (جاب تحت):
      - ثلاث شموع، وقاع الشمعة الأولى أعلى من قمة الشمعة الثالثة
      - الجاب = من قمة الشمعة الثالثة (تحت) إلى قاع الشمعة الأولى (فوق)
      - الشمعة الرابعة تجي من تحت وتطلع فوق أعلى الجاب
    🔴 هبوطي (جاب فوق): نفس الشي بالعكس، والشمعة الرابعة تنزل تحت أسفل الجاب

    ⏱️ متى يجي التنبيه (الفريمين نفس الشي):
      - أول ما تقفل الشمعة الرابعة فوق أعلى الجاب (صعودي) أو تحت أسفله (هبوطي)
      - البوت يفحص بعد إغلاق كل شمعة بدقيقة، ويعيد الفحص بعد 5 و16 دقيقة لو البيانات تأخرت

    🕐 تقسيم الشموع نفس تريدنج فيو:
      - 24 ساعة (مع الجلسة الليلية): شموع الـ4 ساعات تبدأ 8 بالليل نيويورك
        (8-12، 12-4، 4-8، 8-12، 12-4، 4-8) = بتوقيتك 3، 7، 11، 15، 19، 23
      - ⚠️ ياهو ما عنده بيانات الجلسة الليلية (8 بالليل - 4 الفجر)، فعشان الـ24 ساعة
        تحتاج مفتاح Tiingo (باقة Power + إضافة BOATS). بدونه يشتغل على 4 الفجر - 8 بالليل بس

    فلتر: السهم سعره فوق 10$ ، وحجم الجاب (الفرق بين الحدين) 0.50$ أو أكثر

(2) الأخبار - 24 ساعة - الإيجابية بس
    - كل أسهم ناسداك (عليها تداول)
    - يرسل الأخبار الإيجابية بس: اندماج، استحواذ، أرباح ونتائج، موافقات، عقود وشراكات...
      والسلبي والمحايد يتجاهلهم (التصنيف تقريبي من كلمات العنوان، مو دقيق 100%)
    - عنوان الخبر يتترجم للعربي (لو فشلت الترجمة يرسله بالإنجليزي)
    - المصدر: ياهو فاينانس

(3) نماذج الفريم اليومي - كل أسهم ناسداك - التنبيه عند اكتمال النموذج (كسر خط العنق)
    - يرسل أي سهم اخترق/كسر خط العنق خلال آخر شهر (22 يوم تداول)، مو بس اليوم
    - كل نموذج يتنبه عليه مرة وحدة بس، والتنبيهات تنجمع في رسايل عشان ما يزحم القروب
    🟢 القاع المزدوج (W)        : قاعين متقاربين (فرق 3% أو أقل) + اختراق خط العنق لفوق
    🔴 القمة المزدوجة (M)       : قمتين متقاربتين (فرق 3% أو أقل) + كسر خط العنق لتحت
    🔴 الرأس والكتفين            : كتف + رأس أعلى + كتف + كسر خط العنق لتحت
    🟢 الرأس والكتفين المقلوب    : كتف + رأس أنزل + كتف + اختراق خط العنق لفوق

(4) الشورت صفر
    - أسهم ناسداك اللي سعرها من 1 إلى 6 دولار
    - إذا بيانات الشورت الرسمية (من ياهو) صارت صفر  =>  تنبيه
    - البيانات الرسمية تنزل مرتين بالشهر وبتأخير أسبوعين تقريباً، فيفحصها مرة باليوم

(5) الزخم - أسهم ناسداك الرخيصة اللي دخلها حجم تداول مفاجئ
    - السعر من 1 إلى 5 دولار
    - حجم التداول في آخر نص ساعة 700 ألف سهم أو أكثر
    - الفري فلوت من 700 ألف إلى 8 مليون سهم (من ياهو - لو ما عرفه يرسل ويكتب "غير معروف")
    - يفحص كل 5 دقايق من 4 الفجر إلى 8 بالليل نيويورك (يشمل ما قبل الفتح وبعد الإغلاق)

التشغيل:
  pip install yfinance pandas requests lxml
  python gap_scanner.py          # يشتغل باستمرار ويفحص كل 5 دقايق
  python gap_scanner.py --once   # فحص مرة وحدة بس
  python gap_scanner.py --test   # يجرب نموذج الجاب على مثال NVDA (بدون نت)
"""

import gc
import io
import logging
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

LOOP_SLEEP_SEC = 20          # كل كم ثانية يشيك هل جا وقت فحص
NY = "America/New_York"
LOCAL_TZ = "Asia/Riyadh"     # توقيتك المحلي

# ---- (1) نموذج الجاب ----
ENABLE_GAP = True
MIN_MARKET_CAP = 2_000_000_000   # 2 مليار دولار = ميد كاب وفوق
ENABLE_BULLISH = True            # جاب تحت + الرابعة تقفل فوق أعلى الجاب
ENABLE_BEARISH = True            # جاب فوق + الرابعة تقفل تحت أسفل الجاب
# شروط الاتجاه (True = مفعّل ، False = يتجاهله)
REQUIRE_3_CANDLES_DIRECTION = True   # صعودي: الثلاث الأولى كلها حمراء (هابطة) ، هبوطي: كلها خضراء (صاعدة)
REQUIRE_4TH_CANDLE_COLOR = True      # صعودي: الرابعة خضراء ، هبوطي: الرابعة حمراء
GAP_EXTENDED = True              # يشمل ما قبل الفتح وبعد الإغلاق (4 الفجر - 8 بالليل نيويورك)

# الجلسة الليلية (8 بالليل - 4 الفجر نيويورك) = إعداد الـ24 ساعة في تريدنج فيو
# ياهو ما يعطيها، فتجي من Tiingo: حط المفتاح كمتغير TIINGO_TOKEN على Railway
TIINGO_TOKEN = os.environ.get("TIINGO_TOKEN", "")
GAP_OVERNIGHT = bool(TIINGO_TOKEN)   # يتفعل لحاله لو حطيت المفتاح
TIINGO_WORKERS = 8

GAP_MIN_STOCK_PRICE = 10         # يتجاهل الأسهم اللي سعرها أقل من كذا
GAP_MIN_SIZE = 0.50              # يتجاهل الجاب اللي حجمه أقل من كذا (دولار)
ENABLE_GAP_4H = True             # فريم 4 ساعات - ينبه عند إغلاق الشمعة
ENABLE_GAP_1H = True             # فريم ساعة - ينبه عند إغلاق الشمعة
GAP_SCAN_AFTER_CLOSE_MIN = (1, 5, 16)   # يفحص بعد الإغلاق بكذا دقيقة (الأولى هي الأساسية)
GAP_MAX_ALERT_DELAY_MIN = 30     # ما ينبه على شمعة قفلت من أكثر من كذا دقيقة (عشان ما يرسل قديم أول ما يشتغل)
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
NEWS_WORKERS = 3                 # عدد الطلبات المتوازية على ياهو (كثرتها تخلي ياهو يحظر)
NEWS_CHUNK = 100                 # يفحص الأسهم على دفعات، وبين كل دفعة يشيك هل ياهو حاظره
NEWS_CHUNK_PAUSE_SEC = 2         # استراحة بين الدفعات
NEWS_MAX_BACKOFF_MIN = 60        # لو ياهو حظر، يوقف ويرجع بعد وقت يزيد لين هالحد
NEWS_SENT_FILE = "news_sent.txt" # عشان ما يعيد نفس الخبر لو البوت أعاد التشغيل
NEWS_ONLY_POSITIVE = True        # True = يرسل الأخبار الإيجابية بس
NEWS_TRANSLATE = True            # True = يترجم عنوان الخبر للعربي

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
DAILY_LOOKBACK_DAYS = 22         # يرسل النماذج اللي اخترقت خلال آخر كذا يوم تداول (22 = شهر تقريباً)
DAILY_SENT_FILE = "daily_sent.txt"   # عشان ما يعيد نفس النموذج كل يوم

# ---- (4) الشورت صفر ----
ENABLE_SHORT = True
SHORT_MIN_PRICE = 1
SHORT_MAX_PRICE = 6
SHORT_MIN_AVG_VOLUME = 50_000
SHORT_WORKERS = 3
SHORT_SENT_FILE = "short_sent.txt"   # عشان ما يعيد نفس التنبيه لو البوت أعاد التشغيل

# ---- (5) الزخم ----
ENABLE_MOMENTUM = True
MOMENTUM_MIN_PRICE = 1
MOMENTUM_MAX_PRICE = 5
MOMENTUM_MIN_VOLUME = 700_000        # حجم التداول في آخر نص ساعة (عدد أسهم)
MOMENTUM_WINDOW_MIN = 30             # نص ساعة
MOMENTUM_MIN_FLOAT = 700_000         # الفري فلوت من كذا
MOMENTUM_MAX_FLOAT = 8_000_000       # إلى كذا
MOMENTUM_SEND_UNKNOWN_FLOAT = True   # True = لو ياهو ما عنده الفري فلوت يرسله ويكتب "غير معروف"
MOMENTUM_EVERY_MIN = 5               # كل كم دقيقة يفحص
MOMENTUM_REALERT_MIN = 120           # ما يعيد تنبيه نفس السهم قبل كذا دقيقة

SENT_KEEP_LINES = 20000             # ملفات "المرسل" تنقص لآخر كذا سطر عشان ما تكبر للأبد
UNIVERSE_BATCH = 200                # حجم دفعة التحميل لما يفلتر كل الأسهم (أصغر = ذاكرة أقل)
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


class _YFNoise(logging.Filter):
    """يخفي رسائل ياهو المزعجة (مئات الأسطر كل فحص) ويعدّها بدالها."""
    news_fail = 0
    other = 0

    def filter(self, rec):
        try:
            msg = rec.getMessage()
        except Exception:
            msg = ""
        if "Failed to retrieve the news" in msg:
            _YFNoise.news_fail += 1
        else:
            _YFNoise.other += 1
        return False


logging.getLogger("yfinance").addFilter(_YFNoise())


def free_memory():
    """يرجّع الذاكرة بعد كل فحص كبير."""
    gc.collect()


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


def _session():
    """(بداية تقسيم الشموع، نهاية الجلسة) بالدقايق من منتصف الليل بتوقيت نيويورك.
    نهاية None = 24 ساعة."""
    if GAP_OVERNIGHT:
        return 20 * 60, None          # 24 ساعة، اليوم يبدأ 8 بالليل (نفس تريدنج فيو)
    if GAP_EXTENDED:
        return 4 * 60, 20 * 60
    return 9 * 60 + 30, 16 * 60


def us_market_open(now=None):
    """السوق مفتوح حسب الجلسة المختارة (+ دقايق بعد الإغلاق عشان نلحق نفحص آخر شمعة)."""
    now = now or pd.Timestamp.now(tz=NY)
    wd, m = now.weekday(), now.hour * 60 + now.minute
    buf = max(GAP_SCAN_AFTER_CLOSE_MIN) + 2
    if GAP_OVERNIGHT:                 # من الأحد 8 بالليل إلى الجمعة 8 بالليل
        if wd == 5:
            return False
        if wd == 6:
            return m >= 20 * 60
        if wd == 4:
            return m <= 20 * 60 + buf
        return True
    if wd >= 5:
        return False
    start, end = _session()
    return start <= m <= end + buf


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
        del data
        free_memory()
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


OHLC = ["Open", "High", "Low", "Close"]


def to_ny(df):
    df = df.dropna(subset=OHLC)
    idx = df.index
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
    return df.set_index(idx.tz_convert(NY))


def _hhmm(m):
    return f"{m // 60:02d}:{m % 60:02d}"


def to_frame(df, minutes):
    """يحول شموع النص ساعة لشموع أكبر (60 = ساعة، 240 = 4 ساعات) بتوقيت نيويورك،
    بنفس تقسيم تريدنج فيو. كل شمعة معها وقت إغلاقها (end) وعدد الشموع الصغيرة اللي فيها (n)."""
    df = df.dropna(subset=OHLC)
    if df.empty:
        return df
    df = to_ny(df)
    anchor, end_min = _session()
    if end_min is not None:                    # مو 24 ساعة: نشيل اللي برا الجلسة
        df = df.between_time(_hhmm(anchor), _hhmm(end_min - 1))
        if df.empty:
            return df
    m = df.index.hour * 60 + df.index.minute
    offset = ((m - anchor) % 1440) % minutes   # كم دقيقة من بداية شمعتها
    start = df.index.floor("min") - pd.to_timedelta(offset, unit="m")
    out = df.groupby(start).agg(Open=("Open", "first"), High=("High", "max"),
                                Low=("Low", "min"), Close=("Close", "last"),
                                n=("Close", "size"))
    ends = []
    for s in out.index:
        e = s + pd.Timedelta(minutes=minutes)
        if end_min is not None:                # آخر شمعة باليوم تقفل مع إغلاق الجلسة
            e = min(e, s.normalize() + pd.Timedelta(minutes=end_min))
        ends.append(e)
    out["end"] = ends
    return out


def to_4h(df):
    return to_frame(df, 240)


def only_closed(c, last_bar, now):
    """يخلي الشموع المقفلة بس. الشمعة تعتبر مقفلة لو وقتها خلص، وبياناتها كاملة
    (أو جات بيانات بعدها، أو مر ربع ساعة على إغلاقها)."""
    if c.empty:
        return c
    starts = pd.Series(c.index, index=c.index)
    expected = ((c["end"] - starts).dt.total_seconds() / 1800).round()
    done = (c["end"] <= now) & ((c["n"] >= expected) | (last_bar >= c["end"])
                                | (now >= c["end"] + pd.Timedelta(minutes=15)))
    return c[done.values]


def check_pattern(c):
    """يفحص آخر 4 شموع مقفلة بالاتجاهين. يرجع تفاصيل النموذج لو تحقق، وإلا None.
    صعودي: الثلاث الأولى هابطة (حمراء) + جاب بين ذيل الأولى والثالثة + الرابعة خضراء تقفل فوق الجاب.
    هبوطي: بالعكس. (شروط اللون تنطفي من REQUIRE_3_CANDLES_DIRECTION و REQUIRE_4TH_CANDLE_COLOR)"""
    if len(c) < 4:
        return None
    c1, c2, c3, c4 = (c.iloc[i] for i in (-4, -3, -2, -1))
    info = {"price": c4["Close"], "open": c4["Open"], "candle_time": c.index[-1],
            "end": c4["end"] if "end" in c else c.index[-1]}
    first3 = (c1, c2, c3)
    all_red = all(x["Close"] < x["Open"] for x in first3)     # الثلاث هابطة
    all_green = all(x["Close"] > x["Open"] for x in first3)   # الثلاث صاعدة

    # 🟢 صعودي: ثلاث شموع هابطة، قاع الأولى فوق قمة الثالثة،
    #    والرابعة خضراء تفتح تحت أعلى الجاب وتقفل فوقه
    if ENABLE_BULLISH and c1["Low"] > c3["High"]:
        gap_bottom = c3["High"]   # قمة الشمعة الثالثة
        gap_top = c1["Low"]       # قاع الشمعة الأولى = الخط المطلوب
        ok = c4["Open"] < gap_top and c4["Close"] > gap_top
        if REQUIRE_3_CANDLES_DIRECTION and not all_red:
            ok = False
        if REQUIRE_4TH_CANDLE_COLOR and not c4["Close"] > c4["Open"]:
            ok = False
        if ok:
            return {"side": "bull", "gap_bottom": gap_bottom, "gap_top": gap_top, **info}

    # 🔴 هبوطي: ثلاث شموع صاعدة، قمة الأولى تحت قاع الثالثة،
    #    والرابعة حمراء تفتح فوق أسفل الجاب وتقفل تحته
    if ENABLE_BEARISH and c1["High"] < c3["Low"]:
        gap_bottom = c1["High"]   # قمة الشمعة الأولى = الخط المطلوب
        gap_top = c3["Low"]       # قاع الشمعة الثالثة
        ok = c4["Open"] > gap_bottom and c4["Close"] < gap_bottom
        if REQUIRE_3_CANDLES_DIRECTION and not all_green:
            ok = False
        if REQUIRE_4TH_CANDLE_COLOR and not c4["Close"] < c4["Open"]:
            ok = False
        if ok:
            return {"side": "bear", "gap_bottom": gap_bottom, "gap_top": gap_top, **info}

    return None


def _gap_message(t, res, frame):
    lo, hi, px = (round(float(res[k]), 2) for k in ("gap_bottom", "gap_top", "price"))
    if res["side"] == "bull":
        head = f"🟢 Inversion Gap صعودي - {frame}"
        line = f"الشمعة قفلت فوق أعلى الجاب ({hi})"
    else:
        head = f"🔴 Inversion Gap هبوطي - {frame}"
        line = f"الشمعة قفلت تحت أسفل الجاب ({lo})"
    closed_at = pd.Timestamp(res["end"]).tz_convert(LOCAL_TZ)
    return (f"{head}\n"
            f"السهم: {t}\n"
            f"الجاب: {lo} ← {hi}  (حجمه {hi - lo:.2f}$)\n"
            f"{line}\n"
            f"سعر الإغلاق: {px}\n"
            f"وقت الإغلاق: {closed_at:%H:%M} (توقيتك)")


# ---------- الجلسة الليلية من Tiingo (8 بالليل - 4 الفجر نيويورك) ----------
_boats_cache = {}   # الرمز -> (وقت الجلب، البيانات)


def _boats_stale(fetched, now):
    if fetched is None:
        return True
    if now.hour >= 20 or now.hour * 60 + now.minute < 4 * 60 + 20:
        return fetched < now.floor("h")        # وقت الليل: نجدد كل ساعة
    return fetched < now.normalize() + pd.Timedelta(hours=4)   # بعد الليل: نسخة وحدة تكفي


def fetch_boats(t, now):
    """شموع نص ساعة للجلسة الليلية لسهم واحد من Tiingo (BOATS)."""
    try:
        r = requests.get(f"https://api.tiingo.com/boats/{t.lower()}/prices",
                         params={"startDate": (now - pd.Timedelta(days=7)).strftime("%Y-%m-%d"),
                                 "resampleFreq": "30min", "token": TIINGO_TOKEN},
                         headers={**HEADERS, "Content-Type": "application/json"}, timeout=20)
        data = r.json()
        if not isinstance(data, list) or not data:
            if isinstance(data, dict) and data.get("detail"):
                log(f"Tiingo {t}: {data['detail']}")
            return pd.DataFrame(columns=OHLC)
        df = pd.DataFrame(data)
        idx = pd.to_datetime(df["date"])
        idx = idx.dt.tz_localize(NY) if idx.dt.tz is None else idx.dt.tz_convert(NY)
        df = df.rename(columns=str.capitalize).set_index(pd.DatetimeIndex(idx))[OHLC]
        df = df.astype(float).dropna()
        h = df.index.hour
        return df[(h >= 20) | (h < 4)]         # الليل بس، الباقي من ياهو
    except Exception as e:
        log(f"Tiingo {t}: خطأ - {e}")
        return None


def load_boats(tickers, now):
    need = [t for t in tickers if _boats_stale((_boats_cache.get(t) or (None,))[0], now)]
    if need:
        with ThreadPoolExecutor(max_workers=TIINGO_WORKERS) as pool:
            for t, df in zip(need, pool.map(lambda s: fetch_boats(s, now), need)):
                if df is not None:
                    _boats_cache[t] = (now, df)
        log(f"الجلسة الليلية: جددت {len(need)} سهم من Tiingo")
    return {t: v[1] for t, v in _boats_cache.items()}


def scan_gap(tickers, already_sent):
    hits = 0
    now = pd.Timestamp.now(tz=NY)
    boats = load_boats(tickers, now) if GAP_OVERNIGHT else {}
    frames = [(ENABLE_GAP_4H, 240, "4h", "فريم 4 ساعات"), (ENABLE_GAP_1H, 60, "1h", "فريم ساعة")]
    for t, df in download_batches(tickers, 100, period="7d", interval="30m",
                                  prepost=GAP_EXTENDED or GAP_OVERNIGHT):
        try:
            df = to_ny(df)[OHLC]
            night = boats.get(t)
            if night is not None and not night.empty:
                df = pd.concat([df, night])
                df = df[~df.index.duplicated(keep="first")].sort_index()
            if df.empty:
                continue
            last = float(df["Close"].iloc[-1])
            if USE_PRICE_FILTER and not (MIN_PRICE <= last <= MAX_PRICE):
                continue
            if last < GAP_MIN_STOCK_PRICE:
                continue
            last_bar = df.index.max()

            for enabled, minutes, tag, label in frames:
                if not enabled:
                    continue
                res = check_pattern(only_closed(to_frame(df, minutes), last_bar, now))
                if not res or res["gap_top"] - res["gap_bottom"] < GAP_MIN_SIZE:
                    continue
                if (now - res["end"]).total_seconds() / 60 > GAP_MAX_ALERT_DELAY_MIN:
                    continue                    # شمعة قديمة، مو إغلاق جديد
                key = f"{t}-{tag}-{res['side']}-{res['candle_time']}"
                if key in already_sent:
                    continue
                already_sent.add(key)
                _append_line(GAP_SENT_FILE, key)
                hits += 1
                send_telegram(_gap_message(t, res, label))
        except Exception as e:
            log(f"{t}: خطأ - {e}")
    free_memory()
    log(f"[{datetime.now():%H:%M}] الجاب: خلص الفحص - {hits} تنبيه جديد")


def gap_scan_due(now, last_run):
    """بعد إغلاق كل شمعة بدقيقة (وإعادة بعد 5 و16 دقيقة). يرجع وقت الجولة لو جا وقتها."""
    step = "30min" if not (GAP_EXTENDED or GAP_OVERNIGHT) else "h"   # الجلسة الرسمية تقفل على :30
    boundary = now.floor(step)
    for off in sorted(GAP_SCAN_AFTER_CLOSE_MIN, reverse=True):
        slot = boundary + pd.Timedelta(minutes=off)
        if now >= slot:
            return slot if (last_run is None or last_run < slot) else None
    return None


def self_test():
    """يجرب النموذج على مثال NVDA اللي بالصورة (فريم 4 ساعات، 24 ساعة) بدون نت."""
    global GAP_OVERNIGHT
    for overnight, times in ((True, ("2026-09-25 16:00", "2026-09-27 20:00",
                                     "2026-09-28 00:00", "2026-09-28 04:00")),
                             (False, ("2026-09-25 08:00", "2026-09-25 12:00",
                                      "2026-09-25 16:00", "2026-09-28 04:00"))):
        GAP_OVERNIGHT = overnight
        print("=========", "24 ساعة" if overnight else "ممتد بدون ليل (ياهو)", "=========")
        _self_test_run(times)


def _self_test_run(times):
    # نفس أسعار الصورة: (فتح، أعلى، أقل، إغلاق) لكل شمعة 4 ساعات
    prices = [(225.00, 225.40, 224.87, 224.95),   # الأولى - قاعها 224.87
              (225.05, 225.80, 223.75, 223.80),   # الثانية
              (223.80, 224.33, 223.00, 223.10),   # الثالثة - قمتها 224.33
              (223.50, 228.30, 222.90, 228.08)]   # الرابعة - تقفل فوق 224.87
    candles = [(t, *p) for t, p in zip(times, prices)]
    rows = []
    for s, o, h, l, c in candles:
        s = pd.Timestamp(s, tz=NY)
        path = [o + (c - o) * k / 7 for k in range(8)]
        for k in range(8):                                     # 8 شموع نص ساعة لكل 4 ساعات
            op = path[k - 1] if k else o
            rows.append((s + pd.Timedelta(minutes=30 * k), op,
                         h if k == 3 else max(op, path[k]),
                         l if k == 5 else min(op, path[k]), path[k]))
    df = pd.DataFrame(rows, columns=["t"] + OHLC).set_index("t")

    for label, now in (("قبل إغلاق الرابعة (7:59 نيويورك)", "2026-09-28 07:59"),
                       ("بعد الإغلاق بدقيقة (8:01 نيويورك)", "2026-09-28 08:01")):
        now = pd.Timestamp(now, tz=NY)
        part = df[df.index <= now - pd.Timedelta(minutes=30)]
        c = only_closed(to_frame(part, 240), part.index.max(), now)
        res = check_pattern(c)
        print(f"--- {label} ---")
        print(c[OHLC + ["n"]].tail(4).to_string())
        print(_gap_message("NVDA", res, "فريم 4 ساعات") if res else "ما فيه تنبيه")
        print()


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


_universe_cache = {}   # (اليوم، مع نيويورك؟) -> {الرمز: (آخر سعر، متوسط الحجم)}


def _universe_stats(include_nyse):
    """آخر سعر ومتوسط الحجم لكل الأسهم. ينحمّل مرة وحدة باليوم ويستخدمه
    الأخبار واليومي والشورت كلهم (بدل ما كل واحد يحمّل 3000 سهم لحاله)."""
    key = (pd.Timestamp.now(tz=NY).date(), bool(include_nyse))
    if key in _universe_cache:
        return _universe_cache[key]
    _universe_cache.clear()
    all_syms = get_all_us_symbols(include_nyse)
    log(f"الفلتر: أحمّل أسعار {len(all_syms)} سهم (مرة وحدة باليوم) ...")
    stats = {}
    for t, df in download_batches(all_syms, UNIVERSE_BATCH, period="5d", interval="1d", prepost=False):
        try:
            stats[t] = (float(df["Close"].iloc[-1]), float(df["Volume"].mean()))
        except Exception:
            continue
    _universe_cache[key] = stats
    free_memory()
    return stats


def build_universe(label, min_price, max_price, min_vol, include_nyse):
    """الأسهم اللي آخر سعر لها داخل النطاق وعليها تداول."""
    stats = _universe_stats(include_nyse)
    keep = [t for t, (last, avg_vol) in stats.items()
            if min_price <= last <= max_price and avg_vol >= min_vol]
    log(f"{label}: {len(keep)} سهم سعرها {min_price}-{max_price}$ وعليها تداول")
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


NEWS_CATEGORIES = [
    ("🤝 اندماج / استحواذ", "merger merge merges merging acquire acquires acquired acquisition "
                          "acquisitions buyout takeover to-be-acquired tender"),
    ("💰 أرباح / نتائج", "earnings profit profits profitable revenue revenues results eps quarter "
                        "quarterly q1 q2 q3 q4 guidance record"),
    ("💊 موافقة", "fda approval approved approves clearance cleared"),
    ("📝 عقد / شراكة", "contract contracts partnership partners collaboration agreement awarded order orders deal"),
    ("🔁 إعادة شراء / توزيعات", "buyback repurchase dividend"),
]
NEWS_CATEGORIES = [(name, set(words.split())) for name, words in NEWS_CATEGORIES]


def news_classify(text):
    """تصنيف تقريبي من كلمات العنوان. يرجع (النوع، التصنيف)
    النوع: إيجابي / سلبي / محايد ، والتصنيف مثل اندماج أو أرباح."""
    import re
    t = text.lower().replace("to be acquired", "to-be-acquired")
    words = re.findall(r"[a-z0-9][a-z0-9\-]*", t)
    pos = sum(w in POSITIVE_WORDS for w in words)
    neg = sum(w in NEGATIVE_WORDS for w in words)
    category = next((name for name, keys in NEWS_CATEGORIES if any(w in keys for w in words)), "")
    if neg > pos:
        return "negative", category
    if pos > neg or (category and neg == 0):
        return "positive", category
    return "neutral", category


def news_sentiment(text):
    kind, _ = news_classify(text)
    return {"positive": "🟢 إيجابي", "negative": "🔴 سلبي"}.get(kind, "⚪ محايد")


_translations = {}


def translate_ar(text):
    """يترجم العنوان للعربي. يجرب قوقل وبعدين MyMemory، ولو فشلوا يرجع None."""
    if text in _translations:
        return _translations[text]
    result = None
    try:
        r = requests.get("https://translate.googleapis.com/translate_a/single",
                         params={"client": "gtx", "sl": "en", "tl": "ar", "dt": "t", "q": text},
                         headers=HEADERS, timeout=8)
        data = r.json()
        result = "".join(seg[0] for seg in data[0] if seg and seg[0])
    except Exception:
        pass
    if not result or not any("\u0600" <= ch <= "\u06ff" for ch in result):
        try:
            r = requests.get("https://api.mymemory.translated.net/get",
                             params={"q": text[:480], "langpair": "en|ar"}, timeout=8)
            result = r.json()["responseData"]["translatedText"]
        except Exception:
            result = None
    if result and not any("\u0600" <= ch <= "\u06ff" for ch in result):
        result = None                     # ما طلع عربي = الترجمة فشلت
    _translations[text] = result
    return result


def fetch_news(t):
    import yfinance as yf
    try:
        return t, [_parse_news_item(n) for n in (yf.Ticker(t).news or [])]
    except Exception:
        return t, []


_news_state = {"cursor": 0, "backoff": 0}   # وين وقف الفحص لو ياهو حظر، وكم يستنى


def scan_news(tickers, already_sent):
    hits, done, blocked = 0, 0, False
    if not tickers:
        return
    now = pd.Timestamp.now(tz="UTC")
    oldest = now - pd.Timedelta(minutes=NEWS_MAX_AGE_MIN)
    start = _news_state["cursor"] % len(tickers)
    order = tickers[start:] + tickers[:start]     # يكمل من حيث وقف آخر مرة
    fails_total = _YFNoise.news_fail
    with ThreadPoolExecutor(max_workers=NEWS_WORKERS) as pool:
        for i in range(0, len(order), NEWS_CHUNK):
            chunk = order[i:i + NEWS_CHUNK]
            fails_before = _YFNoise.news_fail
            for t, items in pool.map(fetch_news, chunk):
                for n in items:
                    if not n["title"] or n["time"] is None or n["time"] < oldest:
                        continue
                    key = f"{t}-{n['id']}"
                    if key in already_sent:
                        continue
                    already_sent.add(key)
                    _append_line(NEWS_SENT_FILE, key)
                    kind, category = news_classify(n["title"])
                    if NEWS_ONLY_POSITIVE and kind != "positive":
                        continue                  # سلبي أو محايد = نتجاهله
                    hits += 1
                    title = (translate_ar(n["title"]) if NEWS_TRANSLATE else None) or n["title"]
                    label = {"positive": "🟢 إيجابي", "negative": "🔴 سلبي"}.get(kind, "⚪ محايد")
                    local_time = n["time"].tz_convert(LOCAL_TZ)
                    send_telegram(
                        f"📰 خبر {label}" + (f" - {category}" if category else "") + "\n"
                        f"السهم: {t}\n"
                        f"الخبر: {title}\n"
                        f"المصدر: {n['source']}\n"
                        f"الوقت: {local_time:%H:%M} (توقيتك)\n"
                        f"{n['link']}"
                    )
            if _YFNoise.news_fail - fails_before > len(chunk) // 2:
                blocked = True                    # أكثر من نص الدفعة فشل = ياهو حاظرنا
                break
            done += len(chunk)
            time.sleep(NEWS_CHUNK_PAUSE_SEC)
    failed = _YFNoise.news_fail - fails_total
    if blocked:
        _news_state["cursor"] = (start + done) % len(tickers)
        _news_state["backoff"] = min(max(_news_state["backoff"] * 2, NEWS_EVERY_MIN),
                                     NEWS_MAX_BACKOFF_MIN)
        log(f"[{datetime.now():%H:%M}] الأخبار: ياهو حاظر مؤقتاً - فحصت {done} من {len(tickers)}، "
            f"أرجع بعد {NEWS_EVERY_MIN + _news_state['backoff']} دقيقة وأكمل من حيث وقفت")
    else:
        _news_state["cursor"] = 0
        _news_state["backoff"] = 0
    free_memory()
    log(f"[{datetime.now():%H:%M}] الأخبار: خلص الفحص - {hits} خبر جديد"
        + (f" ({failed} سهم ما رجع أخباره)" if failed else ""))


# ================== (3) نماذج الفريم اليومي ==================
def raw_pivots(hi, lo, n):
    """كل القمم والقيعان (قبل الترتيب المتناوب)."""
    top = pd.Series(hi).rolling(2 * n + 1, center=True).max().values
    bot = pd.Series(lo).rolling(2 * n + 1, center=True).min().values
    pts = []
    for i in range(n, len(hi) - n):
        if hi[i] == top[i]:
            pts.append((i, "H", hi[i]))
        if lo[i] == bot[i]:
            pts.append((i, "L", lo[i]))
    pts.sort(key=lambda x: (x[0], x[1] == "L"))
    return pts


def pivots_until(raw, t, n):
    """القمم والقيعان اللي كانت مؤكدة يوم t (يعني كأننا واقفين في ذاك اليوم)، متناوبة."""
    return _alternate([p for p in raw if p[0] <= t - n])


def find_pivots(hi, lo, n):
    """القمم والقيعان المؤكدة، متناوبة (قمة، قاع، قمة ...)."""
    return _alternate(raw_pivots(hi, lo, n))


def _alternate(pts):
    out = []
    for p in pts:
        if out and out[-1][1] == p[1]:
            # نفس النوع ورا بعض: نخلي الأقوى
            if (p[1] == "H" and p[2] >= out[-1][2]) or (p[1] == "L" and p[2] <= out[-1][2]):
                out[-1] = p
        else:
            out.append(p)
    return out


def _double_bottom(hi, lo, cl, t=None, raw=None):
    """قاع مزدوج (W) واخترق خط العنق في الشمعة t (الافتراضي آخر شمعة). يشتغل بالمقلوب للقمة المزدوجة."""
    t = len(cl) - 1 if t is None else t
    raw = raw_pivots(hi, lo, PIVOT_BARS) if raw is None else raw
    piv = [p for p in pivots_until(raw, t, PIVOT_BARS) if p[0] < t]
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


def _inv_head_shoulders(hi, lo, cl, t=None, raw=None):
    """رأس وكتفين مقلوب واخترق خط العنق في الشمعة t (الافتراضي آخر شمعة). يشتغل بالمقلوب للعادي."""
    t = len(cl) - 1 if t is None else t
    raw = raw_pivots(hi, lo, PIVOT_BARS) if raw is None else raw
    piv = [p for p in pivots_until(raw, t, PIVOT_BARS) if p[0] < t]
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


DAILY_PATTERNS = [
    # (مفعّل، الاسم، الكاشف، بالمقلوب؟)
    ("W", "🟢 قاع مزدوج (W)", _double_bottom, False),
    ("M", "🔴 قمة مزدوجة (M)", _double_bottom, True),
    ("IHS", "🟢 رأس وكتفين مقلوب", _inv_head_shoulders, False),
    ("HS", "🔴 رأس وكتفين", _inv_head_shoulders, True),
]


def _pattern_enabled(code):
    return {"W": ENABLE_DOUBLE_BOTTOM, "M": ENABLE_DOUBLE_TOP,
            "IHS": ENABLE_INV_HS, "HS": ENABLE_HS}[code]


def check_daily_patterns(df, lookback=None):
    """النماذج اللي اخترقت/كسرت خط العنق خلال آخر lookback شمعة يومية.
    يرجع قائمة: (الرمز المختصر للنموذج، الاسم، رقم شمعة الاختراق، خط العنق)."""
    lookback = DAILY_LOOKBACK_DAYS if lookback is None else lookback
    df = df.dropna(subset=["High", "Low", "Close"])
    if len(df) < 40:
        return []
    hi, lo, cl = (df[k].astype(float).values for k in ("High", "Low", "Close"))
    arrays = {False: (hi, lo, cl), True: (-lo, -hi, -cl)}
    raws = {flip: raw_pivots(a[0], a[1], PIVOT_BARS) for flip, a in arrays.items()}
    found = []
    for code, name, detect, flip in DAILY_PATTERNS:
        if not _pattern_enabled(code):
            continue
        h, l, c = arrays[flip]
        for t in range(max(len(c) - lookback, 40), len(c)):
            r = detect(h, l, c, t=t, raw=raws[flip])
            if r:
                neck = -r["neck"] if flip else r["neck"]
                found.append((code, name, t, neck))
    return found


def scan_daily(tickers, already_sent):
    """يفحص النماذج ويجمع الجديد منها في رسايل (بدل رسالة لكل سهم)."""
    new = {}   # الاسم -> [سطور]
    for t, df in download_batches(tickers, 200, period="1y", interval="1d", prepost=False):
        try:
            last = float(df["Close"].iloc[-1])
            for code, name, i, neck in check_daily_patterns(df):
                day = pd.Timestamp(df.index[i]).strftime("%Y-%m-%d")
                key = f"{t}-{code}-{day}"
                if key in already_sent:
                    continue
                already_sent.add(key)
                _append_line(DAILY_SENT_FILE, key)
                chg = (last / neck - 1) * 100
                new.setdefault(name, []).append(
                    (day, f"• {t} | الاختراق: {day} | خط العنق: {neck:.2f} | "
                          f"السعر الحين: {last:.2f} ({chg:+.1f}%)"))
        except Exception as e:
            log(f"{t}: خطأ يومي - {e}")
    hits = 0
    for name, rows in new.items():
        rows.sort(reverse=True)                   # الأحدث فوق
        hits += len(rows)
        for i in range(0, len(rows), 25):         # كل رسالة 25 سهم بالكثير
            part = rows[i:i + 25]
            send_telegram(f"{name} - فريم يومي (آخر {DAILY_LOOKBACK_DAYS} يوم تداول)\n"
                          + "\n".join(r[1] for r in part))
            time.sleep(3)
    free_memory()
    log(f"[{datetime.now():%H:%M}] اليومي: خلص الفحص - {hits} تنبيه جديد")


def regular_session_open():
    now = pd.Timestamp.now(tz=NY)
    if now.weekday() >= 5:
        return False
    return now.replace(hour=9, minute=30) <= now <= now.replace(hour=16, minute=10)


# ================== (4) الشورت صفر ==================
def _load_set(path):
    """يقرا ملف المرسل، ويخليه آخر SENT_KEEP_LINES سطر بس عشان ما يكبر للأبد."""
    try:
        with open(path, encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return set()
    if len(lines) > SENT_KEEP_LINES:
        lines = lines[-SENT_KEEP_LINES:]
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
        except Exception:
            pass
    return set(lines)


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
    free_memory()
    log(f"[{datetime.now():%H:%M}] الشورت: خلص الفحص - {hits} تنبيه جديد")


# ================== (5) الزخم ==================
_float_cache = {}   # الرمز -> (اليوم، الفري فلوت، إغلاق أمس)


def fetch_float(t):
    """الفري فلوت وإغلاق أمس من ياهو (ينحفظ لباقي اليوم)."""
    import yfinance as yf
    today = pd.Timestamp.now(tz=NY).date()
    got = _float_cache.get(t)
    if got and got[0] == today:
        return got[1], got[2]
    fl, prev = None, None
    try:
        info = yf.Ticker(t).info or {}
        fl = info.get("floatShares")
        prev = info.get("regularMarketPreviousClose") or info.get("previousClose")
    except Exception:
        pass
    _float_cache[t] = (today, fl, prev)
    return fl, prev


def momentum_hours(now=None):
    """4 الفجر - 8 بالليل نيويورك، أيام الأسبوع."""
    now = now or pd.Timestamp.now(tz=NY)
    m = now.hour * 60 + now.minute
    return now.weekday() < 5 and 4 * 60 <= m <= 20 * 60


def _fmt_shares(x):
    if x is None:
        return "غير معروف"
    x = float(x)
    return f"{x / 1e6:.2f} مليون" if x >= 1e6 else f"{x / 1e3:.0f} ألف"


def scan_momentum(tickers, last_alert):
    hits = 0
    now = pd.Timestamp.now(tz=NY)
    since = now - pd.Timedelta(minutes=MOMENTUM_WINDOW_MIN)
    for t, df in download_batches(tickers, 200, period="1d", interval="5m", prepost=True):
        try:
            df = to_ny(df)
            price = float(df["Close"].iloc[-1])
            if not (MOMENTUM_MIN_PRICE <= price <= MOMENTUM_MAX_PRICE):
                continue
            recent = df[df.index >= since]
            vol = float(recent["Volume"].sum()) if not recent.empty else 0.0
            if vol < MOMENTUM_MIN_VOLUME:
                continue
            prev_alert = last_alert.get(t)
            if prev_alert is not None and now - prev_alert < pd.Timedelta(minutes=MOMENTUM_REALERT_MIN):
                continue
            fl, prev_close = fetch_float(t)
            if fl is None:
                if not MOMENTUM_SEND_UNKNOWN_FLOAT:
                    continue
            elif not (MOMENTUM_MIN_FLOAT <= fl <= MOMENTUM_MAX_FLOAT):
                continue
            last_alert[t] = now
            hits += 1
            day_vol = float(df[df.index.date == now.date()]["Volume"].sum())
            chg = f" ({(price / prev_close - 1) * 100:+.1f}% عن إغلاق أمس)" if prev_close else ""
            send_telegram(
                f"🚀 زخم - حجم تداول مفاجئ\n"
                f"السهم: {t}\n"
                f"السعر: {price:.2f}{chg}\n"
                f"الحجم آخر نص ساعة: {_fmt_shares(vol)} سهم\n"
                f"الحجم اليوم كله: {_fmt_shares(day_vol)} سهم\n"
                f"الفري فلوت: {_fmt_shares(fl)}\n"
                f"الوقت: {now.tz_convert(LOCAL_TZ):%H:%M} (توقيتك)"
            )
        except Exception as e:
            log(f"{t}: خطأ زخم - {e}")
    free_memory()
    log(f"[{datetime.now():%H:%M}] الزخم: خلص الفحص - {hits} تنبيه جديد")


# ================== التشغيل ==================
def main():
    if "--test" in sys.argv:
        self_test()
        return
    once = "--once" in sys.argv
    _load_chats()
    discover_groups()
    log(f"التنبيهات بتروح لـ {len(CHATS)} محادثة: {', '.join(CHATS) or 'ولا وحدة'}")

    gap_tickers, gap_day, gap_last = [], None, None
    log("الجاب: " + ("24 ساعة (مع الجلسة الليلية من Tiingo)" if GAP_OVERNIGHT else
                     "الجلسة الممتدة 4 الفجر - 8 بالليل نيويورك (ياهو مجاناً)" if GAP_EXTENDED else
                     "الجلسة الرسمية بس"))
    was_open = None
    gap_sent = _load_set(GAP_SENT_FILE)
    news_tickers, news_day, news_last = [], None, 0.0
    news_sent = _load_set(NEWS_SENT_FILE)
    daily_tickers, daily_day, daily_last = [], None, 0.0
    daily_sent = _load_set(DAILY_SENT_FILE)
    momentum_tickers, momentum_day, momentum_last = [], None, 0.0
    momentum_alerts = {}
    short_day = None
    short_sent = _load_set(SHORT_SENT_FILE)

    while True:
        discover_groups()
        # (1) الجاب - بعد إغلاق كل شمعة بدقيقة
        now_ny = pd.Timestamp.now(tz=NY)
        slot = gap_scan_due(now_ny, gap_last)
        if ENABLE_GAP and (once or (slot is not None and us_market_open(now_ny))):
            gap_last = slot or now_ny
            today = pd.Timestamp.now(tz=NY).date()
            if gap_day != today or not gap_tickers:
                gap_tickers = get_nasdaq_midcap_plus()
                gap_day = today
                log(f"الجاب: {len(gap_tickers)} سهم ناسداك قيمتها السوقية {MIN_MARKET_CAP/1e9:.0f} مليار وفوق")
            scan_gap(gap_tickers, gap_sent)

        # (2) الأخبار - 24 ساعة
        if ENABLE_NEWS and time.time() - news_last >= (NEWS_EVERY_MIN + _news_state["backoff"]) * 60:
            today = pd.Timestamp.now(tz=NY).date()
            if news_day != today or not news_tickers:
                news_tickers = build_news_universe()
                news_day = today
            scan_news(news_tickers, news_sent)
            news_last = time.time()

        # (3) النماذج اليومية - وقت السوق الرسمي، كل نص ساعة
        if ENABLE_DAILY and (regular_session_open() or once or daily_last == 0.0) \
                and time.time() - daily_last >= DAILY_EVERY_MIN * 60:
            today = pd.Timestamp.now(tz=NY).date()
            if daily_day != today or not daily_tickers:
                daily_tickers = build_universe("اليومي", DAILY_MIN_PRICE, 100_000,
                                               DAILY_MIN_AVG_VOLUME, include_nyse=False)
                daily_day = today
            scan_daily(daily_tickers, daily_sent)
            daily_last = time.time()

        # (5) الزخم - كل 5 دقايق وقت التداول (مع ما قبل الفتح وبعد الإغلاق)
        if ENABLE_MOMENTUM and (momentum_hours() or once) \
                and time.time() - momentum_last >= MOMENTUM_EVERY_MIN * 60:
            today = pd.Timestamp.now(tz=NY).date()
            if momentum_day != today or not momentum_tickers:
                # نطاق أوسع شوي من 1-5$ لأن السعر يتحرك خلال اليوم، والفلتر الدقيق وقت الفحص
                momentum_tickers = build_universe("الزخم", MOMENTUM_MIN_PRICE * 0.5,
                                                  MOMENTUM_MAX_PRICE * 1.5, 0, include_nyse=False)
                momentum_day = today
            scan_momentum(momentum_tickers, momentum_alerts)
            momentum_last = time.time()

        # (4) الشورت صفر - مرة باليوم
        if ENABLE_SHORT:
            today = pd.Timestamp.now(tz=LOCAL_TZ).date()
            if short_day != today:
                short_tickers = build_universe("الشورت", SHORT_MIN_PRICE, SHORT_MAX_PRICE,
                                               SHORT_MIN_AVG_VOLUME, include_nyse=False)
                scan_short(short_tickers, short_sent)
                short_day = today

        is_open = us_market_open()
        if not is_open and was_open is not False:
            log(f"[{datetime.now():%H:%M}] السوق مسكر (الأخبار شغالة)، أنتظر...")
        was_open = is_open

        if once:
            break
        time.sleep(LOOP_SLEEP_SEC)


if __name__ == "__main__":
    main()
