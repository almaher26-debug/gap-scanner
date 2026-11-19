# ===== بوت الشورت (Short bot) =====
# فيه الأقسام الشغالة بس (الأقسام المطفية انحذفت من الملف - 9 نوفمبر 2026)
# 19 نوفمبر 2026: انحذف ماسح السيولة (2) والزخم (4د) والأخبار (7) وذروة البيع (13) ودلتا الحجم CVD (14)
# التشغيل على Railway: python short_bot.py  (المتغيرات: TELEGRAM_TOKEN + ALPACAAPIKEY + ALPACASECRETKEY)
"""
بوت التنبيهات - يشتغل على Railway ويرسل على تيليجرام
=====================================================

(1) الإنفيرجن IFVG - فريم ساعة و4 ساعات - قائمة المراقبة (WATCH_SYMBOLS)
    - 🟢 صعودي: قاع الشمعة الأولى فوق قمة الثالثة (جاب)، الثانية تغطيه، والرابعة تقفل فوق أعلى الجاب
    - 🔴 هبوطي: نفس الشي بالعكس، والرابعة تقفل تحت أسفل الجاب | لون الشموع ما يهم
    - الجلسة الممتدة بدون الليلي (4 الفجر - 8 بالليل نيويورك)، شموع 4 ساعات: 4-8، 8-12، 12-4، 4-8
    - حجم الجاب: 50 سنت وفوق (ساعة) و1$ وفوق (4 ساعات)، والتنبيه بعد إغلاق الشمعة بدقيقة
    - ENABLE_IFVG = False يطفيه (أو ENABLE_IFVG_1H / ENABLE_IFVG_4H لكل فريم)

(4ج) الشورت صفر اللحظي - من Interactive Brokers (نفس ChartExchange)
    - الأسهم: من 1$ إلى 10$ وقيمتها السوقية من 1 إلى 100 مليون
    - تنبيه "🚫 الشورت صفر" لما المتاح للشورت يوصل صفر، مع حجم الشورت آخر 15 يوم (FINRA)
    - أقصى 64 تنبيه باليوم (BZ_MAX_PER_DAY) موزعة على 24 ساعة (BZ_SPREAD_24H)، وتنبيه واحد لكل سهم كل 7 أيام
    - قائمة أسبوعية كل أحد: 10 أسهم صار الشورت عندها صفر خلال آخر 7 أيام
    - ENABLE_BORROW_ZERO = False يطفيه

(4ج-2) نزول الشورت المتاح - نفس مصدر وأسهم (4ج)
    - تنبيه "📉 نزول الشورت المتاح" لما المتاح ينزل أكثر من 90% عن أعلى رقم خلال آخر 30 يوم (وما وصل صفر)
    - يشترك مع (4ج) بنفس الحد: 64 تنبيه باليوم للقسمين مع بعض، موزعة على 24 ساعة، وتنبيه واحد لكل سهم كل 7 أيام
    - BZ_DROP_ALERTS = False يطفيه

(4ب) التجزئة العكسية - أسهم ناسداك
    - كل يوم سوق (بعد 10 الصبح نيويورك): الأسهم اللي سوت تجزئة عكسية جديدة بس
    - كل جمعة: قائمة بتجزئات آخر 7 أيام
    - ENABLE_RSPLIT_SHORT = False يطفيه

(6) كشف خوارزميات التقطيع - من ألباكا
    - الأسهم: أسهم ناسداك اللي سعرها من 1$ إلى 15$ وسوت تجزئة عكسية خلال آخر 3 شهور
    - يدور على صفقات صغيرة (10 أسهم وأقل) بنفس الحجم بالضبط، مثل 1، 1، 1، 1...
    - تنبيه لو تكررت 300 مرة أو أكثر خلال 5 دقايق، وقوي عند 600
    - يقدّر هل غالبها شراء ولا بيع من اتجاه السعر (تقريبي)
    - البيانات من كل البورصات (sip) لحظية بالباقة المدفوعة (ALGO_DELAY_MIN = 0)
    - ALGO_SMALL=0 في Railway يطفيه

(6ج) خوارزميات البني ستوك - نفس منطق (6) بالضبط
    - الأسهم: ناسداك من 1$ إلى 5$ وقيمتها السوقية 40 مليون دولار وتحت (أنشط 300)
    - تنبيه واحد بس لكل سهم كل 24 ساعة (ALGO_PENNY_ONCE_HOURS، ونفسه للقسم (6) ALGO_SMALL_ONCE_HOURS)
    - ALGO_PENNY=0 في Railway يطفيه

(6ب) خوارزميات الأسهم الكبيرة - قائمة المراقبة (WATCH_SYMBOLS) - من ألباكا
    - 300 صفقة أو أكثر ورا بعض بحجم سهم واحد بالضبط، وما بينها ولا صفقة بحجم ثاني، والفاصل 5 ثواني أو أقل
    - ينبه بس لو "شراء كامل" أو "بيع كامل" (الجهة وحدة 90% وفوق) - وقت السوق الرسمي بس
    - ALGO_BIG=0 في Railway يطفيه (أو ALGO_BIG_SYMBOLS لقائمة ثانية)

(6د) الآيس بيرغ - نفس أسهم (6ب) ونفس الصفقات (ما يزيد طلبات على ألباكا)
    - 500 صفقة أو أكثر ورا بعض بنفس الحجم ونفس السعر بالضبط (من سهم إلى 10 أسهم)، والفاصل ثانيتين أو أقل
    - تحديث عند 1000 ثم 2000 ... | ALGO_ICE=0 في Railway يطفيه

(1ك-2) سحب سيولة دعم ومقاومة الأسبوع السابق - فريم 4 ساعات - قائمة المراقبة (WATCH_SYMBOLS)
    - الدعم: شمعة 4 ساعات ذيلها بس نزل تحت قاع الأسبوع السابق، وافتتاحها وإغلاقها فوقه → كول
    - المقاومة: ذيلها بس طلع فوق قمة الأسبوع السابق، وافتتاحها وإغلاقها تحتها → بوت
    - شموع 4 ساعات بدون الجلسة الليلية (4-8 بري، 8-12، 12-4، 4-8 أفتر نيويورك)
    - تنبيه واحد لكل سهم بالأسبوع لكل جهة، يفحص كل 5 دقايق
    - ENABLE_PWL_4H / ENABLE_PWH_4H = False يطفي الدعم / المقاومة | PW4H_WICK_ONLY = False يرجع شرط الإغلاق بس

(1ي) سحب سيولة دعم ومقاومة اليوم السابق - فريم ساعة - قائمة المراقبة (WATCH_SYMBOLS)
    - الدعم: شمعة ساعة ذيلها بس نزل تحت قاع اليوم السابق، وافتتاحها وإغلاقها فوقه → كول
    - المقاومة: ذيلها بس طلع فوق قمة اليوم السابق، وافتتاحها وإغلاقها تحتها → بوت
    - قمة وقاع اليوم السابق من 4 الفجر لين 8 بالليل نيويورك (بدون الليلي)، تنبيه واحد لكل سهم باليوم لكل جهة
    - ENABLE_PDL_1H / ENABLE_PDH_1H = False يطفي الدعم / المقاومة

(1ي-2) قائمة سحب قمة أمس وقاع أمس - إغلاق يومي - قائمة المراقبة (WATCH_SYMBOLS)
    - الشمعة اليومية (9:30-4 نيويورك) ذيلها نزل تحت قاع أمس وقفلت فوقه → كول | طلع فوق قمة أمس وقفلت تحتها → بوت
    - قائمة وحدة مجمعة كل يوم سوق 4:20 العصر نيويورك (12:20 بالليل الرياض بالشتاء)
    - وأول ما يشتغل البوت: قائمة آخر شمعة يومية مقفلة (مرة وحدة لكل PD1D_START_ID)
    - ENABLE_PD1D = False يطفيه | python short_bot.py --pd1dnow [--send] تجربة حقيقية

(11) سحب قمة الجمعة يوم الاثنين ثم سحب دعم الأسبوع السابق (فريم 4 ساعات) → كول
    - الاثنين: السعر يسحب قمة الجمعة ويرجع يختبرها وما يخترقها
    - بعدها ينزل لقاع الأسبوع السابق ويسحب السيولة (ذيل تحت الدعم وإغلاق فوقه)
    - التنبيه: كول مع الأهداف والوقف وعقد كول مدته أسبوعين
    - الأسهم: قائمة المراقبة اللي سعرها 100$-400$ | ENABLE_FRIMON = False يطفيه

(12) سحب السيولة الأسبوعي - فريم 4 ساعات + العقد - قائمة المراقبة اللي سعرها 100$-350$
    - نفس شمعة (1ك-2): سحب دعم الأسبوع السابق → كول | سحب مقاومة الأسبوع السابق → بوت
    - تنبيه واحد بس لكل سهم بالأسبوع (أول سحب، دعم أو مقاومة)
    - العقد: أكثر من 10 أيام، حجم تداول فوق 500، عقود مفتوحة فوق 1000، دلتا فوق 0.1200
    - الأسهم برا 100$-350$ تكمل على (1ك-2) بدون عقد | ENABLE_WKOPT = False يطفيه

(15) تقرير القاما اليومي - قائمة GEX_SYMBOLS (فاضية = قائمة المراقبة) - من سلسلة عقود ياهو
    - كل يوم سوق 8:30 الصبح نيويورك (4:30 العصر الرياض بالشتاء)، رسالة مجمعة
    - لكل سهم: جدار الكول، جدار البوت، نقطة الانقلاب، صافي القاما، أكثر سترايك عقود مفتوحة، أكثر سترايك فوليوم
    - ENABLE_GEX_DAILY = False يطفيه | python short_bot.py --gexnow [--send] [NVDA ...] تجربة حقيقية

التشغيل:
  pip install yfinance pandas requests lxml matplotlib
  python short_bot.py               # يشتغل باستمرار
  python short_bot.py --once        # فحص مرة وحدة بس
  python short_bot.py --algotest    # يجرب كشف خوارزميات التقطيع (بدون نت)
  python short_bot.py --pwltest     # يجرب سحب الأسبوع السابق (بدون نت)
  python short_bot.py --pw4hnow [--send]   # سحب الأسبوع السابق 4 ساعات على بيانات حقيقية
  python short_bot.py --frimontest  # يجرب سحب الجمعة/الاثنين (بدون نت)
  python short_bot.py --wkopttest   # يجرب اختيار العقد للسحب الأسبوعي (بدون نت)
  python short_bot.py --ifvgtest    # يجرب الإنفيرجن (بدون نت)
"""

import gc
import io
import json
import logging
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import csv
import math
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from zoneinfo import ZoneInfo

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

# ---- الجلسات وبيانات الشموع (تستخدمها أقسام الشموع: سحب الأسبوع السابق 4 ساعات + سحب الجمعة/الاثنين) ----
GAP_EXTENDED = True              # يشمل ما قبل الفتح وبعد الإغلاق (4 الفجر - 8 بالليل نيويورك)

# الجلسة الليلية (8 بالليل - 4 الفجر نيويورك) = إعداد الـ24 ساعة في تريدنج فيو
# ياهو ما يعطيها، فتجي من Tiingo: حط المفتاح كمتغير TIINGO_TOKEN على Railway
TIINGO_TOKEN = os.environ.get("TIINGO_TOKEN", "")
GAP_OVERNIGHT = bool(TIINGO_TOKEN)   # يتفعل لحاله لو حطيت المفتاح

# ⭐ قائمتك الموحدة (قائمة المراقبة) - عليها سحب الأسبوع السابق 4 ساعات وسحب الجمعة/الاثنين
TEST_ON_START = True             # True = يرسل رسالة اختبار كل ما البوت يشتغل | False = بدون
ONE_LIST = False  # True = كل الأقسام على القائمة هذي | False = كل قسم يرجع لأسهمه القديمة
WATCH_SYMBOLS = [
    "NVDA", "CRM", "AVGO", "META", "TSLA", "SPCX", "AMD", "LITE", "FICO", "AAPL",
    "RKLB", "UNH", "MU", "LLY", "ADBE", "QCOM", "SHOP", "GOOGL", "MSFT", "MSTR",
    "AMZN", "DDOG", "ACN", "GEV", "LRCX", "PLTR", "OKTA", "ORCL", "INTC", "AAOI",
    "CRDO", "SNDK", "STX", "CRCL", "WDC", "SKHY", "NBIS", "CRWV", "CRWD", "MRVL",
    "ARM", "AMAT", "PANW", "SNOW", "NOW", "DELL", "FSLR", "ENPH", "VRT", "RIVN",
    "KLAC", "MCHP", "FTNT", "ADSK", "MDB", "CSCO", "CLS", "BE", "MOD", "TEM",
    "CELH", "CHWY", "CROX", "GRMN", "CTSH", "BBIO", "DOCS", "ADMA", "CTAS", "MSM",
    "SMH", "ABBV", "HAS", "KO", "LULU", "APH", "SNPS", "IBM", "ORLY", "HD",
    # إعلانات أرباح أسبوع 2 نوفمبر 2026 (الموجودة فوق ما تكررت)
    "AEHR", "APP", "DIBS", "TXG", "SMCI", "MRNA", "AMC", "NVTS", "KTOS", "CHKP",
    "COHR", "UBER", "NET", "VSH", "BMRN", "FSLY", "ANET", "CAVA", "EL", "CIFR",
    "PFE", "OKLO", "ETN", "ABNB", "NVO", "TEAM", "BKNG", "RIOT", "IREN", "U",
    "MP", "GFS", "FN", "MPC", "BXSL", "ALAB", "RUN", "BROS", "FISV",
    # باقي أسهم صورة الأرباح (أعمدة الأيام الخمسة)
    "NSSC", "ETR", "MAR", "PEG", "TSEM", "KRYS", "LIFE", "ON", "ROKU", "O",
    "CALX", "DT", "DOCN", "ET", "APO", "BNTX", "HL", "AMGN", "OUST", "CAR",
    "MCD", "CVS", "CAI", "CAH", "IOVA", "EOSE", "CORZ", "CI", "TAP", "UUUU",
    "CHTR", "WULF", "ELAN", "HUM", "DTI", "BLMN", "PAA", "UAA",
    # أُضيفت 6 نوفمبر 2026
    "TSM", "BABA",
    # أُضيفت 7 نوفمبر 2026
    "AKAM", "BA",
    # صناديق
    "QQQ", "SPY",
    # مؤشرات (من ياهو): سباكس S&P 500 + ناسداك 100
    "^GSPC", "^NDX",
]
# المؤشرات ما لها صفقات ولا بيانات في ألباكا، فتنشال من أقسام ألباكا (الخوارزميات، الزخم، الجلسة الليلية)
INDEX_SYMBOLS = {"^GSPC", "^NDX"}
INDEX_NAMES = {"^GSPC": "سباكس S&P 500", "^NDX": "ناسداك 100"}


def stocks_only(syms):
    """القائمة بدون المؤشرات - للأقسام اللي تعتمد على ألباكا."""
    return [x for x in syms if x not in INDEX_SYMBOLS]


GAP_BASE_MIN = 15                # البيانات تنحمّل بشموع 15 دقيقة، وكل الفريمات تنبني منها
GAP_SCAN_AFTER_CLOSE_MIN = (1, 5, 12)   # يفحص بعد الإغلاق بكذا دقيقة (الأولى هي الأساسية)
GAP_SENT_FILE = os.path.join(os.environ.get("RAILWAY_VOLUME_MOUNT_PATH", "."), "gap_sent.txt")   # في /data عشان ما يعيد نفس التنبيه بعد إعادة التشغيل أو الرفع

# ---- (4ج) الشورت صفر اللحظي: الأسهم المتاحة للشورت وصلت صفر (Interactive Brokers كل 15 دقيقة) ----
ENABLE_BORROW_ZERO = True  # True = شغال | False = مطفي
BZ_ZERO_ALERTS = False           # تنبيه "🚫 الشورت صفر" اللحظي: False = مطفي | True = يرجع
BZ_SPREAD_24H = True             # True = التنبيهات تنقسم على 24 ساعة (وحدة كل 24÷BZ_MAX_PER_DAY = 22.5 دقيقة) | False = ترسل فوراً
BZ_MAX_PER_DAY = 64              # أقصى عدد تنبيهات الشورت صفر باليوم | 0 = بدون حد
BZ_COOLDOWN_DAYS = 7             # تنبيه واحد لكل سهم كل كذا يوم | 0 = بدون حد
BZ_MIN_PRICE = 1                 # أقل سعر: الأسهم فوق دولار بس (0 = بدون حد)
BZ_MAX_PRICE = 10                # أعلى سعر (0 = بدون حد)
BZ_MIN_MARKET_CAP = 1_000_000    # أقل قيمة سوقية: 1 مليون
BZ_MAX_MARKET_CAP = 100_000_000  # أعلى قيمة سوقية: 100 مليون (0 = بدون حد)
BZ_FTP_HOSTS = ("ftp2.interactivebrokers.com", "ftp3.interactivebrokers.com")   # ftp2 أول (ftp3 يعلّق)
BZ_FTP_TIMEOUT = 10              # ثواني لكل محاولة (كانت 25 وتضيّع دقيقة كاملة)
BZ_EVERY_MIN = 2                 # كل كم دقيقة يفحص (كانت 15) — يمسك تحديث IBKR خلال دقيقتين
BZ_WARN_AFTER_MIN = 60           # ينبهك لو ملف IBKR ما تحمّل من كذا دقيقة
BZ_UNIVERSE_EVERY_MIN = 60       # كل كم دقيقة يحدث قائمة البني ستوك (السعر والقيمة السوقية)
# ---- (4ج-2) نزول الشورت المتاح (نفس الطابور والحد اليومي 64 مع الشورت صفر) ----
BZ_DROP_ALERTS = False           # True = شغال | False = مطفي
BZ_DROP_PCT = 90                 # ينبه لما المتاح ينزل أكثر من كذا % عن أعلى رقم بالفترة
BZ_DROP_DAYS = 30                # الفترة: آخر شهر
BZ_DROP_MIN_HIGH = 10_000        # أعلى رقم بالفترة لازم يكون كذا سهم وفوق (يشيل الأسهم اللي متاحها أصلاً قليل)
BZ_SHORT_DAYS = 15               # كم يوم من حجم الشورت يكتب في التنبيه
BZ_STATE_FILE = os.path.join(os.environ.get("RAILWAY_VOLUME_MOUNT_PATH", "."), "borrow_state.json")   # يُحفظ في /data عشان ما يضيع مع كل رفع

# ---- قائمة الشورت صفر الأسبوعية (كل يوم أحد) ----
#   10 أسهم صار المتاح للشورت عندها صفر خلال آخر 7 أيام (الأحدث أول)
BZ_WEEKLY_ZERO = True            # True = شغالة | False = مطفية
BZ_WEEKLY_N = 10                 # كم سهم بالقائمة
BZ_WEEKLY_DAYS = 7               # الفترة: آخر أسبوع
BZ_WEEKLY_DAY = 6                # يوم الإرسال: 6 = الأحد (0 = الاثنين)
BZ_WEEKLY_HOUR = 0               # يرسلها من هالساعة وطالع (توقيتك)
BZ_WEEKLY_MAX_RISE = 30          # يستبعد السهم لو ارتفع أكثر من كذا % خلال الأسبوع (0 = بدون فلتر)

# ---- (1ك-2) سحب سيولة دعم ومقاومة الأسبوع السابق - فريم 4 ساعات - قائمة المراقبة ----
PWL_EVERY_MIN = 5                # كل كم دقيقة يفحص وقت السوق
PWL_MAX_ALERT_DELAY_MIN = 30     # ما ينبه على شمعة قفلت من أكثر من كذا دقيقة
#   الدعم: شمعة 4 ساعات (من هالأسبوع) ذيلها نزل تحت قاع الأسبوع السابق وجسمها كامل فوقه
#   المقاومة: شمعة 4 ساعات ذيلها طلع فوق قمة الأسبوع السابق وجسمها كامل تحتها
#   الشموع بدون الجلسة الليلية: 4-8 بري، 8-12، 12-4 ماركت، 4-8 أفتر (نيويورك)
#   قمة وقاع الأسبوع السابق محسوبة من بري + ماركت + أفتر (4 الفجر - 8 بالليل) بدون الليلي
#   تنبيه واحد لكل سهم بالأسبوع لكل جهة (دعم / مقاومة)
ENABLE_PWL_4H = True  # الدعم: True = شغال | False = مطفي
ENABLE_PWH_4H = True  # المقاومة: True = شغال | False = مطفي
PW4H_WICK_ONLY = True  # True = الذيل بس يكسر المستوى، الافتتاح والإغلاق كلهم بجهته | False = الإغلاق بس

# ---- (1ي) سحب سيولة دعم ومقاومة اليوم السابق - فريم ساعة - قائمة المراقبة ----
#   الدعم: شمعة ساعة (من اليوم) ذيلها بس نزل تحت قاع اليوم السابق، وافتتاحها وإغلاقها فوقه → كول
#   المقاومة: شمعة ساعة ذيلها بس طلع فوق قمة اليوم السابق، وافتتاحها وإغلاقها تحتها → بوت
#   قمة وقاع اليوم السابق من بري + ماركت + أفتر (4 الفجر - 8 بالليل نيويورك) بدون الليلي
#   شموع الساعة من 4 الفجر لين 8 بالليل | تنبيه واحد لكل سهم باليوم لكل جهة | يفحص مع (1ك-2) كل 5 دقايق
ENABLE_PDL_1H = True   # الدعم: True = شغال | False = مطفي
ENABLE_PDH_1H = True   # المقاومة: True = شغال | False = مطفي
PD1H_WICK_ONLY = True  # True = الذيل بس يكسر المستوى (الافتتاح والإغلاق بجهته) | False = الإغلاق بس

# ---- (1ي-2) قائمة سحب قمة أمس وقاع أمس - إغلاق يومي - قائمة المراقبة ----
#   الشمعة اليومية (الجلسة الرسمية 9:30-4 نيويورك، نفس تريدنج فيو):
#   🟢 سحب قاع أمس: ذيلها نزل تحت قاع أمس وقفلت فوقه → كول (الهدف قمة أمس)
#   🔴 سحب قمة أمس: ذيلها طلع فوق قمة أمس وقفلت تحتها → بوت (الهدف قاع أمس)
#   قائمة وحدة مجمعة كل يوم سوق بعد الإغلاق، + قائمة أول ما يشتغل البوت (آخر شمعة يومية مقفلة)
ENABLE_PD1D = True                # True = شغال | False = مطفي
PD1D_LOW = True                   # سحب قاع أمس (كول)
PD1D_HIGH = True                  # سحب قمة أمس (بوت)
PD1D_WICK_ONLY = True             # True = الافتتاح كمان بجهة المستوى (الذيل بس اللي كسر) | False = الإغلاق بس
PD1D_SCAN_AFTER_NY = (16, 20)     # يرسل القائمة بعد كذا نيويورك (= 12:20 بالليل الرياض بالشتاء)
PD1D_SCAN_UNTIL_NY = (20, 0)      # لو بيانات ياهو تأخرت يعيد المحاولة كل 10 دقايق لين كذا
PD1D_RETRY_MIN = 10
PD1D_START_LIST = True            # قائمة أول ما يشتغل البوت (مرة وحدة لكل رقم PD1D_START_ID)
PD1D_START_ID = "1"               # غيّر الرقم لو تبيها تنرسل مرة ثانية بعد الرفع الجاي
PD1D_STATE = os.path.join(os.environ.get("RAILWAY_VOLUME_MOUNT_PATH", "."), "pd1d_state.txt")

# ---- (1) الإنفيرجن IFVG - فريم ساعة و4 ساعات - قائمة المراقبة (WATCH_SYMBOLS) ----
#   نفس نموذج gap_scanner: ثلاث شموع بين ذيل الأولى والثالثة جاب، الثانية تغطي الجاب كامل،
#   والرابعة تقفل وراه (لون الشموع ما يهم)
#   🟢 صعودي: قاع الأولى فوق قمة الثالثة، والرابعة تقفل فوق أعلى الجاب (قاع الأولى)
#   🔴 هبوطي: قمة الأولى تحت قاع الثالثة، والرابعة تقفل تحت أسفل الجاب (قمة الأولى)
#   الجلسة الممتدة بدون الليلي (4 الفجر - 8 بالليل نيويورك)، شموع 4 ساعات: 4-8، 8-12، 12-4، 4-8
#   يفحص بعد إغلاق كل ساعة بدقيقة (ويعيد بعد 5 و12 دقيقة لو بيانات ياهو تأخرت)
ENABLE_IFVG = True               # True = شغال | False = مطفي (الفريمين)
ENABLE_IFVG_1H = True            # فريم ساعة
ENABLE_IFVG_4H = True            # فريم 4 ساعات
IFVG_1H_MIN_SIZE = 0.50          # أقل حجم للجاب - فريم ساعة (دولار)
IFVG_4H_MIN_SIZE = 1.00          # أقل حجم للجاب - فريم 4 ساعات (دولار)
IFVG_MIN_PRICE = 0               # أقل سعر سهم (0 = بدون شرط)
IFVG_REQUIRE_MIDDLE_COVER = True # الشمعة الثانية لازم تغطي الجاب كامل
IFVG_MAX_ALERT_DELAY_MIN = 30    # ما ينبه على شمعة قفلت من أكثر من كذا دقيقة
IFVG_SHOW_CANDLES = True         # يكتب الشموع الأربع (وقت، أعلى، أقل) في التنبيه
# ---- (1-24) الإنفيرجن على 24 ساعة (كان ملف ifvg_24h_scanner.py، الحين هنا) ----
#   شموع ساعة و4 ساعات من 24 ساعة كاملة، اليوم يبدأ 8 بالليل نيويورك (تريدنج فيو مع "خلال الليل")
#   النهار (4 الفجر - 8 بالليل) من ألباكا SIP، والليل (8 بالليل - 4 الفجر) من ألباكا BOATS
ENABLE_IFVG24 = True             # True = شغال | False = مطفي
ENABLE_IFVG24_1H = True          # فريم ساعة (24 ساعة)
ENABLE_IFVG24_4H = True          # فريم 4 ساعات (24 ساعة)
IFVG24_GAMMA = True              # يضيف تمركز القاما للتنبيه | False = بدون
IFVG24_1H_MIN_SIZE = 0.20        # أقل حجم للجاب - فريم ساعة (دولار)
IFVG24_4H_MIN_SIZE = 0.20        # أقل حجم للجاب - فريم 4 ساعات (دولار)
IFVG24_STRICT_4H = os.environ.get("GAP4H_STRICT", "0") != "0"   # شروط إضافية للـ 4 ساعات (متراصة + لون الرابعة)
IFVG24_DAY_FEED = os.environ.get("DAY_FEED", "sip").lower()
IFVG24_NIGHT_FEED = os.environ.get("NIGHT_FEED", "boats").lower()
IFVG24_LOOKBACK_DAYS = 5         # كم يوم يرجع بالبيانات (يغطي الويكند)
IFVG24_SCAN_AFTER_MIN = (17, 20, 25)   # يفحص بعد بداية كل ساعة بكذا دقيقة (SIP متأخر 15 دقيقة)
IFVG24_MAX_ALERT_DELAY_MIN = 45  # ما ينبه على شمعة قفلت من أكثر من كذا دقيقة
IFVG24_SENT_FILE = os.path.join(os.environ.get("RAILWAY_VOLUME_MOUNT_PATH", "."), "ifvg24_sent.txt")

# ---- (12) سحب السيولة الأسبوعي (دعم ← كول | مقاومة ← بوت) + العقد - الأسهم من 100$ إلى 350$ ----
#   نفس شمعة السحب في (1ك-2)، بس الأسهم اللي سعرها داخل النطاق يجيها تنبيه واحد بالأسبوع (أول سحب، دعم أو مقاومة)
#   ومعه عقد بالشروط تحت. الأسهم برا النطاق تكمل على (1ك-2) مثل قبل.
ENABLE_WKOPT = False             # True = شغال | False = مطفي (كل الأسهم ترجع على (1ك-2) بدون عقد)
WKOPT_MIN_PRICE = 100            # سعر السهم من
WKOPT_MAX_PRICE = 350            # إلى
WKOPT_OPT_MIN_DTE = 10           # العقد أكثر من 10 أيام (يختار أقرب انتهاء بعدها)
WKOPT_OPT_MAX_DTE = 45           # أبعد انتهاء يدوّر فيه
WKOPT_OPT_MIN_VOLUME = 500       # حجم التداول في العقد فوق 500
WKOPT_OPT_MIN_OI = 1000          # العقود المفتوحة (الكمية غير إغلاق المركز) فوق 1000
WKOPT_OPT_MIN_DELTA = 0.12       # الدلتا فوق 0.1200 (للبوت: القيمة المطلقة)
WKOPT_REQUIRE_CONTRACT = True    # True = ما ينبه إلا لو لقى عقد بالشروط | False = ينبه حتى بدون عقد
# ---- تمركز القاما للعقود مع تنبيه سحب السيولة (1ك-2) و (12) ----
#   من سلسلة عقود ياهو (العقود المفتوحة + IV): قاما كل سترايك × العقود المفتوحة × 100 × السعر² × 1%
#   الكول موجب والبوت سالب. يطلع: جدار الكول، جدار البوت، أعلى السترايكات، صافي القاما، ونقطة الانقلاب
SWEEP_GAMMA = True               # True = يضيف تمركز القاما للتنبيه | False = بدون
IFVG_GAMMA = True                # يضيف تمركز القاما لتنبيهات الإنفيرجن (ساعة + 4 ساعات) | False = بدون
GAMMA_MAX_DTE = 30               # الانتهاءات اللي تدخل بالحساب: من اليوم إلى كذا يوم
GAMMA_MAX_EXPS = 4               # أقصى عدد انتهاءات (أقربها)
GAMMA_RANGE_PCT = 20             # السترايكات بس اللي داخل ±كذا % من السعر
GAMMA_TOP_N = 3                  # كم سترايك يكتب في "أعلى تمركز"
GAMMA_CHAIN_ALIAS = {"^GSPC": "^SPX"}   # ياهو ما يعطي عقود على ^GSPC، فتنجاب من ^SPX (نفس السترايكات)
SWEEP_CHART = True               # صورة شارت 4 ساعات مع تنبيه السحب (يحتاج matplotlib) | False = نص بس

# ---- (15) تقرير القاما اليومي - مراكز صناع السوق + أكثر سترايك عليه سيولة ----
#   مرة كل يوم سوق قبل الافتتاح (العقود المفتوحة تتحدث مرة باليوم من OCC، فقبل الافتتاح = أرقام إغلاق أمس)
#   لكل سهم: جدار الكول، جدار البوت، نقطة الانقلاب، صافي القاما، أكثر سترايك عقود مفتوحة، وأكثر سترايك فوليوم بآخر جلسة
ENABLE_GEX_DAILY = True          # True = شغال | False = مطفي
GEX_DAILY_AT_NY = (8, 30)        # يرسل من 8:30 الصبح نيويورك = 4:30 العصر الرياض (الشتاء) / 3:30 (الصيف)
GEX_DAILY_UNTIL_NY = (16, 0)     # لو البوت اشتغل بعد كذا وما انرسل، ينتظر لليوم الجاي
# قائمة التقرير: فاضية = نفس قائمة المراقبة (WATCH_SYMBOLS)، أو حط رموز هنا، أو متغير GEX_SYMBOLS في Railway (بينها فاصلة)
GEX_SYMBOLS = [s.strip().upper() for s in os.environ.get("GEX_SYMBOLS", "").split(",") if s.strip()] or [
    "NVDA", "CRM", "AVGO", "META", "TSLA", "SPCX", "AMD", "AAPL", "RKLB", "UNH",
    "MU", "LLY", "ADBE", "QCOM", "SHOP", "GOOGL", "MSFT", "MSTR", "AMZN", "DDOG",
    "PLTR", "OKTA", "ORCL", "INTC", "AAOI", "CRDO", "SNDK", "STX", "CRCL", "WDC",
    "SKHY", "NBIS", "CRWV", "CRWD", "MRVL", "ARM", "AMAT", "PANW", "SNOW", "NOW",
    "DELL", "BE", "SMH", "ABBV", "KO", "HD", "MRNA", "TSM", "BA",
    "QQQ", "SPY", "^GSPC", "^NDX",
]
GEX_DAILY_STATE = os.path.join(os.environ.get("RAILWAY_VOLUME_MOUNT_PATH", "."), "gex_daily.txt")
SWEEP_CHART_BARS = 30            # كم شمعة 4 ساعات تطلع بالصورة

# ---- حساب الدلتا وسعر العقد (يستخدمه سحب الجمعة/الاثنين) ----
PDR_OPT_RATE = 0.04              # الفائدة لحساب الدلتا لو المصدر ما أعطاها

# ---- (4ب) التجزئة العكسية ----
ENABLE_RSPLIT_SHORT = False  # قوائم التجزئة العكسية (مطفي)
RSPLIT_NEW_DAYS = 4                  # "جديد" = تجزئة صارت خلال آخر كذا يوم (يغطي الويكند) وما انرسلت قبل
RSPLIT_CHECK_AFTER_NY = 10           # الفحص اليومي بعد الساعة 10 الصبح نيويورك (عشان سعر الافتتاح يكون موجود)
RSPLIT_NEW_FILE = "rsplit_new.txt"       # التجزئات الجديدة اللي انرسلت
RSPLIT_WEEKLY = True                 # قائمة كل جمعة بتجزئات آخر 7 أيام
RSPLIT_STATE_FILE = "rsplit_state.txt"   # يحفظ آخر يوم/أسبوع انرسل عشان ما يتكرر

# ---- (6) كشف خوارزميات التنفيذ (أوامر متكررة بنفس الحجم) - من ألباكا ----
# يراقب الصفقات لحظياً (بورصة IEX المجانية) ويدور على صفقات ورا بعض بنفس الحجم بالضبط
# مثال: 1، 1، 1، 1، 1، 1 أو 4، 4، 4، 4، 4، 4 = غالباً خوارزمية تقسيم أو آيس بيرغ
ALPACA_KEY = (os.environ.get("ALPACAAPIKEY") or os.environ.get("ALPACA_API_KEY")
              or os.environ.get("APCA_API_KEY_ID", ""))
ALPACA_SECRET = (os.environ.get("ALPACASECRETKEY") or os.environ.get("ALPACA_SECRET_KEY")
                 or os.environ.get("APCA_API_SECRET_KEY", ""))
ENABLE_ALGO = bool(ALPACA_KEY and ALPACA_SECRET)  # يتفعل لحاله لو المفاتيح موجودة
# sip = كل البورصات (لحظي بالباقة المدفوعة، متأخر 15 دقيقة بالمجانية) | iex = بورصة وحدة صغيرة
# الأسهم الصغيرة تقريباً ما تتداول على IEX، فـ sip أدق بكثير لهالنوع
ALGO_FEED = os.environ.get("ALGO_FEED", "sip").lower()
# باقة ألباكا المدفوعة (Algo Trader Plus) = sip لحظي، فالتأخير صفر
# لو رجعت للباقة المجانية حط في Railway متغير ALGO_DELAY_MIN = 16
ALGO_DELAY_MIN = int(os.environ.get("ALGO_DELAY_MIN", "0"))
# الأسهم: تلقائياً أسهم ناسداك اللي سعرها من 1$ إلى 15$ وسوت تجزئة عكسية خلال آخر 3 شهور
# ولو تبي قائمة ثابتة حطها في Railway بمتغير ALGO_SYMBOLS (بينها فاصلة)
ALGO_SYMBOLS = [s.strip().upper() for s in os.environ.get("ALGO_SYMBOLS", "").split(",") if s.strip()]
ALGO_SMALL = os.environ.get("ALGO_SMALL", "1") != "0"   # 0 = يطفي هالقسم
ALGO_MIN_PRICE = 1                    # أقل سعر سهم
ALGO_MAX_PRICE = 15                   # أعلى سعر سهم
ALGO_MAX_MARKET_CAP = 0               # 0 = بدون شرط قيمة سوقية
ALGO_RSPLIT_DAYS = 92                 # لازم سوى تجزئة عكسية خلال آخر كذا يوم (3 شهور) - 0 = بدون شرط
ALGO_MIN_DAY_VOLUME = 50_000          # يشيل الأسهم الميتة (حجم اليوم)
ALGO_MAX_SYMBOLS = 300                # أقصى عدد أسهم يراقبها (الأنشط أول) - بالعادة أقل من كذا بكثير
ALGO_POLL_SEC = 15                    # كل كم ثانية يسحب الصفقات الجديدة
ALGO_MAX_SIZE = 10                    # الأحجام الصغيرة بس: صفقة حجمها 10 أسهم أو أقل (1، 1، 1...)
ALGO_WINDOW_MIN = 5                   # يعد الصفقات المتكررة خلال آخر كذا دقيقة
ALGO_MIN_STREAK = 300                 # تنبيه عند 300 صفقة بنفس الحجم
ALGO_STRONG_STREAK = 600              # تنبيه قوي عند 600 أو أكثر
ALGO_MIN_VALUE = float(os.environ.get("ALGO_MIN_VALUE", "25000"))   # أقل قيمة بالدولار لمجموع الصفقات المتكررة (0 = بدون شرط)
ALGO_SMALL_ONCE_HOURS = 24            # قسم التجزئة العكسية (1$-15$): تنبيه واحد لكل سهم كل كذا ساعة (0 = بدون حد)
ALGO_ONCE_FILE = "algo_once.txt"      # يحفظ وقت آخر تنبيه لكل سهم عشان ما يعيده لو البوت أعاد التشغيل
ALGO_REALERT_MIN = 15                 # ما يعيد نفس مستوى التنبيه لنفس السهم والحجم قبل كذا دقيقة

# ---- (6ج) خوارزميات البني ستوك: من 1$ إلى 5$ وقيمتها السوقية 40 مليون وتحت ----
# نفس منطق القسم (6) بالضبط: صفقات 10 أسهم وأقل بنفس الحجم، تنبيه 300 وقوي 600 خلال 5 دقايق
# السهم اللي داخل قائمة التجزئة العكسية (6) ما يتكرر هنا
ALGO_PENNY = False   # مطفي (True = يرجع)
ALGO_PENNY_ONCE_HOURS = 24            # تنبيه واحد بس لكل سهم، وبعدها يسكت عنه كذا ساعة (0 = بدون حد)
ALGO_PENNY_MIN_PRICE = 1
ALGO_PENNY_MAX_PRICE = 5
ALGO_PENNY_MAX_MARKET_CAP = 40_000_000
ALGO_PENNY_MAX_SYMBOLS = 300          # الأنشط أول


# ---- (6ب) خوارزميات الأسهم الكبيرة: صفقات متتالية بنفس الحجم ----
# أسهم ناسداك اللي قيمتها السوقية مليار دولار وفوق
# ينبه لما تجي 600 صفقة أو أكثر ورا بعض بنفس الحجم بالضبط، وما بينها ولا صفقة بحجم ثاني
# الأحجام الصغيرة بس: 10 أسهم وأقل (1، 1، 1 ... أو 5، 5، 5 ...)
ALGO_BIG = os.environ.get("ALGO_BIG", "1") != "0"      # 0 = يطفي هالقسم
ALGO_BIG_MIN_MARKET_CAP = 1_000_000_000   # مليار دولار وفوق
ALGO_BIG_MIN_STREAK = 300                 # أقل عدد صفقات متتالية بنفس الحجم
ALGO_BIG_MAX_SIZE = 1                     # حجم الصفقة: سهم واحد بس (1، 1، 1...)
ALGO_BIG_MAX_GAP_SEC = 5                  # لو مر أكثر من كذا ثانية بين صفقتين، تنقطع السلسلة
ALGO_BIG_MAX_SYMBOLS = int(os.environ.get("ALGO_BIG_MAX_SYMBOLS", "250"))   # الأنشط أول
ALGO_BIG_SYMBOLS = ([s.strip().upper() for s in os.environ.get("ALGO_BIG_SYMBOLS", "").split(",")
                     if s.strip()] or stocks_only(WATCH_SYMBOLS))   # الافتراضي: قائمة المراقبة (بدون المؤشرات)
ALGO_BIG_REGULAR_ONLY = True              # وقت السوق الرسمي بس (9:30 - 4 نيويورك)
ALGO_BIG_ONE_SIDE_PCT = 90                # "شراء كامل" أو "بيع كامل": الجهة وحدة 90% وفوق، وإلا ما ينبه
ALGO_BIG_POLL_SEC = 20                    # كل كم ثانية يسحب الصفقات الجديدة
ALGO_BIG_CHUNK = 20                       # كم سهم بكل طلب لألباكا (الكبيرة صفقاتها كثيرة)
ALGO_BIG_REALERT_MIN = 15                 # ما يعيد التنبيه لنفس السهم والحجم قبل كذا دقيقة

# ---- (6د) الآيس بيرغ: صفقات متتالية بنفس الحجم ونفس السعر بالضبط ----
# نفس أسهم (6ب) (ناسداك مليار وفوق) ونفس الصفقات اللي تنسحب لها، فما يزيد طلبات على ألباكا
# مثال: 1، 1، 1 ... (من سهم إلى 10 أسهم) كلها على نفس السعر ورا بعض، وما بينها ولا صفقة ثانية
ALGO_ICE = os.environ.get("ALGO_ICE", "1") != "0"      # 0 = يطفي هالقسم (يشتغل لو (6ب) شغال)
ALGO_ICE_MIN_STREAK = 500                 # أقل عدد صفقات متتالية
ALGO_ICE_MIN_SIZE = 1                     # أقل حجم للصفقة: سهم واحد
ALGO_ICE_MAX_SIZE = 10                    # أعلى حجم للصفقة: 10 أسهم
ALGO_ICE_MAX_GAP_SEC = 2                  # "وقت قصير": أكثر من كذا ثانية بين صفقتين = تنقطع السلسلة
ALGO_ICE_REALERT_MIN = 5                  # ما يعيد التنبيه لنفس السهم ونفس الحجم والسعر قبل كذا دقيقة

# ---- المحتوى التعليمي ----
ADD_EDUCATION = False            # الشرح التعليمي تحت التنبيهات: False = محذوف (رسائل أقصر) | True = يرجع
ADD_DISCLAIMER = True            # يضيف سطر إخلاء المسؤولية تحت كل رسالة
DISCLAIMER = "⚠️ محتوى تعليمي فقط، وليس توصية بيع أو شراء."

SENT_KEEP_LINES = 20000             # ملفات "المرسل" تنقص لآخر كذا سطر عشان ما تكبر للأبد
UNIVERSE_BATCH = 200                # حجم دفعة التحميل لما يفلتر كل الأسهم (أصغر = ذاكرة أقل)
# ===============================================

HEADERS = {"User-Agent": "Mozilla/5.0"}


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
# تحذيرات ياهو مع pandas الجديدة (inplace) تطلع مئات الأسطر وتخلي Railway يحذف رسائل السجل
import warnings
warnings.filterwarnings("ignore", message=".*inplace keyword.*")
warnings.filterwarnings("ignore", category=FutureWarning, module="yfinance")


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
            _send_one(cid, "✅ البوت متصل هنا وبيرسل التنبيهات")


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


EDUCATION = {
    "sweep": ("📚 للتعلّم - سحب السيولة:\n"
              "تحت كل قاع واضح تتجمع أوامر وقف خسارة. لما السعر ينزل تحتها ويضربها ثم يرجع ويقفل "
              "فوقها، يعني اللي نزّله أخذ السيولة وما قدر يثبّت تحت.\n"
              "يضعف لو رجع السعر وقفل تحت الدعوم، أو كان حجم شمعة السحب ضعيف."),
    "flow": ("📚 للتعلّم - دخول السيولة:\n"
             "الحجم النسبي يقارن تداول اليوم بمعدّله. حجم أضعاف المعتاد مع اختراق قمة وفلوت صغير "
             "يعني طلب غير عادي على سهم قليل المعروض، فالحركة تكون عنيفة.\n"
             "البني ستوك ترتد بسرعة لو ما وراها سبب حقيقي، والسبريد والتذبذب عالي."),
    "rsplit": ("📚 للتعلّم - التجزئة العكسية:\n"
               "الشركة تدمج أسهمها (مثلاً كل 10 أسهم = سهم) عشان ترفع السعر، غالباً لتفادي "
               "الشطب من البورصة. عدد الأسهم يقل والقيمة ما تتغير.\n"
               "كثير منها يكمل نزول بعدها، وأحياناً يتبعها طرح أسهم جديدة."),
    "algo": ("📚 للتعلّم - خوارزميات التقطيع:\n"
             "مئات الصفقات الصغيرة بنفس الحجم بالضبط (سهم، سهم، سهم...) علامة على برنامج "
             "يقسّم أمر كبير على قطع صغيرة عشان ما يحرك السعر ولا يبان.\n"
             "تقدير الشراء/البيع من اتجاه السعر تقريبي، وفي الأسهم الصغيرة ممكن يكون تلاعب أو صانع سوق."),
    "news": ("📚 للتعلّم - الأخبار:\n"
             "التصنيف \"إيجابي\" آلي من كلمات العنوان، مو قراءة للخبر كامل، فاقرأ الخبر قبل أي قرار.\n"
             "كثير من حركة السعر تصير قبل وصول الخبر، وأحياناً السهم ينزل رغم إن الخبر إيجابي."),
}


# ================== القطاع (تقنية، صحة، ...) - يتكتب تحت اسم السهم بالتنبيه ==================
SHOW_SECTOR = True               # True = يكتب قطاع السهم بكل الأقسام
SECTOR_FILE = os.path.join(os.environ.get("RAILWAY_VOLUME_MOUNT_PATH", "."), "sectors.txt")
SECTOR_AR = {
    "technology": "تقنية 💻", "health care": "صحة 🏥", "healthcare": "صحة 🏥",
    "finance": "مالية 🏦", "financial services": "مالية 🏦", "financials": "مالية 🏦",
    "consumer discretionary": "استهلاكية كمالية 🛍️", "consumer cyclical": "استهلاكية كمالية 🛍️",
    "consumer staples": "استهلاكية أساسية 🛒", "consumer defensive": "استهلاكية أساسية 🛒",
    "industrials": "صناعة 🏭", "energy": "طاقة ⛽", "utilities": "مرافق ⚡",
    "real estate": "عقار 🏢", "basic materials": "مواد أساسية ⛏️",
    "telecommunications": "اتصالات 📡", "communication services": "اتصالات وإعلام 📡",
}
SECTOR_ETFS = {"SPY", "QQQ", "SMH", "IWM", "DIA", "SOXX", "XLK", "XLF", "XLE", "XLV", "ARKK", "TQQQ", "SQQQ", "SOXL"}
_SECTORS = {}
_SECTORS_DAY = None
_SECTOR_LOCK = threading.Lock()


def _load_sectors():
    """خريطة السهم ← القطاع من سكرينر ناسداك (ناسداك + نيويورك + أمكس)، مرة باليوم، ومحفوظة بملف."""
    global _SECTORS_DAY
    today = datetime.now().date()
    if _SECTORS_DAY == today and _SECTORS:
        return
    if not _SECTORS:                                  # من الملف أول (لو الموقع ما رد)
        try:
            with open(SECTOR_FILE, encoding="utf-8") as f:
                for line in f:
                    k, _, v = line.rstrip("\n").partition("\t")
                    if k and v:
                        _SECTORS[k] = v
        except FileNotFoundError:
            pass
    got = {}
    for ex in ("nasdaq", "nyse", "amex"):
        url = ("https://api.nasdaq.com/api/screener/stocks"
               f"?tableonly=true&limit=10000&exchange={ex}&download=true")
        try:
            r = requests.get(url, headers={**HEADERS, "Accept": "application/json"}, timeout=30)
            data = r.json().get("data") or {}
            for row in data.get("rows") or (data.get("table") or {}).get("rows") or []:
                sym = str(row.get("symbol", "")).strip().upper()
                sec = str(row.get("sector") or "").strip()
                if sym and sec:
                    got[sym] = sec
        except Exception as e:
            log(f"القطاعات: ما قدرت أجيب {ex.upper()}: {e}")
    if len(got) > 1000:
        _SECTORS.update(got)
        try:
            with open(SECTOR_FILE, "w", encoding="utf-8") as f:
                f.writelines(f"{k}\t{v}\n" for k, v in _SECTORS.items())
        except Exception:
            pass
        log(f"القطاعات: {len(got)} سهم")
    _SECTORS_DAY = today


def sector_of(sym):
    """قطاع السهم بالعربي، أو "" لو ما عرفناه."""
    sym = (sym or "").upper()
    if sym in INDEX_SYMBOLS:
        return "مؤشر 📈"
    if sym in SECTOR_ETFS:
        return "صندوق مؤشرات 📊"
    with _SECTOR_LOCK:
        try:
            _load_sectors()
        except Exception as e:
            log(f"القطاعات: خطأ - {e}")
        sec = _SECTORS.get(sym) or _SECTORS.get(sym.replace(".", "/"))
        if not sec:                                   # احتياطي: ياهو (مرة لكل سهم)
            try:
                import yfinance as yf
                with _YF_LOCK:
                    sec = (yf.Ticker(sym).info or {}).get("sector") or ""
            except Exception:
                sec = ""
            _SECTORS[sym] = sec or "-"
    if not sec or sec == "-":
        return ""
    return SECTOR_AR.get(sec.lower(), sec)


def _with_sector(text, sym):
    """يضيف سطر "القطاع" تحت السطر اللي فيه اسم السهم."""
    sec = sector_of(sym)
    if not sec:
        return text
    lines = text.split("\n")
    tag = f"${sym}"
    for i, ln in enumerate(lines):
        if tag in ln:
            lines.insert(i + 1, f"القطاع: {sec}")
            return "\n".join(lines)
    return f"القطاع: {sec}\n" + text


def sec_tag(sym, sep=" | "):
    """للرسايل اللي فيها أكثر من سهم: يرجع " | القطاع" يتحط بآخر سطر السهم."""
    if not SHOW_SECTOR:
        return ""
    try:
        sec = sector_of(sym)
    except Exception:
        sec = ""
    return f"{sep}{sec}" if sec else ""


def _send_photo_one(chat_id, png, caption=None):
    """يرسل صورة (PNG بايتات) مع نص تحتها لو فيه. يرجع True لو انرسلت."""
    try:
        data = {"chat_id": chat_id}
        if caption:
            data["caption"] = caption
        r = requests.post(f"{TG_API}/sendPhoto", data=data,
                          files={"photo": ("chart.png", png, "image/png")}, timeout=40).json()
        if not r.get("ok"):
            log(f"فشل إرسال الصورة لـ {chat_id}: {r.get('description')}")
            return False
        return True
    except Exception as e:
        log(f"فشل إرسال الصورة لـ {chat_id}:", e)
        return False


def send_telegram(text, kind=None, sym=None, photo=None):
    if sym and SHOW_SECTOR:
        try:
            text = _with_sector(text, sym)
        except Exception as e:
            log(f"القطاع: {sym}: {e}")
    text = "للمتابعة\n" + text
    for code, name in INDEX_NAMES.items():         # $^GSPC ← سباكس S&P 500 (^GSPC)
        text = text.replace(f"${code}", f"{name} ({code})")
    if ADD_EDUCATION and kind in EDUCATION:
        text += "\n\n" + EDUCATION[kind]
    if ADD_DISCLAIMER and "ليست توصية" not in text:
        text += "\n\n" + DISCLAIMER
    log(text)
    if "ضع_" in TELEGRAM_TOKEN:
        return  # ما حطيت التوكن، يطبع بالشاشة بس
    fits = len(text.encode("utf-16-le")) // 2 <= 1024      # حد تيليجرام للنص تحت الصورة
    for chat_id in list(CHATS):
        if photo and fits and _send_photo_one(chat_id, photo, text):
            continue                                        # الصورة والتنبيه برسالة وحدة
        if photo:
            _send_photo_one(chat_id, photo)                 # النص طويل: الصورة لحالها وبعدها النص
        _send_one(chat_id, text)


def _session(overnight=None):
    """(بداية تقسيم الشموع، نهاية الجلسة) بالدقايق من منتصف الليل بتوقيت نيويورك.
    نهاية None = 24 ساعة. overnight=True يجبره على 24 ساعة (فريم 4 ساعات)."""
    if overnight is None:
        overnight = GAP_OVERNIGHT
    if overnight:
        return 20 * 60, None          # 24 ساعة، اليوم يبدأ 8 بالليل (نفس تريدنج فيو)
    if GAP_EXTENDED:
        return 4 * 60, 20 * 60
    return 9 * 60 + 30, 16 * 60


def us_market_open(now=None, overnight=None):
    """السوق مفتوح حسب الجلسة المختارة (+ دقايق بعد الإغلاق عشان نلحق نفحص آخر شمعة)."""
    now = now or pd.Timestamp.now(tz=NY)
    if overnight is None:
        overnight = GAP_OVERNIGHT
    wd, m = now.weekday(), now.hour * 60 + now.minute
    # 20 دقيقة: ياهو أحياناً ما يعطي كل شموع الربع ساعة بعد الإغلاق، فالشمعة تعتبر مقفلة
    # بعد 15 دقيقة (only_closed). لو الوقت أقصر من كذا تضيع آخر شمعة باليوم (4-8 بالليل)
    buf = max(max(GAP_SCAN_AFTER_CLOSE_MIN) + 2, 20)
    if overnight:                     # من الأحد 8 بالليل إلى الجمعة 8 بالليل
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


_YF_LOCK = threading.RLock()   # ياهو ما يتحمل تحميلين بنفس اللحظة من خيطين


def download_batches(tickers, batch_size, **kw):
    """يحمّل بيانات ياهو على دفعات، ويرجع (الرمز، البيانات) لكل سهم."""
    import yfinance as yf

    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i + batch_size]
        try:
            with _YF_LOCK:
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


# ================== أدوات الشموع والجلسات ==================
def _to_number(x):
    try:
        return float(str(x).replace("$", "").replace(",", "").strip())
    except Exception:
        return 0.0


OHLC = ["Open", "High", "Low", "Close"]


def to_ny(df):
    df = df.dropna(subset=OHLC)
    idx = df.index
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
    return df.set_index(idx.tz_convert(NY))


def _hhmm(m):
    return f"{m // 60:02d}:{m % 60:02d}"


def to_frame(df, minutes, overnight=None, session=None):
    """يحول شموع النص ساعة لشموع أكبر (60 = ساعة، 240 = 4 ساعات) بتوقيت نيويورك،
    بنفس تقسيم تريدنج فيو. كل شمعة معها وقت إغلاقها (end) وعدد الشموع الصغيرة اللي فيها (n).
    overnight=True = 24 ساعة (الشموع تبدأ 8 بالليل)."""
    df = df.dropna(subset=OHLC)
    if df.empty:
        return df
    df = to_ny(df)
    anchor, end_min = session or _session(overnight)   # session = (بداية، نهاية) بالدقايق لو تبي جلسة معينة
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


def only_closed(c, last_bar, now):
    """يخلي الشموع المقفلة بس. الشمعة تعتبر مقفلة لو وقتها خلص، وبياناتها كاملة
    (أو جات بيانات بعدها، أو مر ربع ساعة على إغلاقها)."""
    if c.empty:
        return c
    starts = pd.Series(c.index, index=c.index)
    expected = ((c["end"] - starts).dt.total_seconds() / (GAP_BASE_MIN * 60)).round()
    done = (c["end"] <= now) & ((c["n"] >= expected) | (last_bar >= c["end"])
                                | (now >= c["end"] + pd.Timedelta(minutes=15)))
    return c[done.values]


# ---------- شموع 4 ساعات للجلسة العادية: 9:30-1:30 و 1:30-4:00 نيويورك (يستخدمها سحب الجمعة/الاثنين) ----------
_MKT4H_START, _MKT4H_SPLIT, _MKT4H_END = 9 * 60 + 30, 13 * 60 + 30, 16 * 60


def mkt4h_candles(df):
    """شموع النص ساعة (الجلسة العادية) → شموع 4 ساعات: 9:30-1:30 و 1:30-4:00.
    كل شمعة معها end (وقت الإغلاق) و n (عدد الشموع) و need (المطلوب)."""
    df = to_ny(df)
    if df.empty:
        return df
    m = df.index.hour * 60 + df.index.minute
    df = df[(m >= _MKT4H_START) & (m < _MKT4H_END)]
    if df.empty:
        return df
    m = pd.Series(df.index.hour * 60 + df.index.minute, index=df.index)
    first = m < _MKT4H_SPLIT
    start = df.index.normalize() + pd.to_timedelta(
        first.map({True: _MKT4H_START, False: _MKT4H_SPLIT}).values, unit="m")
    out = df.groupby(start).agg(Open=("Open", "first"), High=("High", "max"),
                                Low=("Low", "min"), Close=("Close", "last"),
                                n=("Close", "size"))
    sm = pd.Series(out.index.hour * 60 + out.index.minute, index=out.index)
    em = sm.map(lambda s: _MKT4H_SPLIT if s == _MKT4H_START else _MKT4H_END)
    out["end"] = out.index.normalize() + pd.to_timedelta(em.values, unit="m")
    out["need"] = ((em - sm) / 30).values
    return out


# ================== قوائم الأسهم (تستخدمها كل الأقسام) ==================
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
    الماسح واليومي والشورت كلهم (بدل ما كل واحد يحمّل 3000 سهم لحاله)."""
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
    if ONE_LIST:
        log(f"{label}: {len(WATCH_SYMBOLS)} سهم (القائمة الموحدة)")
        return list(WATCH_SYMBOLS)
    stats = _universe_stats(include_nyse)
    keep = [t for t, (last, avg_vol) in stats.items()
            if min_price <= last <= max_price and avg_vol >= min_vol]
    log(f"{label}: {len(keep)} سهم سعرها {min_price}-{max_price}$ وعليها تداول")
    return keep


# ================== ملفات المرسل (عشان ما يتكرر التنبيه) ==================
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


# ================== (4ج) الشورت صفر اللحظي (الأسهم المتاحة للشورت) ==================
#   المصدر: ملف Interactive Brokers العام (نفس ChartExchange) يتحدث كل 15 دقيقة
#   + حجم الشورت اليومي آخر 15 يوم من FINRA
def _bz_num(x):
    try:
        return float(str(x).replace("$", "").replace(",", "").strip())
    except Exception:
        return 0.0


BZ_EXCHANGE = {}   # الرمز -> البورصة (لرابط ChartExchange)


def bz_universe():
    """البني ستوك: {الرمز: {"price", "cap"}} من سكرينر ناسداك (ناسداك + نيويورك + أميكس)."""
    out = {}
    for ex in ("nasdaq", "nyse", "amex"):
        url = ("https://api.nasdaq.com/api/screener/stocks"
               f"?tableonly=true&limit=10000&exchange={ex}&download=true")
        try:
            r = requests.get(url, headers={**HEADERS, "Accept": "application/json"}, timeout=40)
            data = r.json().get("data") or {}
            rows = data.get("rows") or (data.get("table") or {}).get("rows") or []
            for row in rows:
                sym = str(row.get("symbol", "")).strip().upper()
                price, cap = _bz_num(row.get("lastsale")), _bz_num(row.get("marketCap"))
                price_ok = (price >= BZ_MIN_PRICE if BZ_MIN_PRICE else price > 0) and \
                           (price <= BZ_MAX_PRICE if BZ_MAX_PRICE else True)
                if ONE_LIST:
                    ok = sym in WATCH_SYMBOLS
                else:
                    ok = (sym.isalpha() and len(sym) <= 5 and price_ok
                          and cap >= BZ_MIN_MARKET_CAP and (cap <= BZ_MAX_MARKET_CAP if BZ_MAX_MARKET_CAP else True))
                if ok:
                    out[sym] = {"price": price, "cap": cap}
                    BZ_EXCHANGE[sym] = ex
        except Exception as e:
            log(f"الشورت صفر: سكرينر {ex} خطأ: {e}")
    return out


def bz_cx_link(sym):
    """رابط صفحة السهم في ChartExchange عشان تتأكد بنفسك."""
    ex = BZ_EXCHANGE.get(sym, "nasdaq")
    return f"https://chartexchange.com/symbol/{ex}-{sym.lower()}/borrow-fee/"


_bz_last_ok = None   # (السيرفر، سلبي؟) اللي نجح آخر مرة — يجربه أول عشان ما يضيع وقت


def bz_download_ibkr():
    """يحمّل ملف IBKR. يبدأ بآخر سيرفر نجح، وبعدها الباقي، ويكتب بالسجل وين وقف بالضبط."""
    import ftplib
    import socket
    global _bz_last_ok
    errors = []
    combos = [(h, p) for h in BZ_FTP_HOSTS for p in (True, False)]
    if _bz_last_ok in combos:
        combos.remove(_bz_last_ok)
        combos.insert(0, _bz_last_ok)
    for host, passive in combos:
        stage = "الاتصال"
        buf = io.BytesIO()
        try:
            ip = socket.gethostbyname(host)
            with ftplib.FTP(timeout=BZ_FTP_TIMEOUT) as ftp:
                ftp.connect(ip, 21)
                stage = "تسجيل الدخول"
                ftp.login("shortstock", "")
                ftp.set_pasv(passive)
                stage = "تحميل الملف"
                ftp.retrbinary("RETR usa.txt", buf.write)
            text = buf.getvalue().decode("utf-8", errors="ignore")
            if text.strip():
                _bz_last_ok = (host, passive)
                if errors:
                    log(f"الشورت صفر: نجح التحميل من {host} ({'سلبي' if passive else 'نشط'}) "
                        f"بعد: {' | '.join(errors)}")
                return text
            errors.append(f"{host}: الملف فاضي")
        except Exception as e:
            errors.append(f"{host} {'سلبي' if passive else 'نشط'} وقف عند {stage}: {e}")
    raise RuntimeError("ما قدرت أحمل ملف IBKR — " + " | ".join(errors))


def bz_parse_ibkr(text):
    """{الرمز: {"available": عدد، "fee": رسوم %}}"""
    out, cols = {}, []
    for line in text.splitlines():
        if not line.strip():
            continue
        if line.startswith("#SYM"):
            cols = [c.strip().lstrip("#").upper() for c in line.split("|")]
            continue
        if line.startswith("#") or not cols:
            continue
        row = dict(zip(cols, line.split("|")))
        sym = row.get("SYM", "").strip().upper()
        raw = row.get("AVAILABLE", "").strip().replace(",", "").lstrip(">")
        try:
            avail = int(float(raw))
        except ValueError:
            continue
        try:
            fee = float(row.get("FEERATE", "") or "nan")
        except ValueError:
            fee = float("nan")
        if sym:
            out[sym] = {"available": avail, "fee": fee}
    return out


_bz_finra = {}


def _bz_finra_day(day):
    if day in _bz_finra:
        return _bz_finra[day]
    try:
        r = requests.get(f"https://cdn.finra.org/equity/regsho/daily/CNMSshvol{day}.txt",
                         headers=HEADERS, timeout=30)
        if r.status_code != 200:
            return None
    except Exception:
        return None
    rows = {}
    for line in r.text.splitlines()[1:]:
        p = line.split("|")
        if len(p) >= 5:
            try:
                rows[p[1].strip().upper()] = (float(p[2]), float(p[4]))
            except ValueError:
                pass
    _bz_finra[day] = rows
    return rows


def bz_short_history_txt(sym):
    out, d, tries = [], datetime.now(ZoneInfo(NY)).date(), 0
    while len(out) < BZ_SHORT_DAYS and tries < BZ_SHORT_DAYS * 2 + 10:
        tries += 1
        if d.weekday() < 5:
            rows = _bz_finra_day(d.strftime("%Y%m%d"))
            if rows is not None and sym in rows:
                sv, tv = rows[sym]
                out.append(f"{d:%m-%d}: {sv:,.0f} من {tv:,.0f} ({(sv / tv * 100 if tv else 0):.0f}%)")
        d -= timedelta(days=1)
    for k in sorted(_bz_finra)[:-(BZ_SHORT_DAYS * 2 + 10)]:
        _bz_finra.pop(k, None)
    if not out:
        return "📊 حجم الشورت آخر 15 يوم: ما فيه بيانات"
    return f"📊 حجم الشورت آخر {len(out)} يوم (FINRA):\n" + "\n".join(out)


def _bz_out(state, kind, text, sym=None):
    """يرسل التنبيه فوراً، أو يحطه بالطابور لو BZ_SPREAD_24H (عشان تنقسم على 24 ساعة)."""
    if not BZ_SPREAD_24H:
        send_telegram(text, sym=sym)
        return
    q = state.get("_queue")
    if not isinstance(q, list):
        q = state["_queue"] = []
    q.append({"k": kind, "t": text, "s": sym, "at": datetime.now(ZoneInfo(LOCAL_TZ)).isoformat()})


def bz_dispatch(state):
    """يرسل تنبيه واحد من الطابور كل (24 ساعة ÷ BZ_MAX_PER_DAY). اللي عمره أكثر من 24 ساعة ينشال."""
    q = state.get("_queue")
    if not BZ_SPREAD_24H or not isinstance(q, list) or not q:
        return
    now = datetime.now(ZoneInfo(LOCAL_TZ))
    q[:] = [x for x in q if now - datetime.fromisoformat(x["at"]) < timedelta(hours=24)]
    if not BZ_ZERO_ALERTS:   # يشيل تنبيهات الشورت صفر اللي كانت بالطابور قبل الإطفاء
        q[:] = [x for x in q if not str(x.get("t", "")).startswith("🚫")]
    gap = timedelta(minutes=24 * 60 / max(BZ_MAX_PER_DAY or 30, 1))
    last = state.get("_last_send")
    if not q or (last and now - datetime.fromisoformat(last) < gap):
        _bz_save_state(state)
        return
    x = q.pop(0)
    send_telegram(x["t"], sym=x["s"])
    state["_last_send"] = now.isoformat()
    _bz_save_state(state)
    log(f"الشورت صفر: انرسل تنبيه من الطابور ({x['s']}) — باقي {len(q)}")


def _bz_load_state():
    try:
        with open(BZ_STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _bz_save_state(state):
    try:
        with open(BZ_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f)
    except Exception as e:
        log(f"الشورت صفر: ما قدرت أحفظ الحالة: {e}")


_bz_last_hash = None   # بصمة آخر ملف IBKR — لو ما تغير ما يعيد الفحص


def bz_check(state, first_run, universe):
    """يرجّع True لو الملف جديد وانفحص، False لو نفس الملف السابق."""
    global _bz_last_hash
    text = bz_download_ibkr()
    h = hash(text)
    if h == _bz_last_hash and not first_run:
        return False          # IBKR ما حدّث الملف للحين
    _bz_last_hash = h
    data = bz_parse_ibkr(text)
    if not data:
        log("الشورت صفر: ملف IBKR فاضي أو صيغته تغيرت")
        return True
    now = datetime.now(ZoneInfo(LOCAL_TZ))
    fee_txt = lambda f: "غير معروف" if f != f else f"{f:.2f}%"
    zero_now = alerts = 0
    cool = state.get("_cool")
    if not isinstance(cool, dict):
        cool = state["_cool"] = {}

    daily = state.get("_daily")
    today_s = now.strftime("%Y-%m-%d")
    if not isinstance(daily, dict) or daily.get("day") != today_s:
        daily = state["_daily"] = {"day": today_s, "n": 0}

    def cooled(kind, sym):
        """True = مسموح ينبه: ما نبه على هالسهم خلال BZ_COOLDOWN_DAYS، وما وصل حد اليوم BZ_MAX_PER_DAY."""
        if BZ_MAX_PER_DAY and daily["n"] >= BZ_MAX_PER_DAY:
            return False
        key = f"{kind}:{sym}"
        last = cool.get(key)
        if BZ_COOLDOWN_DAYS and last and now - datetime.fromisoformat(last) < timedelta(days=BZ_COOLDOWN_DAYS):
            return False
        cool[key] = now.isoformat()
        daily["n"] += 1
        return True

    for k in [k for k, v in cool.items() if now - datetime.fromisoformat(v) >= timedelta(days=max(BZ_COOLDOWN_DAYS, 1))]:
        del cool[k]
    zlog = state.get("_zero_log")
    if not isinstance(zlog, dict):
        zlog = state["_zero_log"] = {}
    for k in [k for k, v in zlog.items() if now - datetime.fromisoformat(v) >= timedelta(days=30)]:
        del zlog[k]
    hist = state.get("_hist")              # {الرمز: {اليوم: أعلى متاح باليوم}} لآخر BZ_DROP_DAYS يوم
    if not isinstance(hist, dict):
        hist = state["_hist"] = {}
    cutoff = (now - timedelta(days=BZ_DROP_DAYS)).strftime("%Y-%m-%d")
    for s_ in list(hist):
        h_ = {d: v for d, v in hist[s_].items() if d >= cutoff}
        if h_:
            hist[s_] = h_
        else:
            del hist[s_]
    for sym, u in universe.items():
        info = data.get(sym)
        prev = state.get(sym)
        if info is None:
            # IBKR يشيل السهم من الملف لما يخلص المتاح = صفر (نفس ملاحظة ChartExchange)
            if not isinstance(prev, (int, float)) or prev <= 0:
                continue
            info = {"available": 0, "fee": float("nan")}
        avail = info["available"]
        zero_now += avail == 0
        if prev is not None and not first_run and prev > 0 and avail == 0:
            zlog[sym] = now.isoformat()          # سجل الشورت صفر للقائمة الأسبوعية
        elif avail > 0:
            zlog.pop(sym, None)
        if prev is not None and not first_run:
            if BZ_ZERO_ALERTS and prev > 0 and avail == 0 and cooled("zero", sym):
                _bz_out(state, "main",
                    f"🚫 الشورت صفر - ${sym}\n"
                    f"السعر: {u['price']:.2f}$\n"
                    f"القيمة السوقية: {u['cap'] / 1e6:.1f} مليون$\n"
                    f"الأسهم المتاحة للشورت: 0 (كانت {prev:,})\n"
                    f"رسوم الاستلاف: {fee_txt(info['fee'])}\n"
                    f"الوقت: {now:%Y-%m-%d %H:%M} (توقيتك)\n"
                    f"المصدر: Interactive Brokers (نفس ChartExchange)\n"
                    f"{bz_cx_link(sym)}\n\n"
                    f"{bz_short_history_txt(sym)}", sym=sym)
                alerts += 1
                time.sleep(0.5)
        # ---- (4ج-2) نزول الشورت المتاح عن أعلى رقم بالشهر ----
        sh = hist.get(sym) or {}
        if sh and not first_run and BZ_DROP_ALERTS and avail > 0:
            top_day, top = max(sh.items(), key=lambda x: x[1])
            drop = (1 - avail / top) * 100 if top else 0
            was_above = prev is None or prev >= top * (1 - BZ_DROP_PCT / 100)   # يعني توه نزل تحت الحد
            if top >= BZ_DROP_MIN_HIGH and drop > BZ_DROP_PCT and was_above and cooled("drop", sym):
                _bz_out(state, "main",
                    f"📉 نزول الشورت المتاح - ${sym}\n"
                    f"نزل {drop:.0f}% من أعلى رقم خلال آخر شهر\n"
                    f"الأسهم المتاحة للشورت: {avail:,}\n"
                    f"أعلى رقم بالشهر: {top:,} (يوم {top_day})\n"
                    f"السعر: {u['price']:.2f}$\n"
                    f"القيمة السوقية: {u['cap'] / 1e6:.1f} مليون$\n"
                    f"رسوم الاستلاف: {fee_txt(info['fee'])}\n"
                    f"الوقت: {now:%Y-%m-%d %H:%M} (توقيتك)\n"
                    f"المصدر: Interactive Brokers\n"
                    f"{bz_cx_link(sym)}\n\n"
                    f"{bz_short_history_txt(sym)}", sym=sym)
                alerts += 1
                time.sleep(0.5)
        if avail > sh.get(today_s, -1):
            hist.setdefault(sym, {})[today_s] = avail
        state[sym] = avail
    _bz_save_state(state)
    log(f"[{datetime.now():%H:%M}] الشورت صفر: {len(universe)} سهم بني ستوك — "
        f"صفر حالياً {zero_now} — تنبيهات {alerts}")
    return True


def bz_weekly_zero_list(state, universe, now=None):
    """أسهم صار الشورت عندها صفر خلال آخر BZ_WEEKLY_DAYS يوم: [(الرمز، وقت الصفر)] — الأحدث أول."""
    now = now or datetime.now(ZoneInfo(LOCAL_TZ))
    since = now - timedelta(days=BZ_WEEKLY_DAYS)
    found = {}
    for sym, ts in (state.get("_zero_log") or {}).items():
        t = datetime.fromisoformat(ts)
        if t >= since and state.get(sym) == 0:
            found[sym] = t
    items = [(s, t) for s, t in sorted(found.items(), key=lambda x: x[1], reverse=True) if s in universe]
    if not BZ_WEEKLY_MAX_RISE or not items:
        return [(s, t, None) for s, t in items][:BZ_WEEKLY_N]
    rises = bz_week_rise([s for s, _ in items], since)
    out = []
    for s, t in items:
        r = rises.get(s)
        if r is not None and r > BZ_WEEKLY_MAX_RISE:
            continue                      # عطى ارتفاع أكثر من 30% — يستبعد
        out.append((s, t, r))
        if len(out) >= BZ_WEEKLY_N:
            break
    return out


def bz_week_rise(syms, since):
    """{الرمز: أعلى ارتفاع % خلال الفترة} = (أعلى سعر من بداية الفترة ÷ إغلاق آخر يوم قبلها) - 1."""
    out = {}
    try:
        for sym, df in download_batches(syms, 50, period="1mo", interval="1d"):
            idx = df.index.tz_localize(None) if df.index.tz is not None else df.index
            start = pd.Timestamp(since.date())
            before, during = df[idx < start], df[idx >= start]
            if before.empty or during.empty:
                continue
            base = float(before["Close"].iloc[-1])
            if base > 0:
                out[sym] = (float(during["High"].max()) / base - 1) * 100
    except Exception as e:
        log(f"الشورت صفر: ما قدرت أحسب الارتفاع الأسبوعي: {e}")
    return out


def bz_weekly_zero_text(state, universe, now=None):
    now = now or datetime.now(ZoneInfo(LOCAL_TZ))
    rows = bz_weekly_zero_list(state, universe, now)
    head = (f"📋 قائمة الشورت صفر الأسبوعية - {now:%Y-%m-%d}\n"
            f"أسهم صار الشورت عندها صفر خلال آخر {BZ_WEEKLY_DAYS} أيام"
            + (f" وما ارتفعت أكثر من {BZ_WEEKLY_MAX_RISE}%" if BZ_WEEKLY_MAX_RISE else "") + "\n"
            "الشورت صفر = ما فيه ولا سهم متاح للاستلاف عشان البيع على المكشوف (المصدر: Interactive Brokers)\n")
    if not rows:
        return head + "\nما فيه ولا سهم ينطبق عليه الشرط هالأسبوع."
    lines = [f"{i}) ${s} - صفر من {t:%m-%d} | السعر {universe[s]['price']:.2f}$"
             + (f" | أعلى ارتفاع {r:.0f}%" if r is not None else "")
             + f" | القيمة {universe[s]['cap'] / 1e6:.1f} مليون$"
             for i, (s, t, r) in enumerate(rows, 1)]
    return head + f"\n({len(rows)} سهم)\n" + "\n".join(lines)


def bz_weekly_zero(state, universe):
    """كل أحد: يرسل القائمة مرة وحدة بالأسبوع."""
    if not BZ_WEEKLY_ZERO or not universe:
        return
    now = datetime.now(ZoneInfo(LOCAL_TZ))
    if now.weekday() != BZ_WEEKLY_DAY or now.hour < BZ_WEEKLY_HOUR:
        return
    wk = now.strftime("%G-W%V")
    if state.get("_weekly_zero") == wk:
        return
    send_telegram(bz_weekly_zero_text(state, universe, now))
    state["_weekly_zero"] = wk
    _bz_save_state(state)
    log("الشورت صفر: انرسلت القائمة الأسبوعية")


BZ_TEST_ID = "1"   # غيّر الرقم لو تبي رسالة تجريبية ثانية بعد الرفع الجاي


def bz_send_test_once():
    """يرسل تنبيه تجريبي مرة وحدة بس (يتذكرها في مجلد /data عشان ما تتكرر مع كل تشغيل)."""
    if not BZ_ZERO_ALERTS:
        return
    folder = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH", ".")
    marker = os.path.join(folder, "bz_test_sent.txt")
    try:
        with open(marker, encoding="utf-8") as f:
            if f.read().strip() == BZ_TEST_ID:
                return
    except Exception:
        pass
    now = datetime.now(ZoneInfo(LOCAL_TZ))
    send_telegram(
        "🧪 رسالة تجريبية - هذا مو تنبيه حقيقي\n\n"
        "🚫 الشورت صفر - $NUWE\n"
        "السعر: 6.46$\n"
        "الأسهم المتاحة للشورت: 0 (كانت 76)\n"
        "رسوم الاستلاف: 173.41%\n"
        f"الوقت: {now:%Y-%m-%d %H:%M} (توقيتك)\n"
        "المصدر: Interactive Brokers (نفس ChartExchange)\n"
        f"{bz_cx_link('NUWE')}\n\n"
        "لو وصلتك هالرسالة، التنبيهات الحقيقية بتوصل لنفس المكان.")
    try:
        with open(marker, "w", encoding="utf-8") as f:
            f.write(BZ_TEST_ID)
    except Exception as e:
        log(f"الشورت صفر: ما قدرت أحفظ علامة الرسالة التجريبية: {e}")


def bz_run_forever():
    price_txt = (f"{BZ_MIN_PRICE:g}-{BZ_MAX_PRICE:g}$" if BZ_MAX_PRICE
                 else f"السعر {BZ_MIN_PRICE:g}$ وفوق" if BZ_MIN_PRICE else "بدون حد سعر")
    log(f"الشورت صفر: بدأ — {price_txt}، " + (f"قيمة سوقية {BZ_MIN_MARKET_CAP / 1e6:g}-{BZ_MAX_MARKET_CAP / 1e6:g} مليون " if BZ_MAX_MARKET_CAP else "بدون حد للقيمة السوقية ")
        + 
        f"— كل {BZ_EVERY_MIN} دقيقة")
    bz_send_test_once()
    state = _bz_load_state()
    first_run = not state      # أول مرة يسجل الوضع بس عشان ما يجيك سيل تنبيهات
    universe, uni_last = {}, 0.0
    last_ok, warned = time.time(), False
    while True:
        try:
            if not universe or time.time() - uni_last >= BZ_UNIVERSE_EVERY_MIN * 60:
                fresh = bz_universe()
                if fresh:
                    universe, uni_last = fresh, time.time()
                    log(f"الشورت صفر: قائمة البني ستوك {len(universe)} سهم")
            if universe:
                bz_check(state, first_run, universe)
                first_run = False
                bz_dispatch(state)
                bz_weekly_zero(state, universe)
                if warned:
                    send_telegram("✅ تنبيه الشورت صفر رجع يشتغل (ملف IBKR يتحمل طبيعي)")
                last_ok, warned = time.time(), False
        except Exception as e:
            log(f"الشورت صفر: خطأ {e}")
            if time.time() - last_ok >= BZ_WARN_AFTER_MIN * 60 and not warned:   # ساعة بدون بيانات = يعلمك
                warned = True
                send_telegram("⚠️ تنبيه الشورت صفر واقف: ما قدر يحمل ملف IBKR من ساعة.\n"
                              f"آخر خطأ: {str(e)[:300]}")
        time.sleep(BZ_EVERY_MIN * 60)


# ================== طلبات بيانات ألباكا (تستخدمها سلسلة العقود) ==================
def _alpaca_data_get(path, params=None):
    r = requests.get("https://data.alpaca.markets" + path, params=params or {}, timeout=20,
                     headers={"APCA-API-KEY-ID": ALPACA_KEY, "APCA-API-SECRET-KEY": ALPACA_SECRET,
                              "Accept": "application/json"})
    r.raise_for_status()
    return r.json()


# ================== (1ك-2) سحب سيولة دعم ومقاومة الأسبوع السابق - فريم 4 ساعات ==================


def _week_start(ts):
    """بداية الأسبوع (الاثنين 00:00 بتوقيت نيويورك)."""
    ts = pd.Timestamp(ts)
    return ts.normalize() - pd.Timedelta(days=ts.weekday())


def _prev_week_rows(daily, prev_wk, this_wk):
    d = [pd.Timestamp(i).date() for i in daily.index]
    return daily[[(prev_wk <= x < this_wk) for x in d]]


def prev_week_low(daily, prev_wk, this_wk):
    """(قاع الأسبوع السابق، يومه) من الشموع اليومية، أو None."""
    pw = _prev_week_rows(daily, prev_wk, this_wk)
    if pw.empty:
        return None
    lows = pw["Low"].astype(float)
    return float(lows.min()), pd.Timestamp(lows.idxmin()).date()


def prev_week_high(daily, prev_wk, this_wk):
    """(قمة الأسبوع السابق، يومها) من الشموع اليومية، أو None."""
    pw = _prev_week_rows(daily, prev_wk, this_wk)
    if pw.empty:
        return None
    highs = pw["High"].astype(float)
    return float(highs.max()), pd.Timestamp(highs.idxmax()).date()


def prev_week_ext_levels(df, week_start):
    """قاع وقمة الأسبوع السابق من شموع 15 دقيقة على الجلسة الممتدة (بري + ماركت + أفتر،
    4 الفجر - 8 بالليل نيويورك) بدون الجلسة الليلية.
    يرجع {"low": (القاع، يومه), "high": (القمة، يومها)} أو None."""
    prev = week_start - pd.Timedelta(days=7)
    pw = df[(df.index >= prev) & (df.index < week_start)]
    if pw.empty:
        return None
    pw = pw.between_time("04:00", "19:59")
    if pw.empty:
        return None
    lows, highs = pw["Low"].astype(float), pw["High"].astype(float)
    return {"low": (float(lows.min()), pd.Timestamp(lows.idxmin()).date()),
            "high": (float(highs.max()), pd.Timestamp(highs.idxmax()).date())}


def prev_day_ext_levels(df, today):
    """قاع وقمة اليوم السابق (آخر يوم تداول قبل today) من شموع 15 دقيقة على الجلسة الممتدة
    (4 الفجر - 8 بالليل نيويورك) بدون الليلي. يرجع {"low": (القاع، اليوم), "high": (القمة، اليوم)} أو None."""
    ext = df.between_time("04:00", "19:59")
    if ext.empty:
        return None
    dates = pd.Series(ext.index.date, index=ext.index)
    before = dates[(dates < today) & (ext.index.weekday < 5)]   # بدون السبت والأحد
    if before.empty:
        return None
    pd_day = before.iloc[-1]                      # الاثنين = الجمعة، وبعد العطلة = آخر يوم فيه تداول
    pdd = ext[(dates == pd_day).values]
    lows, highs = pdd["Low"].astype(float), pdd["High"].astype(float)
    return {"low": (float(lows.min()), pd_day), "high": (float(highs.max()), pd_day)}


def check_pwl_1h(c1h, support, week_start, wick_only=False):
    """الدعم: آخر شمعة ساعة (من هالأسبوع) ذيلها نزل تحت قاع الأسبوع السابق وقفلت فوقه.
    wick_only=True: الافتتاح بعد لازم فوق الدعم (الذيل بس اللي نزل تحته)."""
    c1h = c1h[c1h.index >= week_start]
    if c1h.empty:
        return None
    last = c1h.iloc[-1]
    low, close = float(last["Low"]), float(last["Close"])
    if not (low < support < close):
        return None
    if wick_only and not float(last["Open"]) > support:
        return None
    before = c1h.iloc[:-1]
    closes_beyond = int((before["Close"] < support).sum()) if len(before) else 0
    return {"open": float(last["Open"]), "high": float(last["High"]), "low": low, "close": close,
            "depth": (support - low) / support * 100, "start": c1h.index[-1], "end": last["end"],
            "closes_beyond": closes_beyond,
            "first_touch": bool(before.empty or before["Low"].min() >= support)}


def check_pwh_1h(c1h, resistance, week_start, wick_only=False):
    """المقاومة: آخر شمعة ساعة (من هالأسبوع) ذيلها طلع فوق قمة الأسبوع السابق وقفلت تحتها.
    wick_only=True: الافتتاح بعد لازم تحت المقاومة (الذيل بس اللي طلع فوقها)."""
    c1h = c1h[c1h.index >= week_start]
    if c1h.empty:
        return None
    last = c1h.iloc[-1]
    high, close = float(last["High"]), float(last["Close"])
    if not (close < resistance < high):
        return None
    if wick_only and not float(last["Open"]) < resistance:
        return None
    before = c1h.iloc[:-1]
    closes_beyond = int((before["Close"] > resistance).sum()) if len(before) else 0
    return {"open": float(last["Open"]), "high": high, "low": float(last["Low"]), "close": close,
            "depth": (high - resistance) / resistance * 100, "start": c1h.index[-1], "end": last["end"],
            "closes_beyond": closes_beyond,
            "first_touch": bool(before.empty or before["High"].max() <= resistance)}


def _pwl_message(t, side, lvl, lvl_day, r, frame="فريم ساعة", trade=False,
                 period="الأسبوع السابق", scope="هالأسبوع"):
    t1 = pd.Timestamp(r["start"]).tz_convert(LOCAL_TZ)
    color = "خضراء 🟢" if r["close"] > r["open"] else "حمراء 🔴"
    if side == "low":
        head = f"💧 سحب سيولة دعم {period} — {frame}"
        lvl_line = f"الدعم (قاع {period}): {lvl:.2f}  (يوم {lvl_day})"
        wick = f"أقل سعر بالشمعة: {r['low']:.2f}  (-{r['depth']:.2f}% تحت الدعم)"
        close = f"الإغلاق: {r['close']:.2f} فوق الدعم | الشمعة {color}"
        word, where = "الدعم", "تحت"
    else:
        head = f"🔻 سحب سيولة مقاومة {period} — {frame}"
        lvl_line = f"المقاومة (قمة {period}): {lvl:.2f}  (يوم {lvl_day})"
        wick = f"أعلى سعر بالشمعة: {r['high']:.2f}  (+{r['depth']:.2f}% فوق المقاومة)"
        close = f"الإغلاق: {r['close']:.2f} تحت المقاومة | الشمعة {color}"
        word, where = "المقاومة", "فوق"
    note = (f"أول لمس {'للدعم' if side == 'low' else 'للمقاومة'} {scope}" if r["first_touch"] else
            f"قبلها {r['closes_beyond']} شمعة قفلت {where} {word}" if r["closes_beyond"] else
            f"لمس {word} قبل وما قفل {where}{'ه' if side == 'low' else 'ها'}")
    trade_lines = ""
    if trade:
        if side == "low":
            trade_lines = (f"\n📈 الاتجاه المتوقع: كول (صعود)"
                           f"\n🛑 الوقف: الدعم {lvl:.2f}")
        else:
            trade_lines = (f"\n📉 الاتجاه المتوقع: بوت (هبوط)"
                           f"\n🛑 الوقف: المقاومة {lvl:.2f}")
    return (f"{head}\nالسهم: ${t}\n{lvl_line}\n{wick}\n{close}\n{note}"
            f"{trade_lines}\n"
            f"وقت الشمعة: {t1:%Y-%m-%d %H:%M} (توقيتك)")


def scan_pwl_4h(symbols, sent):
    """(1ك-2) فريم 4 ساعات: سحب الدعم (ENABLE_PWL_4H) والمقاومة (ENABLE_PWH_4H) — تنبيه واحد لكل جهة بالأسبوع."""
    now = pd.Timestamp.now(tz=NY)
    wk0 = _week_start(now)
    checks4h = []
    if ENABLE_PWL_4H or ENABLE_WKOPT:
        checks4h.append(("low", "pwl4h", check_pwl_1h, ENABLE_PWL_4H))
    if ENABLE_PWH_4H or ENABLE_WKOPT:
        checks4h.append(("high", "pwh4h", check_pwh_1h, ENABLE_PWH_4H))
    # (1ي) اليوم السابق - فريم ساعة
    checks1h = [x for x in (("low", "pdl1h", check_pwl_1h, ENABLE_PDL_1H),
                            ("high", "pdh1h", check_pwh_1h, ENABLE_PDH_1H)) if x[3]]
    if not checks4h and not checks1h:
        return
    today = now.date()
    day0 = now.normalize()                          # بداية اليوم (نيويورك)
    hits = 0
    for t, df in download_batches(symbols, 100, period="15d", interval=f"{GAP_BASE_MIN}m",
                                  prepost=True):   # 15 يوم عشان الأسبوع السابق كامل + بري وأفتر
        try:
            df = to_ny(df)[OHLC]
            if df.empty:
                continue
            # ---- (1ي) سحب دعم/مقاومة اليوم السابق - فريم ساعة ----
            lvd = prev_day_ext_levels(df, today) if checks1h else None
            if lvd:
                c1h = only_closed(to_frame(df, 60, overnight=False), df.index.max(), now)
                for side, tag, fn, _ in checks1h:
                    lvl, lvl_day = lvd[side]
                    r = fn(c1h, lvl, day0, wick_only=PD1H_WICK_ONLY)
                    if not r or (now - pd.Timestamp(r["end"])).total_seconds() / 60 > PWL_MAX_ALERT_DELAY_MIN:
                        continue
                    key = f"{t}-{tag}-{today:%Y%m%d}"     # تنبيه واحد لكل سهم باليوم لكل جهة
                    if key in sent:
                        continue
                    sent.add(key)
                    _append_line(GAP_SENT_FILE, key)
                    hits += 1
                    send_telegram(with_gamma(_pwl_message(t, side, lvl, lvl_day, r, frame="فريم ساعة",
                                                          trade=True, period="اليوم السابق", scope="اليوم"),
                                             t, r["close"]), kind="sweep", sym=t)
            if not checks4h:
                continue
            # مستويات الأسبوع السابق من البري + الماركت + الأفتر (بدون الليلي)
            lv4 = prev_week_ext_levels(df, wk0)
            if not lv4:
                continue
            # overnight=False: شموع 4-8، 8-12، 12-4، 4-8 (بري + ماركت + أفتر) بدون الليلي
            c4h = only_closed(to_frame(df, 240, overnight=False), df.index.max(), now)
            wk_key = f"{t}-wkopt-{wk0:%Y%m%d}"     # (12) تنبيه واحد لكل سهم بالأسبوع
            for side, tag, fn, old_on in checks4h:
                lvl, lvl_day = lv4[side]
                r = fn(c4h, lvl, wk0, wick_only=PW4H_WICK_ONLY)
                if not r or (now - pd.Timestamp(r["end"])).total_seconds() / 60 > PWL_MAX_ALERT_DELAY_MIN:
                    continue
                # ---- (12) الأسهم من 100$ إلى 350$: تنبيه واحد بالأسبوع + العقد ----
                if wkopt_in_range(r["close"]):
                    if wk_key in sent:
                        break
                    put = side == "high"
                    opt = None
                    try:
                        opt = wkopt_pick_option(t, r["close"], put)
                    except Exception as e:
                        log(f"سحب أسبوعي + عقد: {t}: العقد: {e}")
                    if opt is None and WKOPT_REQUIRE_CONTRACT:
                        log(f"سحب أسبوعي + عقد: {t}: فيه سحب {'مقاومة' if put else 'دعم'} بس ما فيه عقد بالشروط")
                        continue
                    sent.add(wk_key)
                    _append_line(GAP_SENT_FILE, wk_key)
                    hits += 1
                    send_telegram(with_gamma(wkopt_message(t, side, lvl, lvl_day, r, opt), t, r["close"]),
                                  kind="sweep", sym=t)
                    break
                key = f"{t}-{tag}-{wk0:%Y%m%d}"
                if old_on and key not in sent:
                    sent.add(key)
                    _append_line(GAP_SENT_FILE, key)
                    hits += 1
                    send_telegram(with_gamma(_pwl_message(t, side, lvl, lvl_day, r, frame="فريم 4 ساعات",
                                                          trade=True), t, r["close"]),
                                  kind="sweep", sym=t)
        except Exception as e:
            log(f"سحب دعم/مقاومة الأسبوع السابق: {t}: خطأ - {e}")
    free_memory()
    if hits:
        log(f"[{datetime.now():%H:%M}] سحب دعم/مقاومة اليوم السابق (ساعة) + الأسبوع السابق (4 ساعات): {hits} تنبيه")


# ================== (1ي-2) قائمة سحب قمة أمس وقاع أمس - إغلاق يومي ==================
def _pd1d_daily(df):
    """الشموع اليومية بفهرس تواريخ (بدون تكرار)."""
    d = df.dropna(subset=OHLC).copy()
    d.index = pd.Index([pd.Timestamp(i).date() for i in d.index])
    return d[~d.index.duplicated(keep="last")]


def check_pd1d(daily, day, wick_only=None):
    """شمعة يوم day مقابل اليوم اللي قبلها. يرجع [(الجهة، التفاصيل)] - "low" = سحب قاع أمس، "high" = سحب قمة أمس."""
    wick_only = PD1D_WICK_ONLY if wick_only is None else wick_only
    d = _pd1d_daily(daily)
    d = d[[x <= day for x in d.index]]
    if len(d) < 2 or d.index[-1] != day:
        return []
    cur, prev = d.iloc[-1], d.iloc[-2]
    o, h, l, c = (float(cur[k]) for k in OHLC)
    pdh, pdl = float(prev["High"]), float(prev["Low"])
    vol = None
    if "Volume" in d and len(d) > 5:
        past = d["Volume"].iloc[-21:-1].astype(float)
        if past.mean() > 0:
            vol = float(cur["Volume"]) / float(past.mean())
    base = {"open": o, "high": h, "low": l, "close": c, "pdh": pdh, "pdl": pdl,
            "day": day, "prev_day": d.index[-2], "rvol": vol}
    out = []
    if l < pdl < c and (not wick_only or o > pdl):
        out.append(("low", {**base, "level": pdl, "depth": (pdl - l) / pdl * 100}))
    if c < pdh < h and (not wick_only or o < pdh):
        out.append(("high", {**base, "level": pdh, "depth": (h - pdh) / pdh * 100}))
    return out


def _pd1d_line(t, side, r):
    c = r["close"]
    if side == "low":
        tgt = (f"🎯 قمة أمس {r['pdh']:.2f} ({(r['pdh'] / c - 1) * 100:+.1f}%)" if r["pdh"] > c
               else "قفل فوق قمة أمس كمان")
        stop = f"🛑 {r['low']:.2f} ({(r['low'] / c - 1) * 100:+.1f}%)"
        lvl = f"قاع أمس {r['level']:.2f} ← نزل {r['low']:.2f} (-{r['depth']:.2f}%)"
    else:
        tgt = (f"🎯 قاع أمس {r['pdl']:.2f} ({(r['pdl'] / c - 1) * 100:+.1f}%)" if r["pdl"] < c
               else "قفل تحت قاع أمس كمان")
        stop = f"🛑 {r['high']:.2f} ({(r['high'] / c - 1) * 100:+.1f}%)"
        lvl = f"قمة أمس {r['level']:.2f} ← طلع {r['high']:.2f} (+{r['depth']:.2f}%)"
    col = "🟢" if c > r["open"] else "🔴"
    rv = f" | فوليوم {r['rvol']:.1f}x" if r.get("rvol") else ""
    return f"${t}{sec_tag(t)}\nإغلاق {c:.2f} {col} | {lvl}{rv}\n{tgt} | {stop}"


def pd1d_last_closed_day(now=None):
    """آخر يوم شمعته اليومية مقفلة: اليوم لو بعد 4:15 العصر نيويورك، وإلا اليوم اللي قبله (أيام الأسبوع)."""
    now = now or pd.Timestamp.now(tz=NY)
    d = now.date()
    if now.weekday() >= 5 or (now.hour, now.minute) < (16, 15):
        d -= timedelta(days=1)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


def pd1d_scan(symbols, day=None):
    """يرجع (اليوم، [(الرمز، الجهة، التفاصيل)]، كم سهم فيه شمعة اليوم). اليوم None = آخر شمعة مقفلة عند ياهو."""
    want = day or pd1d_last_closed_day()
    data, ready, latest = {}, 0, None
    for t, df in download_batches(symbols, 100, period="3mo", interval="1d", prepost=False):
        try:
            d = _pd1d_daily(df)
            d = d[[x <= want for x in d.index]]
            if d.empty:
                continue
            data[t] = d
            latest = max(latest or d.index[-1], d.index[-1])
        except Exception as e:
            log(f"قائمة سحب أمس: {t}: {e}")
    if day is None and latest is not None:
        want = latest            # عطلة: ياخذ آخر يوم فيه تداول
    hits = []
    for t, d in data.items():
        if d.index[-1] == want:
            ready += 1
        try:
            for side, r in check_pd1d(d, want):
                if (side == "low" and PD1D_LOW) or (side == "high" and PD1D_HIGH):
                    hits.append((t, side, r))
        except Exception as e:
            log(f"قائمة سحب أمس: {t}: {e}")
    free_memory()
    return want, hits, ready


def pd1d_send(day, hits, prefix=""):
    """قائمة وحدة (تنقسم لو طويلة): الكول (سحب قاع أمس) ثم البوت (سحب قمة أمس)، الأعمق سحب أول."""
    lows = sorted([(t, r) for t, s, r in hits if s == "low"], key=lambda x: -x[1]["depth"])
    highs = sorted([(t, r) for t, s, r in hits if s == "high"], key=lambda x: -x[1]["depth"])
    head = (f"{prefix}📋 قائمة سحب سيولة أمس — إغلاق يومي {day:%Y-%m-%d}\n"
            f"الشمعة اليومية (9:30-4 نيويورك) سحبت قمة/قاع اليوم اللي قبلها وقفلت داخله"
            + (" (الافتتاح كمان داخله، الذيل بس اللي كسر)" if PD1D_WICK_ONLY else "")
            + f"\n🟢 سحب قاع أمس: {len(lows)} | 🔴 سحب قمة أمس: {len(highs)}")
    blocks = []
    if PD1D_LOW:
        blocks.append("🟢 سحب قاع أمس → كول (الهدف قمة أمس، الوقف تحت الذيل)")
        blocks += [f"{i}) " + _pd1d_line(t, "low", r) for i, (t, r) in enumerate(lows, 1)] or ["ما فيه"]
    if PD1D_HIGH:
        blocks.append("🔴 سحب قمة أمس → بوت (الهدف قاع أمس، الوقف فوق الذيل)")
        blocks += [f"{i}) " + _pd1d_line(t, "high", r) for i, (t, r) in enumerate(highs, 1)] or ["ما فيه"]
    chunks, cur = [], head
    for b in blocks:
        if len(cur) + len(b) + 2 > 3400:
            chunks.append(cur)
            cur = ""
        cur += ("\n\n" if cur else "") + b
    chunks.append(cur)
    for i, c in enumerate(chunks, 1):
        send_telegram(c + (f"\n\n({i}/{len(chunks)})" if len(chunks) > 1 else ""), kind="sweep")
        time.sleep(1)
    log(f"[{datetime.now():%H:%M}] قائمة سحب أمس ({day}): {len(lows)} قاع + {len(highs)} قمة")


_pd1d_running = threading.Event()
_pd1d_last_try = [0.0]


def _pd1d_state():
    try:
        with open(PD1D_STATE, encoding="utf-8") as f:
            return dict(x.split("=", 1) for x in f.read().split() if "=" in x)
    except FileNotFoundError:
        return {}


def _pd1d_save(st):
    try:
        with open(PD1D_STATE, "w", encoding="utf-8") as f:
            f.write("\n".join(f"{k}={v}" for k, v in st.items()) + "\n")
    except Exception as e:
        log(f"قائمة سحب أمس: ما قدرت أحفظ الحالة: {e}")


def pd1d_maybe_start(symbols):
    """أول ما يشتغل: قائمة آخر شمعة مقفلة (مرة وحدة). وبعدها كل يوم سوق بعد الإغلاق - بخيط لحاله."""
    if not ENABLE_PD1D or _pd1d_running.is_set():
        return
    st = _pd1d_state()
    now = pd.Timestamp.now(tz=NY)
    today = str(now.date())
    start_due = PD1D_START_LIST and st.get("start") != PD1D_START_ID
    daily_due = (now.weekday() < 5 and PD1D_SCAN_AFTER_NY <= (now.hour, now.minute) < PD1D_SCAN_UNTIL_NY
                 and st.get("day") != today)
    if not (start_due or daily_due) or time.time() - _pd1d_last_try[0] < PD1D_RETRY_MIN * 60:
        return
    _pd1d_last_try[0] = time.time()
    _pd1d_running.set()

    def run():
        try:
            if daily_due:
                day, hits, ready = pd1d_scan(symbols, now.date())
                if ready < max(1, len(symbols) // 2):     # ياهو للحين ما حدّث شمعة اليوم
                    log(f"قائمة سحب أمس: شمعة اليوم ناقصة ({ready} من {len(symbols)}) - أعيد بعد {PD1D_RETRY_MIN} دقايق")
                    return
                pd1d_send(day, hits)
                st["day"] = today
                st["start"] = PD1D_START_ID              # ما يحتاج قائمة البداية بعدها
            else:
                day, hits, _ = pd1d_scan(symbols)
                pd1d_send(day, hits, prefix="🆕 أول قائمة (آخر شمعة يومية مقفلة)\n")
                st["start"] = PD1D_START_ID
            _pd1d_save(st)
        except Exception as e:
            log(f"قائمة سحب أمس: خطأ - {e}")
        finally:
            _pd1d_running.clear()

    threading.Thread(target=run, daemon=True, name="pd1d").start()


def pd1d_self_test():
    """python short_bot.py --pd1dtest — يجرب الشرط على شموع وهمية بدون نت."""
    idx = pd.to_datetime(["2026-11-12", "2026-11-13", "2026-11-16"])
    def mk(o, h, l, c):
        return pd.DataFrame({"Open": [100, 100, o], "High": [101, 102, h], "Low": [99, 98, l],
                             "Close": [100, 100, c], "Volume": [1e6, 1e6, 2e6]}, index=idx)
    day = datetime(2026, 11, 16).date()
    r = check_pd1d(mk(99, 100.5, 97.5, 99.5), day)
    assert [s for s, _ in r] == ["low"] and r[0][1]["level"] == 98, r
    print("✅ سحب قاع أمس (98): نزل 97.5 وقفل 99.5")
    r = check_pd1d(mk(101, 102.8, 100.5, 101.2), day)
    assert [s for s, _ in r] == ["high"] and r[0][1]["level"] == 102, r
    print("✅ سحب قمة أمس (102): طلع 102.8 وقفل 101.2")
    assert check_pd1d(mk(99, 100, 97.5, 97.9), day) == []
    print("✅ قفل تحت قاع أمس = ما ينحسب")
    assert check_pd1d(mk(97.8, 100, 97.5, 99), day) == [] and check_pd1d(mk(97.8, 100, 97.5, 99), day, False)
    print("✅ افتتح تحت القاع: ما ينحسب بالذيل بس، وينحسب لو PD1D_WICK_ONLY = False")
    assert check_pd1d(mk(99, 100.5, 97.5, 99.5), datetime(2026, 11, 17).date()) == []
    print("✅ ما فيه شمعة لليوم المطلوب = ما ينحسب")
    assert pd1d_last_closed_day(pd.Timestamp("2026-11-17 00:31", tz=NY)) == day
    assert pd1d_last_closed_day(pd.Timestamp("2026-11-17 16:20", tz=NY)) == datetime(2026, 11, 17).date()
    assert pd1d_last_closed_day(pd.Timestamp("2026-11-16 09:00", tz=NY)) == datetime(2026, 11, 13).date()
    print("✅ آخر شمعة مقفلة: قبل 4:15 = أمس (والاثنين = الجمعة)")
    hits = [("AAA", *check_pd1d(mk(99, 100.5, 97.5, 99.5), day)[0]),
            ("BBB", *check_pd1d(mk(101, 102.8, 100.5, 101.2), day)[0])]
    global SHOW_SECTOR
    saved, SHOW_SECTOR = SHOW_SECTOR, False
    try:
        pd1d_send(day, hits, prefix="🧪 ")
    finally:
        SHOW_SECTOR = saved
    print("PD1D TEST OK")


# ================== (1) الإنفيرجن IFVG - فريم ساعة و4 ساعات ==================
def check_ifvg(c):
    """آخر 4 شموع مقفلة بالاتجاهين. يرجع تفاصيل النموذج لو تحقق، وإلا None.
    لون الشموع ما يهم - المهم الجاب بين ذيل الأولى والثالثة، والثانية تغطي الجاب كامل،
    والرابعة تقفل وراه."""
    if len(c) < 4:
        return None
    c1, c2, c3, c4 = (c.iloc[i] for i in (-4, -3, -2, -1))
    info = {"price": float(c4["Close"]), "open": float(c4["Open"]), "candle_time": c.index[-1],
            "end": c4["end"] if "end" in c else c.index[-1], "candles": c.iloc[-4:]}
    # 🟢 صعودي: قاع الأولى فوق قمة الثالثة، والرابعة تقفل فوق أعلى الجاب
    if c1["Low"] > c3["High"]:
        bottom, top = float(c3["High"]), float(c1["Low"])
        covered = c2["High"] >= top and c2["Low"] <= bottom
        if (covered or not IFVG_REQUIRE_MIDDLE_COVER) and c4["Close"] > top:
            return {"side": "bull", "gap_bottom": bottom, "gap_top": top, **info}
    # 🔴 هبوطي: قمة الأولى تحت قاع الثالثة، والرابعة تقفل تحت أسفل الجاب
    if c1["High"] < c3["Low"]:
        bottom, top = float(c1["High"]), float(c3["Low"])
        covered = c2["High"] >= top and c2["Low"] <= bottom
        if (covered or not IFVG_REQUIRE_MIDDLE_COVER) and c4["Close"] < bottom:
            return {"side": "bear", "gap_bottom": bottom, "gap_top": top, **info}
    return None


def _ifvg_message(t, res, frame):
    lo, hi, px = (round(float(res[k]), 2) for k in ("gap_bottom", "gap_top", "price"))
    if res["side"] == "bull":
        head, line = f"🟢 Inversion Gap - {frame}", f"الشمعة قفلت فوق أعلى الـ IFVG ({hi})"
    else:
        head, line = f"🔴 Inversion Gap - {frame}", f"الشمعة قفلت تحت أسفل الـ IFVG ({lo})"
    closed_at = pd.Timestamp(res["end"]).tz_convert(LOCAL_TZ)
    msg = (f"{head}\n"
           f"السهم: ${t}\n"
           f"IFVG: {lo} ← {hi}  (حجمه {hi - lo:.2f}$)\n"
           f"{line}\n"
           f"سعر الإغلاق: {px}\n"
           f"وقت الإغلاق: {closed_at:%H:%M} (توقيتك)")
    cs = res.get("candles")
    if IFVG_SHOW_CANDLES and cs is not None:
        rows = []
        for k, (ts, r) in enumerate(cs.iterrows(), 1):
            lt = pd.Timestamp(ts).tz_convert(LOCAL_TZ)
            col = "🟢" if r["Close"] > r["Open"] else "🔴"
            rows.append(f"{k}) {lt:%m/%d %H:%M} {col} أعلى {r['High']:.2f} | أقل {r['Low']:.2f}")
        msg += "\nالشموع (بتوقيتك):\n" + "\n".join(rows)
    return msg


def ifvg_scan_due(now, last_run):
    """بعد إغلاق كل ساعة بدقيقة (وإعادة بعد 5 و12 دقيقة). يرجع وقت الجولة لو جا وقتها."""
    boundary = now.floor("h")
    for off in sorted(GAP_SCAN_AFTER_CLOSE_MIN, reverse=True):
        slot = boundary + pd.Timedelta(minutes=off)
        if now >= slot:
            return slot if (last_run is None or last_run < slot) else None
    return None


def scan_ifvg(symbols, sent, now=None):
    """(1) IFVG فريم ساعة و4 ساعات على الجلسة الممتدة (بدون الليلي)."""
    now = now or pd.Timestamp.now(tz=NY)
    frames = [(ENABLE_IFVG_4H, 240, "ifvg4h", "فريم 4 ساعات", IFVG_4H_MIN_SIZE),
              (ENABLE_IFVG_1H, 60, "ifvg1h", "فريم ساعة", IFVG_1H_MIN_SIZE)]
    frames = [f for f in frames if f[0]]
    if not frames:
        return
    hits = 0
    for t, df in download_batches(symbols, 100, period="7d", interval=f"{GAP_BASE_MIN}m", prepost=True):
        try:
            df = to_ny(df)[OHLC]
            if df.empty or float(df["Close"].iloc[-1]) < IFVG_MIN_PRICE:
                continue
            last_bar = df.index.max()
            for _, minutes, tag, label, min_size in frames:
                res = check_ifvg(only_closed(to_frame(df, minutes, overnight=False), last_bar, now))
                if not res or round(res["gap_top"] - res["gap_bottom"], 2) < min_size:
                    continue
                if (now - pd.Timestamp(res["end"])).total_seconds() / 60 > IFVG_MAX_ALERT_DELAY_MIN:
                    continue                    # شمعة قديمة، مو إغلاق جديد
                key = f"{t}-{tag}-{res['side']}-{res['candle_time']}"
                if key in sent:
                    continue
                sent.add(key)
                _append_line(GAP_SENT_FILE, key)
                hits += 1
                msg = _ifvg_message(t, res, label)
                if IFVG_GAMMA:
                    msg = with_gamma(msg, t, res["price"])
                send_telegram(msg, kind="gap", sym=t)
        except Exception as e:
            log(f"الإنفيرجن: {t}: خطأ - {e}")
    free_memory()
    log(f"[{datetime.now():%H:%M}] الإنفيرجن (ساعة + 4 ساعات): خلص الفحص - {hits} تنبيه جديد")


def ifvg_self_test():
    """python short_bot.py --ifvgtest — يجرب النموذج على شموع وهمية بدون نت."""
    # (فتح، أعلى، أقل، إغلاق) لكل شمعة 4 ساعات (نفس مثال NVDA في gap_scanner)
    times = ("2026-09-25 08:00", "2026-09-25 12:00", "2026-09-25 16:00", "2026-09-28 04:00")
    prices = [(225.00, 225.40, 224.87, 224.95),   # الأولى - قاعها 224.87
              (225.05, 225.80, 223.75, 223.80),   # الثانية تغطي الجاب
              (223.80, 224.33, 223.00, 223.10),   # الثالثة - قمتها 224.33
              (223.50, 228.30, 222.90, 228.08)]   # الرابعة - تقفل فوق 224.87
    rows = []
    for s, (o, h, l, c) in zip(times, prices):
        s = pd.Timestamp(s, tz=NY)
        path = [o + (c - o) * k / 15 for k in range(16)]
        for k in range(16):
            op = path[k - 1] if k else o
            rows.append((s + pd.Timedelta(minutes=15 * k), op,
                         h if k == 6 else max(op, path[k]), l if k == 10 else min(op, path[k]), path[k]))
    df = pd.DataFrame(rows, columns=["t"] + OHLC).set_index("t")
    for label, now, want in (("قبل إغلاق الرابعة", "2026-09-28 07:59", False),
                             ("بعد الإغلاق بدقيقة", "2026-09-28 08:01", True)):
        now = pd.Timestamp(now, tz=NY)
        part = df[df.index <= now - pd.Timedelta(minutes=15)]
        c = only_closed(to_frame(part, 240, overnight=False), part.index.max(), now)
        res = check_ifvg(c)
        assert bool(res) == want, (label, res)
        print(f"✅ {label}: " + ("تنبيه صعودي" if res else "ما فيه تنبيه"))
        if res:
            assert res["side"] == "bull" and res["gap_top"] == 224.87 and res["gap_bottom"] == 224.33
            print(_ifvg_message("NVDA", res, "فريم 4 ساعات"))
    # هبوطي: نفس الأرقام مقلوبة
    idx = pd.date_range("2026-10-13 04:00", periods=4, freq="4h", tz=NY)
    bear = pd.DataFrame({"Open": [100, 100.2, 101.3, 101.5], "High": [100.5, 101.6, 102, 101.8],
                         "Low": [99.8, 100.1, 101.1, 99.5], "Close": [100.2, 101.4, 101.6, 99.9]}, index=idx)
    bear["end"] = bear.index + pd.Timedelta(hours=4)
    r = check_ifvg(bear)
    assert r and r["side"] == "bear" and r["gap_bottom"] == 100.5 and r["gap_top"] == 101.1, r
    print("✅ هبوطي: الرابعة قفلت تحت قمة الأولى (100.5)")
    nocov = bear.copy(); nocov.iloc[1, nocov.columns.get_loc("High")] = 100.9
    assert check_ifvg(nocov) is None
    print("✅ الثانية ما غطت الجاب = ما فيه تنبيه")
    c4 = to_frame(pd.DataFrame({"Open": 1.0, "High": 1.0, "Low": 1.0, "Close": 1.0},
                               index=pd.date_range("2026-10-13 00:00", "2026-10-13 23:45",
                                                   freq="15min", tz=NY)), 240, overnight=False)
    assert [f"{x:%H}" for x in c4.index] == ["04", "08", "12", "16"]
    c1 = to_frame(pd.DataFrame({"Open": 1.0, "High": 1.0, "Low": 1.0, "Close": 1.0},
                               index=pd.date_range("2026-10-13 00:00", "2026-10-13 23:45",
                                                   freq="15min", tz=NY)), 60, overnight=False)
    assert f"{c1.index[0]:%H}" == "04" and f"{c1.index[-1]:%H}" == "19" and len(c1) == 16
    print("✅ شموع 4 ساعات 4-8-12-4 وشموع الساعة من 4 الفجر لين 8 بالليل (بدون الليلي)")
    assert ifvg_scan_due(pd.Timestamp("2026-10-13 10:00:30", tz=NY), None) is None
    s1 = ifvg_scan_due(pd.Timestamp("2026-10-13 10:01:10", tz=NY), None)
    assert s1 is not None and ifvg_scan_due(pd.Timestamp("2026-10-13 10:03", tz=NY), s1) is None
    assert ifvg_scan_due(pd.Timestamp("2026-10-13 10:05", tz=NY), s1) is not None
    print("✅ وقت الفحص: بعد الساعة بدقيقة، ويعيد بعد 5 و12 دقيقة")
    print("IFVG TEST OK")


# ================== (12) سحب السيولة الأسبوعي (فريم 4 ساعات) + العقد ==================
def wkopt_in_range(price):
    return ENABLE_WKOPT and WKOPT_MIN_PRICE <= float(price) <= WKOPT_MAX_PRICE


def wkopt_pick_option(t, spot, put):
    """كول (سحب دعم) أو بوت (سحب مقاومة): أكثر من 10 أيام، حجم فوق 500، عقود مفتوحة فوق 1000،
    دلتا فوق 0.12. يختار أقرب انتهاء فيه عقد بالشروط، وفيه الأرخص (أقل دلتا فوق الحد).
    يرجع (العقد، الحجم، العقود المفتوحة) أو None."""
    today = pd.Timestamp.now(tz=NY).date()
    d1 = today + timedelta(days=WKOPT_OPT_MIN_DTE + 1)        # أكثر من 10 أيام
    d2 = today + timedelta(days=WKOPT_OPT_MAX_DTE)
    ok = []
    for x in _pdr1h_option_rows(t, put, spot, d1, d2):
        exp, k, delta, bid, ask, sym, iv, gamma, vol, src = x
        if delta is None or abs(delta) <= WKOPT_OPT_MIN_DELTA or not ask:
            continue
        if (vol or 0) <= WKOPT_OPT_MIN_VOLUME:
            continue
        if (exp - today).days <= WKOPT_OPT_MIN_DTE:
            continue
        ok.append(x)
    for exp in sorted({x[0] for x in ok}):                     # أقرب انتهاء أول
        for x in sorted((x for x in ok if x[0] == exp), key=lambda x: abs(x[2])):
            oi = _opt_open_interest(t, x) or 0
            if oi > WKOPT_OPT_MIN_OI:
                return x, x[8], oi
    return None


def wkopt_message(t, side, lvl, lvl_day, r, opt):
    put = side == "high"
    kind = "بوت" if put else "كول"
    head = "🔴 بوت — سحب سيولة مقاومة أسبوعية" if put else "🟢 كول — سحب سيولة دعم أسبوعي"
    lines = [head, _pwl_message(t, side, lvl, lvl_day, r, frame="فريم 4 ساعات", trade=True), ""]
    if opt:
        c, vol, oi = opt
        exp, k, delta, bid, ask, sym, iv = c[:7]
        days = (exp - pd.Timestamp.now(tz=NY).date()).days
        mid = (bid + ask) / 2 if bid else ask
        lines += [f"📄 العقد: {t} {kind} {k:g} — انتهاء {exp:%Y-%m-%d} ({days} يوم)",
                  f"السعر الحين: {mid:.2f}$ (العقد كامل {mid * 100:,.0f}$) | بيد {bid or 0:.2f} / أسك {ask:.2f}",
                  f"الدلتا: {delta:.4f}" + (f" | IV: {iv * 100:.0f}%" if iv else ""),
                  f"حجم التداول: {int(vol):,} | العقود المفتوحة: {int(oi):,}"]
    else:
        lines.append(f"📄 العقد: ما لقيت {kind} بالشروط")
    lines.append(f"(شروط العقد: أكثر من {WKOPT_OPT_MIN_DTE} أيام، حجم فوق {WKOPT_OPT_MIN_VOLUME}، "
                 f"عقود مفتوحة فوق {WKOPT_OPT_MIN_OI:,}، دلتا فوق {WKOPT_OPT_MIN_DELTA:.4f})")
    lines += ["", "⚠️ محتوى تعليمي — تداول وهمي، ليست توصية للشراء."]
    return "\n".join(lines)


WKOPT_TEST_ID = "1"   # رسالة تجريبية مرة وحدة بعد الرفع — غيّر الرقم لو تبي وحدة ثانية


def wkopt_send_test_once():
    """يرسل تنبيه تجريبي للقسم (12) مرة وحدة (يتذكرها في /data عشان ما تتكرر مع كل تشغيل)."""
    if not ENABLE_WKOPT:
        return
    marker = os.path.join(os.environ.get("RAILWAY_VOLUME_MOUNT_PATH", "."), "wkopt_test_sent.txt")
    try:
        with open(marker, encoding="utf-8") as f:
            if f.read().strip() == WKOPT_TEST_ID:
                return
    except Exception:
        pass
    now = pd.Timestamp.now(tz=NY)
    lvl_day = (now - pd.Timedelta(days=6)).date()
    exp = (now + pd.Timedelta(days=12)).date()
    r_low = {"open": 181.2, "high": 182.6, "low": 178.9, "close": 181.8, "depth": 0.72,
             "start": now.floor("h"), "end": now, "closes_beyond": 0, "first_touch": True}
    call = ((exp, 185.0, 0.3120, 2.35, 2.45, "TEST", 0.36, 0.03, 1840, "test"), 1840, 6250)
    r_high = {"open": 247.0, "high": 251.9, "low": 246.1, "close": 247.6, "depth": 0.85,
              "start": now.floor("h"), "end": now, "closes_beyond": 0, "first_touch": True}
    put = ((exp, 245.0, -0.2870, 3.10, 3.25, "TEST", 0.41, 0.03, 960, "test"), 960, 3400)
    note = "🧪 رسالة تجريبية - هذا مو تنبيه حقيقي (السهم والأرقام وهمية)\n\n"
    send_telegram(note + wkopt_message("TEST", "low", 180.20, lvl_day, r_low, call), kind="sweep")
    time.sleep(1)
    send_telegram(note + wkopt_message("TEST", "high", 249.80, lvl_day, r_high, put)
                  + "\n\nلو وصلتك الرسالتين، تنبيهات القسم الحقيقية بتوصل لنفس المكان.", kind="sweep")
    try:
        with open(marker, "w", encoding="utf-8") as f:
            f.write(WKOPT_TEST_ID)
    except Exception as e:
        log(f"سحب أسبوعي + عقد: ما قدرت أحفظ علامة الرسالة التجريبية: {e}")


def wkopt_self_test():
    """python short_bot.py --wkopttest — يجرب اختيار العقد والرسالة بدون نت."""
    global _pdr1h_option_rows, _opt_open_interest
    today = pd.Timestamp.now(tz=NY).date()
    e9, e12, e19 = (today + timedelta(days=d) for d in (9, 12, 19))
    fake_rows = [   # (انتهاء، سترايك، دلتا، bid، ask، رمز، IV، جاما، حجم، مصدر)
        (e9, 200, -0.30, 2.0, 2.1, "A", 0.4, 0.02, 5000, "t"),    # 9 أيام = يترفض
        (e12, 190, -0.10, 0.5, 0.6, "B", 0.4, 0.02, 5000, "t"),   # دلتا 0.10 = يترفض
        (e12, 195, -0.18, 1.0, 1.1, "C", 0.4, 0.02, 400, "t"),    # حجم 400 = يترفض
        (e12, 197, -0.22, 1.5, 1.6, "D", 0.4, 0.02, 900, "t"),    # عقود مفتوحة 800 = يترفض
        (e12, 198, -0.27, 1.9, 2.0, "E", 0.4, 0.02, 1200, "t"),   # ✅
        (e19, 195, -0.20, 2.2, 2.4, "F", 0.4, 0.02, 3000, "t"),   # انتهاء أبعد
    ]
    oi = {"A": 9000, "B": 9000, "C": 9000, "D": 800, "E": 1500, "F": 9000}
    saved = (_pdr1h_option_rows, _opt_open_interest)
    _pdr1h_option_rows = lambda t, put, spot, d1, d2: [x for x in fake_rows if d1 <= x[0] <= d2]
    _opt_open_interest = lambda t, x: oi[x[5]]
    try:
        got = wkopt_pick_option("TEST", 200, True)
        assert got and got[0][5] == "E" and got[2] == 1500, got
        print("✅ العقد: أكثر من 10 أيام + حجم فوق 500 + مفتوحة فوق 1000 + دلتا فوق 0.12 → E")
        assert wkopt_in_range(100) and wkopt_in_range(350) and not wkopt_in_range(351) and not wkopt_in_range(99)
        print("✅ نطاق السعر 100$-350$")
        r = {"open": 201.0, "high": 203.5, "low": 199.8, "close": 200.4, "depth": 0.9,
             "start": pd.Timestamp.now(tz=NY).floor("h"), "end": pd.Timestamp.now(tz=NY),
             "closes_beyond": 0, "first_touch": True}
        print()
        print(wkopt_message("TEST", "high", 201.7, today, r, got))
    finally:
        _pdr1h_option_rows, _opt_open_interest = saved


def pw4h_now(symbols, send=False):
    """تجربة حقيقية لفريم 4 ساعات: يطلع كل شموع السحب (دعم ومقاومة) من بداية هالأسبوع
    على قائمة المراقبة، بدون شرط وقت التنبيه وبدون ملف المرسل. send=True يرسلها تيليجرام."""
    now = pd.Timestamp.now(tz=NY)
    wk0 = _week_start(now)                      # بالويكند = الأسبوع اللي خلص (الاثنين اللي راح)
    print(f"تجربة سحب سيولة الأسبوع السابق - 4 ساعات | الأسبوع من {wk0:%Y-%m-%d} | {len(symbols)} رمز")
    found = 0
    for t, df in download_batches(symbols, 100, period="20d", interval=f"{GAP_BASE_MIN}m", prepost=True):
        try:
            df = to_ny(df)[OHLC]
            lv4 = prev_week_ext_levels(df, wk0)
            if not lv4:
                continue
            c4h = only_closed(to_frame(df, 240, overnight=False), df.index.max(), now)
            c4h = c4h[(c4h.index >= wk0) & (c4h.index < wk0 + pd.Timedelta(days=7))]
            for i in range(len(c4h)):
                part = c4h.iloc[:i + 1]
                for side, fn in (("low", check_pwl_1h), ("high", check_pwh_1h)):
                    lvl, lvl_day = lv4[side]
                    r = fn(part, lvl, wk0, wick_only=PW4H_WICK_ONLY)
                    if r:
                        found += 1
                        msg = with_gamma(_pwl_message(t, side, lvl, lvl_day, r, frame="فريم 4 ساعات",
                                                      trade=True), t, r["close"])
                        print(msg + "\n")
                        if send:
                            send_telegram("🧪 تجربة\n" + msg, kind="sweep", sym=t)
        except Exception as e:
            print(f"{t}: خطأ - {e}")
    print(f"المجموع: {found} شمعة سحب")


def pwl_self_test():
    """يجرب (1ك) الدعم والمقاومة على بيانات مصنوعة بدون نت."""
    ny = ZoneInfo(NY)
    # يومي: الأسبوع السابق قاعه 100 يوم الأربعاء، وقمته 106 يوم الجمعة
    days = pd.to_datetime(["2026-10-05", "2026-10-06", "2026-10-07", "2026-10-08", "2026-10-09",
                           "2026-10-12"])
    daily = pd.DataFrame({"Open": [105, 104, 102, 103, 104, 103], "High": [105.5, 105, 104, 105, 106, 107],
                          "Low": [103, 102, 100, 101, 102, 99], "Close": [104, 103, 101, 104, 105, 102]},
                         index=days)
    pw0, wk = datetime(2026, 10, 5).date(), datetime(2026, 10, 12).date()
    lvl, day = prev_week_low(daily, pw0, wk)
    assert lvl == 100 and str(day) == "2026-10-07", (lvl, day)
    hi, hday = prev_week_high(daily, pw0, wk)
    assert hi == 106 and str(hday) == "2026-10-09", (hi, hday)
    print(f"✅ قاع الأسبوع السابق {lvl} ({day}) | قمته {hi} ({hday}) - شموع هالأسبوع ما دخلت")

    wk0 = pd.Timestamp("2026-10-12", tz=ny)
    idx = pd.to_datetime(["2026-10-13 10:00", "2026-10-13 11:00", "2026-10-13 12:00"]).tz_localize(ny)

    def frame(o, h, l, c):
        f = pd.DataFrame({"Open": o, "High": h, "Low": l, "Close": c}, index=idx)
        f["end"] = f.index + pd.Timedelta(hours=1)
        return f

    # ---- الدعم ----
    ok = frame([102, 101, 100.5], [102.5, 101.5, 101.8], [101, 100.2, 99.4], [101.2, 100.6, 101.5])
    r = check_pwl_1h(ok, lvl, wk0)
    assert r and r["first_touch"], r
    print(f"✅ دعم: نزل لـ {r['low']} وقفل {r['close']} فوق {lvl} (أول لمس)")
    bad = ok.copy(); bad.iloc[-1, bad.columns.get_loc("Close")] = 99.8
    assert check_pwl_1h(bad, lvl, wk0) is None
    nos = ok.copy(); nos.iloc[-1, nos.columns.get_loc("Low")] = 100.1
    assert check_pwl_1h(nos, lvl, wk0) is None
    assert check_pwl_1h(ok, lvl, pd.Timestamp("2026-10-19", tz=ny)) is None
    print("✅ دعم: قفل تحته / ما نزل تحته / أسبوع قديم = ما فيه تنبيه")

    # ---- المقاومة ----
    ok = frame([104, 105, 105.5], [104.8, 105.8, 106.7], [103.5, 104.5, 105], [104.9, 105.4, 105.2])
    r = check_pwh_1h(ok, hi, wk0)
    assert r and r["first_touch"], r
    print(f"✅ مقاومة: طلع لـ {r['high']} وقفل {r['close']} تحت {hi} (أول لمس)")
    bad = ok.copy(); bad.iloc[-1, bad.columns.get_loc("Close")] = 106.2
    assert check_pwh_1h(bad, hi, wk0) is None
    nos = ok.copy(); nos.iloc[-1, nos.columns.get_loc("High")] = 105.9
    assert check_pwh_1h(nos, hi, wk0) is None
    assert check_pwh_1h(ok, hi, pd.Timestamp("2026-10-19", tz=ny)) is None
    print("✅ مقاومة: قفل فوقها / ما طلع فوقها / أسبوع قديم = ما فيه تنبيه")

    # ---- 4 ساعات: الذيل بس (الافتتاح والإغلاق بجهة المستوى) ----
    assert check_pwh_1h(ok, hi, wk0, wick_only=True)          # افتتح 105.5 تحت 106 = ذيل بس
    body = ok.copy(); body.iloc[-1, body.columns.get_loc("Open")] = 106.3
    assert check_pwh_1h(body, hi, wk0) and check_pwh_1h(body, hi, wk0, wick_only=True) is None
    sup = frame([102, 101, 100.5], [102.5, 101.5, 101.8], [101, 100.2, 99.4], [101.2, 100.6, 101.5])
    assert check_pwl_1h(sup, lvl, wk0, wick_only=True)
    sbody = sup.copy(); sbody.iloc[-1, sbody.columns.get_loc("Open")] = 99.7
    assert check_pwl_1h(sbody, lvl, wk0) and check_pwl_1h(sbody, lvl, wk0, wick_only=True) is None
    print("✅ 4 ساعات: الجسم دخل تحت الدعم / فوق المقاومة = ما فيه تنبيه، الذيل بس = تنبيه")

    # ---- 4 ساعات بدون الجلسة الليلية ----
    m15 = pd.date_range("2026-10-13 00:00", "2026-10-13 23:45", freq="15min", tz=ny)
    raw = pd.DataFrame({"Open": 100.0, "High": 101.0, "Low": 99.0, "Close": 100.0}, index=m15)
    c4 = to_frame(raw, 240, overnight=False)
    hrs = [f"{x:%H:%M}" for x in c4.index]
    assert hrs == ["04:00", "08:00", "12:00", "16:00"], hrs
    print(f"✅ شموع 4 ساعات بدون الليلي (نيويورك): {', '.join(hrs)}")

    # ---- مستويات الأسبوع السابق: بري + ماركت + أفتر، والليلي ما يدخل ----
    m15w = pd.date_range("2026-10-05 00:00", "2026-10-13 23:45", freq="15min", tz=ny)
    w = pd.DataFrame({"Open": 100.0, "High": 101.0, "Low": 99.0, "Close": 100.0}, index=m15w)
    w.loc[pd.Timestamp("2026-10-06 05:00", tz=ny), ["High", "Low"]] = [101.5, 97.0]   # بري = يدخل
    w.loc[pd.Timestamp("2026-10-07 18:00", tz=ny), ["High", "Low"]] = [104.0, 99.5]   # أفتر = يدخل
    w.loc[pd.Timestamp("2026-10-08 22:00", tz=ny), ["High", "Low"]] = [110.0, 90.0]   # ليلي = ما يدخل
    w.loc[pd.Timestamp("2026-10-13 10:00", tz=ny), ["High", "Low"]] = [120.0, 80.0]   # هالأسبوع = ما يدخل
    ev = prev_week_ext_levels(w, wk0)
    assert ev["low"] == (97.0, datetime(2026, 10, 6).date()), ev
    assert ev["high"] == (104.0, datetime(2026, 10, 7).date()), ev
    print(f"✅ الأسبوع السابق (بري + أفتر بدون الليلي): قاع {ev['low'][0]} | قمة {ev['high'][0]}")

    # ---- (1ي) اليوم السابق - فريم ساعة: الاثنين يقرا الجمعة، والليلي ما يدخل ----
    m15d = pd.date_range("2026-11-13 00:00", "2026-11-16 23:45", freq="15min", tz=ny)
    d = pd.DataFrame({"Open": 100.0, "High": 100.5, "Low": 99.5, "Close": 100.0}, index=m15d)
    d.loc[pd.Timestamp("2026-11-13 06:00", tz=ny), "Low"] = 98.0      # بري الجمعة = يدخل
    d.loc[pd.Timestamp("2026-11-13 17:00", tz=ny), "High"] = 102.0    # أفتر الجمعة = يدخل
    d.loc[pd.Timestamp("2026-11-13 21:00", tz=ny), "Low"] = 90.0      # ليلي = ما يدخل
    pdl = prev_day_ext_levels(d, datetime(2026, 11, 16).date())
    assert pdl["low"] == (98.0, datetime(2026, 11, 13).date()) and pdl["high"][0] == 102.0, pdl
    print(f"✅ اليوم السابق (الاثنين ← الجمعة، بدون الليلي): قاع {pdl['low'][0]} | قمة {pdl['high'][0]}")
    # شمعة ساعة 10:00 الاثنين: افتتاح 98.6، ذيل 97.6، إغلاق 98.8 = سحب دعم بالذيل بس
    mon = d[d.index.date == datetime(2026, 11, 16).date()].copy()
    mon[OHLC] = 99.0
    for ts, o, h, l, c in (("10:00", 98.6, 98.7, 98.5, 98.6), ("10:15", 98.6, 98.7, 97.6, 98.2),
                           ("10:30", 98.2, 98.5, 98.1, 98.4), ("10:45", 98.4, 98.9, 98.3, 98.8)):
        mon.loc[pd.Timestamp(f"2026-11-16 {ts}", tz=ny), OHLC] = [o, h, l, c]
    c1 = to_frame(mon[mon.index < pd.Timestamp("2026-11-16 11:00", tz=ny)], 60, overnight=False)
    day0 = pd.Timestamp("2026-11-16", tz=ny)
    r1 = check_pwl_1h(c1, 98.0, day0, wick_only=True)
    assert r1 and r1["low"] == 97.6 and r1["close"] == 98.8, r1
    body = c1.copy(); body.iloc[-1, body.columns.get_loc("Open")] = 97.9
    assert check_pwl_1h(body, 98.0, day0, wick_only=True) is None
    shut = c1.copy(); shut.iloc[-1, shut.columns.get_loc("Close")] = 97.9
    assert check_pwl_1h(shut, 98.0, day0, wick_only=True) is None
    print("✅ اليوم السابق ساعة: ذيل بس = تنبيه | افتتح أو قفل تحت الدعم = ما فيه تنبيه")
    print()
    print(_pwl_message("TEST", "low", 98.0, pdl["low"][1], r1, frame="فريم ساعة", trade=True,
                       period="اليوم السابق", scope="اليوم"))
    print()
    print(_pwl_message("TEST", "high", hi, hday, r))


# ================== العقود: الدلتا والسعر واختيار العقد (يستخدمها سحب الجمعة/الاثنين) ==================


def _bs_delta(spot, strike, years, iv, put):
    """دلتا بلاك شولز (لو المصدر ما أعطى الدلتا)."""
    if not (spot and strike and years > 0 and iv and iv > 0.01):
        return None
    d1 = (math.log(spot / strike) + (PDR_OPT_RATE + iv * iv / 2) * years) / (iv * math.sqrt(years))
    n = 0.5 * (1 + math.erf(d1 / math.sqrt(2)))
    return n - 1 if put else n


def _bs_price(spot, strike, years, iv, put):
    """سعر بلاك شولز للعقد."""
    if not (spot and strike and years > 0 and iv and iv > 0.01):
        return None
    sq = iv * math.sqrt(years)
    d1 = (math.log(spot / strike) + (PDR_OPT_RATE + iv * iv / 2) * years) / sq
    d2 = d1 - sq
    N = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2)))
    disc = strike * math.exp(-PDR_OPT_RATE * years)
    return disc * N(-d2) - spot * N(-d1) if put else spot * N(d1) - disc * N(d2)


def _opt_years(exp):
    end = pd.Timestamp(exp).tz_localize(NY) + pd.Timedelta(hours=16)
    return max((end - pd.Timestamp.now(tz=NY)).total_seconds(), 60) / (365 * 24 * 3600)


def _pdr1h_option_rows(t, put, spot, d1, d2):
    """كل العقود بين التاريخين: (انتهاء، سترايك، دلتا، bid، ask، رمز، IV، جاما، حجم التداول، المصدر)."""
    import re
    rows = []
    if ALPACA_KEY and ALPACA_SECRET:
        try:
            token = None
            for _ in range(10):
                p = {"feed": "indicative", "type": "put" if put else "call", "limit": 1000,
                     "expiration_date_gte": d1.isoformat(), "expiration_date_lte": d2.isoformat()}
                if token:
                    p["page_token"] = token
                _alpaca_wait()
                js = _alpaca_data_get(f"/v1beta1/options/snapshots/{t}", p)
                for sym, sn in (js.get("snapshots") or {}).items():
                    m = re.match(r"^(.+?)(\d{6})([CP])(\d{8})$", sym)
                    if not m:
                        continue
                    exp = datetime.strptime(m.group(2), "%y%m%d").date()
                    k = int(m.group(4)) / 1000
                    q, g = sn.get("latestQuote") or {}, sn.get("greeks") or {}
                    iv = sn.get("impliedVolatility")
                    delta = g.get("delta")
                    if delta is None:
                        delta = _bs_delta(spot, k, _opt_years(exp), iv, put)
                    vol = (sn.get("dailyBar") or {}).get("v") or 0
                    rows.append((exp, k, delta, q.get("bp"), q.get("ap"), sym, iv, g.get("gamma"), vol, "Alpaca"))
                token = js.get("next_page_token")
                if not token:
                    break
        except Exception as e:
            log(f"عقد الساعة: {t}: Alpaca: {e}")
    if not rows:
        try:
            import yfinance as yf
            with _YF_LOCK:
                tk = yf.Ticker(t)
                exps = [e for e in (tk.options or []) if d1 <= pd.Timestamp(e).date() <= d2]
            for e in sorted(exps)[:4]:
                with _YF_LOCK:
                    ch = tk.option_chain(e)
                df = ch.puts if put else ch.calls
                exp = pd.Timestamp(e).date()
                yrs = _opt_years(exp)
                for x in df.itertuples():
                    iv = float(x.impliedVolatility or 0)
                    vol = 0 if pd.isna(x.volume) else int(x.volume)
                    _OI_CACHE[x.contractSymbol] = 0 if pd.isna(x.openInterest) else int(x.openInterest)
                    rows.append((exp, float(x.strike), _bs_delta(spot, float(x.strike), yrs, iv, put),
                                 float(x.bid or 0), float(x.ask or 0), x.contractSymbol, iv, None, vol,
                                 "Yahoo (دلتا محسوبة)"))
        except Exception as e:
            log(f"عقد الساعة: {t}: Yahoo: {e}")
    return rows


_OI_CACHE = {}


def _opt_open_interest(t, x):
    """العقود المفتوحة للعقد. ألباكا ما يعطيها بالسناب شوت، فنجيبها من ياهو (سلسلة الانتهاء مرة وحدة)."""
    sym = x[5]
    if sym in _OI_CACHE:
        return _OI_CACHE[sym]
    try:
        import yfinance as yf
        with _YF_LOCK:
            ch = yf.Ticker(t).option_chain(x[0].isoformat())
        for df in (ch.calls, ch.puts):
            for y in df.itertuples():
                _OI_CACHE[y.contractSymbol] = 0 if pd.isna(y.openInterest) else int(y.openInterest)
    except Exception as e:
        log(f"العقود المفتوحة: {t} {x[0]}: {e}")
    if len(_OI_CACHE) > 50000:
        _OI_CACHE.clear()
    return _OI_CACHE.setdefault(sym, None)


# ================== تمركز القاما (يستخدمه سحب السيولة والإنفيرجن) ==================
def _bs_gamma(spot, strike, years, iv):
    """قاما بلاك شولز (نفسها للكول والبوت)."""
    if not (spot and strike and years > 0 and iv and iv > 0.01):
        return 0.0
    sq = iv * math.sqrt(years)
    d1 = (math.log(spot / strike) + (PDR_OPT_RATE + iv * iv / 2) * years) / sq
    return math.exp(-d1 * d1 / 2) / math.sqrt(2 * math.pi) / (spot * sq)


GAMMA_CACHE_MIN = 30             # سلسلة العقود لكل سهم تتخزن كذا دقيقة (الإنفيرجن ينبه كثير، فما نعيد التحميل كل مرة)
_GAMMA_CACHE = {}                # الرمز -> (وقت التحميل، [(سترايك، انتهاء، IV، مفتوحة، كول؟)]، الانتهاءات)


def _gamma_chain(t):
    """سلسلة عقود ياهو لأقرب الانتهاءات (محفوظة GAMMA_CACHE_MIN دقيقة)."""
    hit = _GAMMA_CACHE.get(t)
    if hit and time.time() - hit[0] < GAMMA_CACHE_MIN * 60:
        return hit[1], hit[2]
    import yfinance as yf
    today = pd.Timestamp.now(tz=NY).date()
    last = today + timedelta(days=GAMMA_MAX_DTE)
    with _YF_LOCK:
        tk = yf.Ticker(GAMMA_CHAIN_ALIAS.get(t, t))
        exps = [e for e in (tk.options or []) if today <= pd.Timestamp(e).date() <= last]
    exps = sorted(exps)[:GAMMA_MAX_EXPS]
    raw = []                     # (سترايك، انتهاء، IV، مفتوحة، كول؟، فوليوم) - IV ممكن تكون صفر
    for e in exps:
        with _YF_LOCK:
            ch = tk.option_chain(e)
        exp = pd.Timestamp(e).date()
        for df, is_call in ((ch.calls, True), (ch.puts, False)):
            for x in df.itertuples():
                oi = 0 if pd.isna(x.openInterest) else int(x.openInterest)
                iv = 0 if pd.isna(x.impliedVolatility) else float(x.impliedVolatility)
                if oi > 0:
                    vol = 0 if pd.isna(x.volume) else int(x.volume)
                    raw.append((float(x.strike), exp, iv, oi, is_call, vol))
    # ياهو قبل الافتتاح وبالويكند يرجع IV قريب من الصفر (ما فيه bid/ask)، فبدال ما تنشال العقود:
    # نستخدم وسيط IV الصالح لنفس الانتهاء، وإلا وسيط الكل، وإلا التذبذب التاريخي للسهم (30 يوم)
    good = [r for r in raw if r[2] > 0.01]
    fallback = {}
    if len(good) < len(raw):
        for e in {r[1] for r in raw}:
            ivs = sorted(r[2] for r in good if r[1] == e)
            if ivs:
                fallback[e] = ivs[len(ivs) // 2]
        all_ivs = sorted(r[2] for r in good)
        hv = all_ivs[len(all_ivs) // 2] if all_ivs else None
        if hv is None:
            try:
                with _YF_LOCK:
                    h = tk.history(period="3mo", interval="1d")["Close"].dropna()
                r = (h / h.shift(1)).apply(math.log).dropna().tail(30)
                hv = float(r.std() * math.sqrt(252)) if len(r) > 5 else None
            except Exception:
                hv = None
        for e in {r[1] for r in raw}:
            fallback.setdefault(e, hv)
    chain = []
    for k, e, iv, oi, c, v in raw:
        if iv <= 0.01:
            iv = fallback.get(e) or 0
        if iv > 0.01:
            chain.append((k, e, iv, oi, c, v))
    if len(_GAMMA_CACHE) > 500:
        _GAMMA_CACHE.clear()
    _GAMMA_CACHE[t] = (time.time(), chain, exps)
    return chain, exps


def _gamma_rows(t, spot):
    """[(سترايك، سنوات، IV، العقود المفتوحة، كول؟، فوليوم)] داخل ±GAMMA_RANGE_PCT% من السعر، والانتهاءات المستخدمة."""
    chain, exps = _gamma_chain(t)
    lo, hi = spot * (1 - GAMMA_RANGE_PCT / 100), spot * (1 + GAMMA_RANGE_PCT / 100)
    yrs = {e: _opt_years(e) for e in {x[1] for x in chain}}
    rows = [(k, yrs[e], iv, oi, c, v) for k, e, iv, oi, c, v in chain if lo <= k <= hi]
    return rows, exps


def _gex_at(rows, s):
    """صافي القاما بالدولار لكل 1% حركة لو السعر = s."""
    tot = 0.0
    for k, yrs, iv, oi, is_call, *_ in rows:
        g = _bs_gamma(s, k, yrs, iv) * oi * 100 * s * s * 0.01
        tot += g if is_call else -g
    return tot


def _fmt_usd(v):
    a = abs(v)
    sgn = "-" if v < 0 else ""
    if a >= 1e9:
        return f"{sgn}{a / 1e9:.2f}B$"
    if a >= 1e6:
        return f"{sgn}{a / 1e6:.1f}M$"
    if a >= 1e3:
        return f"{sgn}{a / 1e3:.0f}K$"
    return f"{sgn}{a:.0f}$"


def gamma_levels(t, spot):
    """مستويات القاما والسيولة لسهم، أو None لو ما فيه بيانات عقود.
    {calls, puts: قاما كل سترايك$، call_wall, put_wall, top, net, flip, oi_top: (سترايك، كول، بوت)،
     vol_top: (سترايك، فوليوم)، exps}"""
    if not spot:
        return None
    spot = float(spot)
    rows, exps = _gamma_rows(t, spot)
    if not rows:
        return None
    calls, puts, oi_k, vol_k = {}, {}, {}, {}
    for k, yrs, iv, oi, is_call, vol in rows:
        g = _bs_gamma(spot, k, yrs, iv) * oi * 100 * spot * spot * 0.01
        d = calls if is_call else puts
        d[k] = d.get(k, 0.0) + g
        o = oi_k.setdefault(k, [0, 0])
        o[0 if is_call else 1] += oi
        vol_k[k] = vol_k.get(k, 0) + (vol or 0)
    total = {k: calls.get(k, 0.0) + puts.get(k, 0.0) for k in set(calls) | set(puts)}
    # نقطة الانقلاب: أقرب سعر للسعر الحالي يتغير عنده صافي القاما من سالب لموجب
    grid = [spot * (1 + i / 200) for i in range(-30, 31)]       # ±15% بخطوة 0.5%
    vals = [_gex_at(rows, s) for s in grid]
    flips = [(grid[i] + grid[i + 1]) / 2 for i in range(len(grid) - 1) if (vals[i] < 0) != (vals[i + 1] < 0)]
    ko = max(oi_k, key=lambda k: sum(oi_k[k])) if oi_k else None
    kv = max(vol_k, key=vol_k.get) if vol_k and max(vol_k.values()) > 0 else None
    return {"calls": calls, "puts": puts, "exps": exps,
            "call_wall": max(calls, key=calls.get) if calls else None,
            "put_wall": max(puts, key=puts.get) if puts else None,
            "top": sorted(total, key=total.get, reverse=True)[:GAMMA_TOP_N],
            "net": _gex_at(rows, spot),
            "flip": min(flips, key=lambda x: abs(x - spot)) if flips else None,
            "oi_top": (ko, oi_k[ko][0], oi_k[ko][1]) if ko is not None else None,
            "vol_top": (kv, vol_k[kv]) if kv is not None else None}


def gamma_block(t, spot):
    """نص تمركز القاما للتنبيه، أو "" لو ما فيه بيانات."""
    if not SWEEP_GAMMA or not spot:
        return ""
    lv = gamma_levels(t, spot)
    if not lv:
        return ""
    spot = float(spot)
    calls, puts, exps = lv["calls"], lv["puts"], lv["exps"]
    pct = lambda k: f"{(k / spot - 1) * 100:+.1f}%"
    lines = [f"🧲 تمركز القاما (أقرب {len(exps)} انتهاء، لين {pd.Timestamp(exps[-1]):%m-%d}):"]
    if lv["call_wall"] is not None:
        kc = lv["call_wall"]
        lines.append(f"جدار الكول: {kc:g} ({pct(kc)}) — {_fmt_usd(calls[kc])}")
    if lv["put_wall"] is not None:
        kp = lv["put_wall"]
        lines.append(f"جدار البوت: {kp:g} ({pct(kp)}) — {_fmt_usd(-puts[kp])}")
    if lv["top"]:
        lines.append("أعلى تمركز: " + " | ".join(f"{k:g} ({pct(k)})" for k in lv["top"]))
    net = lv["net"]
    lines.append(f"صافي القاما: {_fmt_usd(net)} لكل 1% — "
                 + ("موجب ← حركة أهدى والسعر ينشد للسترايكات الكبيرة" if net >= 0
                    else "سالب ← الحركة أقوى وأسرع"))
    if lv["flip"] is not None:
        f = lv["flip"]
        lines.append(f"نقطة الانقلاب: {f:.2f} ({pct(f)}) — "
                     + ("السعر فوقها" if spot > f else "السعر تحتها"))
    return "\n".join(lines)


# ================== (15) تقرير القاما اليومي ==================
def _k_fmt(v):
    return f"{v / 1e6:.2f}M" if v >= 1e6 else f"{v / 1e3:.1f}K" if v >= 1e3 else f"{v:.0f}"


def _gex_line(t, spot, lv):
    """سطرين لكل سهم بالتقرير اليومي."""
    pct = lambda k: f"{(k / spot - 1) * 100:+.1f}%"
    net = lv["net"]
    head = f"${t} {spot:.2f} | صافي {_fmt_usd(net)} {'🟢' if net >= 0 else '🔴'}"
    parts = []
    if lv["call_wall"] is not None:
        parts.append(f"كول {lv['call_wall']:g} ({pct(lv['call_wall'])})")
    if lv["put_wall"] is not None:
        parts.append(f"بوت {lv['put_wall']:g} ({pct(lv['put_wall'])})")
    if lv["flip"] is not None:
        parts.append(f"انقلاب {lv['flip']:.2f}")
    if lv["oi_top"]:
        k, c, p = lv["oi_top"]
        parts.append(f"أكثر سيولة {k:g} ({_k_fmt(c + p)} عقد مفتوح)")
    if lv["vol_top"]:
        k, v = lv["vol_top"]
        parts.append(f"فوليوم {k:g} ({_k_fmt(v)})")
    return head + "\n" + " | ".join(parts)


def gex_daily_lines(symbols):
    """[(نص السهم)]، [الرموز اللي ما لها بيانات]."""
    spots = {}
    for t, df in download_batches(symbols, 100, period="5d", interval="1d", prepost=False):
        try:
            spots[t] = float(df["Close"].iloc[-1])
        except Exception:
            pass
    lines, miss = [], []
    for t in symbols:
        lv = None
        if spots.get(t):
            try:
                lv = gamma_levels(t, spots[t])
            except Exception as e:
                log(f"تقرير القاما: {t}: {e}")
        if lv:
            lines.append(_gex_line(t, spots[t], lv))
        else:
            miss.append(t)
    free_memory()
    return lines, miss


def gex_daily_send(symbols, prefix=""):
    t0 = time.time()
    lines, miss = gex_daily_lines(symbols)
    now = pd.Timestamp.now(tz=LOCAL_TZ)
    head = (f"{prefix}🧲 تقرير القاما اليومي — {now:%Y-%m-%d}\n"
            f"مراكز صناع السوق من العقود المفتوحة (أقرب {GAMMA_MAX_EXPS} انتهاءات، السترايكات ±{GAMMA_RANGE_PCT}% من السعر)\n"
            "كول = جدار الكول (مقاومة) | بوت = جدار البوت (دعم)\n"
            "انقلاب = السعر اللي يتحول عنده صافي القاما بين موجب وسالب\n"
            "أكثر سيولة = السترايك اللي عليه أكثر عقود مفتوحة | فوليوم = أكثر سترايك تداول بآخر جلسة\n"
            "صافي 🟢 موجب = حركة أهدى | 🔴 سالب = حركة أقوى وأسرع")
    chunks, cur = [], head
    for ln in lines:
        if len(cur) + len(ln) + 2 > 3400:
            chunks.append(cur)
            cur = ""
        cur += ("\n\n" if cur else "") + ln
    if miss:
        tail = "ما فيه بيانات عقود: " + " ".join(miss)
        if len(cur) + len(tail) + 2 > 3400:
            chunks.append(cur)
            cur = ""
        cur += ("\n\n" if cur else "") + tail
    chunks.append(cur)
    for i, c in enumerate(chunks, 1):
        send_telegram(c + (f"\n\n({i}/{len(chunks)})" if len(chunks) > 1 else ""), kind="gex")
        time.sleep(1)
    log(f"[{datetime.now():%H:%M}] تقرير القاما: {len(lines)} سهم، {len(miss)} بدون بيانات — "
        f"{time.time() - t0:.0f} ثانية")


_gex_running = threading.Event()


def gex_daily_maybe_start():
    """مرة كل يوم سوق، من GEX_DAILY_AT_NY لين GEX_DAILY_UNTIL_NY (نيويورك) - بخيط لحاله."""
    if not ENABLE_GEX_DAILY or _gex_running.is_set():
        return
    now = pd.Timestamp.now(tz=NY)
    if now.weekday() >= 5 or not (GEX_DAILY_AT_NY <= (now.hour, now.minute) < GEX_DAILY_UNTIL_NY):
        return
    day = str(now.date())
    try:
        with open(GEX_DAILY_STATE, encoding="utf-8") as f:
            if f.read().strip() == day:
                return
    except FileNotFoundError:
        pass
    try:
        with open(GEX_DAILY_STATE, "w", encoding="utf-8") as f:   # يتسجل قبل الإرسال عشان ما يتكرر لو صار خطأ
            f.write(day)
    except Exception as e:
        log(f"تقرير القاما: ما قدرت أحفظ اليوم: {e}")
    _gex_running.set()

    def run():
        try:
            gex_daily_send(GEX_SYMBOLS or list(WATCH_SYMBOLS))
        except Exception as e:
            log(f"تقرير القاما: خطأ - {e}")
        finally:
            _gex_running.clear()

    threading.Thread(target=run, daemon=True, name="gex_daily").start()


def gex_self_test():
    """python short_bot.py --gextest — يجرب الحساب والرسالة على سلسلة وهمية بدون نت."""
    exp = (pd.Timestamp.now(tz=NY) + pd.Timedelta(days=7)).date()
    fake = [  # (سترايك، انتهاء، IV، مفتوحة، كول؟، فوليوم)
        (95, exp, 0.4, 9000, False, 1200), (100, exp, 0.4, 20000, False, 3000),
        (100, exp, 0.4, 15000, True, 8000), (105, exp, 0.4, 25000, True, 4000),
        (110, exp, 0.4, 6000, True, 900), (90, exp, 0.4, 3000, False, 100)]
    _GAMMA_CACHE["TEST"] = (time.time(), fake, [exp.isoformat()])
    lv = gamma_levels("TEST", 101.0)
    assert lv["call_wall"] == 105 and lv["put_wall"] == 100, lv
    assert lv["oi_top"] == (100, 15000, 20000) and lv["vol_top"] == (100, 11000), lv
    print("✅ جدار الكول 105 | جدار البوت 100 | أكثر عقود مفتوحة 100 (35K) | أكثر فوليوم 100")
    print(_gex_line("TEST", 101.0, lv))
    print()
    print(gamma_block("TEST", 101.0))
    print("GEX TEST OK")


def with_gamma(msg, t, spot):
    """يضيف تمركز القاما للتنبيه (قبل سطر التنبيه ⚠️ لو موجود)."""
    try:
        g = gamma_block(t, spot)
    except Exception as e:
        log(f"تمركز القاما: {t}: {e}")
        return msg
    if not g:
        log(f"تمركز القاما: {t}: ما فيه بيانات عقود من ياهو - التنبيه راح بدون قاما")
        return msg
    if "\n⚠️" in msg:
        a, b = msg.rsplit("\n⚠️", 1)
        return a.rstrip() + "\n\n" + g + "\n\n⚠️" + b
    return msg + "\n\n" + g


# ================== (4ب) التجزئة العكسية ==================
def load_rsplits(tickers):
    """كل التجزئات العكسية آخر سنة.
    يرجع {الرمز: {"splits": [(التاريخ، النسبة، سعر الافتتاح يومها)], "last": آخر سعر}}"""
    out = {}
    for t, df in download_batches(tickers, UNIVERSE_BATCH, period="1y", interval="1d",
                                  prepost=False, actions=True):
        try:
            if "Stock Splits" not in df:
                continue
            sp = df["Stock Splits"].fillna(0)
            rev = sp[(sp > 0) & (sp < 1)]
            if rev.empty:
                continue
            splits = [(pd.Timestamp(i).date(), float(r), float(df.loc[i, "Open"]))
                      for i, r in rev.items()]
            out[t] = {"splits": splits, "last": float(df["Close"].iloc[-1])}
        except Exception:
            continue
    free_memory()
    return out


def _rsplit_line(t, info, split):
    d, ratio, opn = split
    return (f"• ${t}{sec_tag(t)}\n"
            f"   تاريخ التجزئة: {d:%Y-%m-%d} | النسبة: كل {1 / ratio:g} أسهم = سهم\n"
            f"   افتتح بعد التجزئة على: {opn:.2f}$ | السعر الحين: {info['last']:.2f}$\n"
            f"   عدد التجزئات العكسية آخر سنة: {len(info['splits'])}")


def _send_rsplit_list(title, items):
    """items = [(الرمز، البيانات، التجزئة)]. يرسلها على رسايل (كل رسالة 15 سهم)."""
    items = sorted(items, key=lambda x: x[2][0], reverse=True)       # الأحدث فوق
    for i in range(0, len(items), 15):
        part = items[i:i + 15]
        head = title + (f" ({i // 15 + 1})" if len(items) > 15 else "")
        send_telegram(head + "\n\n" + "\n\n".join(_rsplit_line(*x) for x in part), kind="rsplit")
        time.sleep(2)


def splits_between(data, start, end):
    """التجزئات اللي تاريخها من start لين end (تواريخ)."""
    return [(t, info, sp) for t, info in data.items() for sp in info["splits"]
            if start <= sp[0] <= end]


def scan_rsplit_new(data, already_sent):
    """يرسل التجزئات الجديدة بس. لو ما فيه جديد، ما يرسل شي."""
    today = pd.Timestamp.now(tz=NY).date()
    since = today - pd.Timedelta(days=RSPLIT_NEW_DAYS)
    new = []
    for t, info, sp in splits_between(data, since, today):
        key = f"{t}-{sp[0]:%Y-%m-%d}"
        if key in already_sent:
            continue
        already_sent.add(key)
        _append_line(RSPLIT_NEW_FILE, key)
        new.append((t, info, sp))
    if new:
        _send_rsplit_list(f"🆕 تجزئة عكسية جديدة - {len(new)} سهم", new)
    log(f"[{datetime.now():%H:%M}] التجزئة العكسية: {len(new)} سهم جديد")
    return new


def _rsplit_state():
    st = {}
    for line in _load_set(RSPLIT_STATE_FILE):
        k, _, v = line.partition("=")
        st[k] = v
    return st


def _save_rsplit_state(st):
    try:
        with open(RSPLIT_STATE_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(f"{k}={v}" for k, v in st.items()) + "\n")
    except Exception:
        pass


def rsplit_job(state, new_sent, force=False):
    """مرة باليوم (أيام السوق، بعد 10 الصبح نيويورك):
    الجديد كل يوم + قائمة الأسبوع يوم الجمعة."""
    now = pd.Timestamp.now(tz=NY)
    today = now.date()
    if not force and (now.weekday() >= 5 or now.hour < RSPLIT_CHECK_AFTER_NY):
        return
    if not force and state.get("day") == str(today):
        return
    tickers = build_universe("التجزئة العكسية", 0.01, 100_000, 0, include_nyse=False)
    data = load_rsplits(tickers)
    log(f"التجزئة العكسية: {len(data)} سهم سوى تجزئة عكسية آخر سنة")

    scan_rsplit_new(data, new_sent)

    week = f"{today.isocalendar()[0]}-W{today.isocalendar()[1]:02d}"
    if RSPLIT_WEEKLY and now.weekday() == 4 and state.get("week") != week:     # الجمعة
        items = splits_between(data, today - pd.Timedelta(days=6), today)
        if items:
            _send_rsplit_list(f"📋 قائمة الأسبوع - تجزئات عكسية آخر 7 أيام ({len(items)} سهم)", items)
        state["week"] = week

    state["day"] = str(today)
    _save_rsplit_state(state)
    free_memory()


# ================== (11) سحب قمة الجمعة يوم الاثنين ثم سحب دعم الأسبوع السابق (فريم 4 ساعات) → كول ==================
#   1) يوم الاثنين: السعر يسحب قمة الجمعة (ذيل فوقها) ويرجع يختبرها وما يخترقها (ولا شمعة 4 ساعات تقفل فوقها)
#   2) بعدها ينزل لقاع الأسبوع السابق (الدعم) ويسحب السيولة: شمعة 4 ساعات ذيلها تحت الدعم وإغلاقها فوقه
#   3) التنبيه: كول، الأهداف (قمة الجمعة ثم قمة الاثنين)، الوقف تحت شمعة السحب، وعقد كول مدته أسبوعين
#   الأسهم: القائمة الموحدة (WATCH_SYMBOLS) اللي سعرها 100$-400$
ENABLE_FRIMON = False            # True = شغال | False = مطفي
FRIMON_MIN_PRICE = 100
FRIMON_MAX_PRICE = 400
FRIMON_OPT_DTE = 14              # مدة العقد: أسبوعين (يختار أقرب انتهاء لـ 14 يوم)
FRIMON_OPT_MIN_DTE = 10          # يدوّر بين 10 و18 يوم
FRIMON_OPT_MAX_DTE = 18
FRIMON_OPT_MIN_VOLUME = 300      # حجم التداول في العقد فوق 300
FRIMON_OPT_MIN_OI = 1000         # العقود المفتوحة (الكمية غير إغلاق المركز) فوق 1000
FRIMON_OPT_MIN_DELTA = 0.15      # الدلتا فوق 0.1500
FRIMON_SCAN_AFTER_MIN = 3        # يفحص بعد إغلاق شمعة 4 ساعات بكم دقيقة (1:30 و 4:00 العصر نيويورك)
FRIMON_SCAN_WINDOW_MIN = 40
FRIMON_TEST_ID = "1"             # رسالة تجريبية مرة وحدة بعد الرفع — غيّر الرقم لو تبي وحدة ثانية
FRIMON_SENT_FILE = os.path.join(os.environ.get("RAILWAY_VOLUME_MOUNT_PATH", "."), "frimon_sent.txt")


def frimon_resistance_above(daily, this_wk, level, bars=2):
    """أقرب مقاومة يومية فوق المستوى: قمة شمعة يومية أعلى من الشمعتين قبلها والشمعتين بعدها
    (قبل الأسبوع الحالي). يرجع السعر أو None."""
    d = daily[[pd.Timestamp(i).date() < this_wk for i in daily.index]]
    hi = d["High"].astype(float).tolist()
    piv = [hi[i] for i in range(bars, len(hi) - bars)
           if hi[i] >= max(hi[i - bars:i]) and hi[i] >= max(hi[i + 1:i + 1 + bars])]
    above = [h for h in piv if h > level * 1.002]
    return min(above) if above else None


def frimon_check(daily, c4, now):
    """daily = شموع يومية (آخر شهر)، c4 = شموع 4 ساعات (mkt4h_candles)، now = الوقت (نيويورك).
    يرجع تفاصيل النموذج لو تحقق على آخر شمعة 4 ساعات مقفلة، وإلا None."""
    if daily is None or daily.empty or c4 is None or c4.empty:
        return None
    this_wk = _week_start(now).date()
    prev_wk = this_wk - timedelta(days=7)
    pw = _prev_week_rows(daily, prev_wk, this_wk)
    if pw.empty:
        return None
    fri = pw.iloc[-1]                                   # آخر يوم بالأسبوع السابق (الجمعة)
    fh, fri_day = float(fri["High"]), pd.Timestamp(pw.index[-1]).date()
    lows = pw["Low"].astype(float)
    pwl, pwl_day = float(lows.min()), pd.Timestamp(lows.idxmin()).date()

    c = c4[(c4["end"] <= now).values]                   # الشموع المقفلة بس
    days = pd.Series([pd.Timestamp(i).date() for i in c.index], index=c.index)
    c = c[(days >= this_wk).values]
    if len(c) < 2:
        return None
    first_day = min(pd.Timestamp(i).date() for i in c.index)
    if first_day.weekday() != 0:                        # لازم يوم الاثنين موجود (مو عطلة)
        return None
    cdays = [pd.Timestamp(i).date() for i in c.index]
    mon = c[[d == first_day for d in cdays]]
    if mon.empty or float(mon["High"].max()) <= fh:     # 1) سحب قمة الجمعة يوم الاثنين
        return None
    mon_high = float(mon["High"].max())
    sweep_i = list(c.index).index(mon["High"].astype(float).idxmax())
    # إعادة اختبار وعدم اختراق: ولا شمعة من الاثنين لين الحين قفلت فوق قمة الجمعة
    if (c["Close"].astype(float) > fh).any():
        return None
    sig = c.iloc[-1]                                    # 2) آخر شمعة مقفلة = شمعة سحب الدعم
    if len(c) - 1 <= sweep_i:
        return None                                     # لازم بعد سحب القمة
    lo, cl = float(sig["Low"]), float(sig["Close"])
    if not (lo < pwl < cl):
        return None
    # أول سحب للدعم بعد سحب القمة (ما نعيد على شمعة ثانية)
    mid = c.iloc[sweep_i + 1:-1]
    if (mid["Low"].astype(float) < pwl).any():
        return None
    if not (FRIMON_MIN_PRICE <= cl <= FRIMON_MAX_PRICE):
        return None
    pwh = float(pw["High"].astype(float).max())
    near = frimon_resistance_above(daily, this_wk, fh)
    cands = [("مقاومة الجمعة", fh), ("قمة الأسبوع السابق", pwh)]
    if near:
        cands.insert(1, ("أقرب مقاومة يومية فوقها", near))
    targets = []
    for name, px in sorted(cands, key=lambda x: x[1]):
        if px > cl and (not targets or px - targets[-1][1] > cl * 0.002):
            targets.append((name, px))
    if not targets:
        return None
    return {"fh": fh, "fri_day": fri_day, "pwl": pwl, "pwl_day": pwl_day, "mon_high": mon_high,
            "entry": cl, "stop": lo, "sig_start": c.index[-1], "sig_end": sig["end"], "targets": targets}


def _frimon_opt_px(c, spot, new_spot):
    """سعر العقد التقديري لو السهم راح لـ new_spot (بلاك شولز بنفس IV، بدون حساب مرور الوقت)."""
    exp, k, delta, bid, ask, sym, iv, gamma = c[:8]
    mid = (bid + ask) / 2 if bid else ask
    yrs = _opt_years(exp)
    p0, p1 = _bs_price(spot, k, yrs, iv, False), _bs_price(new_spot, k, yrs, iv, False)
    if p0 is not None and p1 is not None:
        px = mid + (p1 - p0)
    else:
        ds = new_spot - spot
        px = mid + delta * ds + 0.5 * (gamma or 0) * ds * ds
    return max(round(px, 2), 0.01), mid


def frimon_pick_option(t, spot):
    """عقد كول: أقرب انتهاء لأسبوعين، حجم فوق 300، عقود مفتوحة فوق 1000، دلتا فوق 0.15.
    يرجع (العقد، الحجم، العقود المفتوحة) أو None."""
    today = pd.Timestamp.now(tz=NY).date()
    d1, d2 = today + timedelta(days=FRIMON_OPT_MIN_DTE), today + timedelta(days=FRIMON_OPT_MAX_DTE)
    ok = []
    for x in _pdr1h_option_rows(t, False, spot, d1, d2):
        exp, k, delta, bid, ask, sym, iv, gamma, vol, src = x
        if delta is None or delta <= FRIMON_OPT_MIN_DELTA or not ask:
            continue
        if (vol or 0) <= FRIMON_OPT_MIN_VOLUME:
            continue
        ok.append(x)
    if not ok:
        return None
    target = today + timedelta(days=FRIMON_OPT_DTE)
    exp = min({x[0] for x in ok}, key=lambda e: abs((e - target).days))
    cands = sorted((x for x in ok if x[0] == exp), key=lambda x: x[2])   # الأرخص (أقل دلتا) أول
    for x in cands:
        oi = _opt_open_interest(t, x) or 0
        if oi > FRIMON_OPT_MIN_OI:
            return x, x[8], oi
    return None


def frimon_message(t, r, opt):
    entry, stop = r["entry"], r["stop"]
    risk = entry - stop
    lines = [f"🟢 كول — سحب قمة الجمعة ثم سحب دعم الأسبوع السابق (فريم 4 ساعات)",
             f"السهم: ${t}{sec_tag(t, ' — ')}",
             f"قمة الجمعة ({r['fri_day']:%m-%d}): {r['fh']:.2f} ← انسحبت يوم الاثنين ({r['mon_high']:.2f}) وما انخترقت",
             f"دعم الأسبوع السابق ({r['pwl_day']:%m-%d}): {r['pwl']:.2f} ← انسحب والإغلاق فوقه",
             f"شمعة السحب: {r['sig_start'].tz_convert(LOCAL_TZ):%m-%d %H:%M} (توقيتك)",
             "",
             f"🛑 وقف الخسارة: {stop:.2f} (تحت شمعة سحب الدعم) — {risk / entry * 100:.1f}%"]
    for i, (name, px) in enumerate(r["targets"], 1):
        lines.append(f"🎯 الهدف {i}: {px:.2f} — +{(px / entry - 1) * 100:.1f}%"
                     + (f" | {(px - entry) / risk:.1f}R" if risk > 0 else ""))
    lines.append("")
    if opt:
        c, vol, oi = opt
        exp, k, delta, bid, ask, sym, iv = c[:7]
        days = (exp - pd.Timestamp.now(tz=NY).date()).days
        stop_px, mid = _frimon_opt_px(c, entry, stop)
        lines += [f"📄 العقد: {t} كول {k:g} — انتهاء {exp:%Y-%m-%d} ({days} يوم)",
                  f"السعر الحين: {mid:.2f}$ (العقد كامل {mid * 100:,.0f}$) | بيد {bid or 0:.2f} / أسك {ask:.2f}",
                  f"الدلتا: {delta:.4f}" + (f" | IV: {iv * 100:.0f}%" if iv else ""),
                  f"حجم التداول: {int(vol):,} | العقود المفتوحة: {int(oi):,}",
                  f"🛑 وقف العقد: {stop_px:.2f}$ ({(stop_px / mid - 1) * 100:+.0f}%) لو السهم وصل {stop:.2f}"]
        for i, (name, px) in enumerate(r["targets"], 1):
            tp, _ = _frimon_opt_px(c, entry, px)
            lines.append(f"🎯 العقد عند الهدف {i} ({px:.2f}): تقريباً {tp:.2f}$ ({(tp / mid - 1) * 100:+.0f}%)")
        lines.append("(أسعار العقد عند الوقف والأهداف تقديرية — بلاك شولز بنفس IV، وما تحسب مرور الوقت)")
    else:
        lines.append(f"📄 العقد: ما لقيت كول بالشروط (أسبوعين، حجم فوق {FRIMON_OPT_MIN_VOLUME}، "
                     f"عقود مفتوحة فوق {FRIMON_OPT_MIN_OI:,}، دلتا فوق {FRIMON_OPT_MIN_DELTA:.4f})")
    lines += ["", "⚠️ ليست توصية بيع أو شراء — للتعليم والتداول الوهمي فقط."]
    return "\n".join(lines)


def frimon_scan(symbols, sent, now=None):
    now = now or pd.Timestamp.now(tz=NY)
    wk = f"{now.isocalendar()[0]}-W{now.isocalendar()[1]:02d}"
    daily = {t: df for t, df in download_batches(symbols, 100, period="6mo", interval="1d", prepost=False)}
    cands = [t for t, df in daily.items()
             if FRIMON_MIN_PRICE * 0.9 <= float(df["Close"].iloc[-1]) <= FRIMON_MAX_PRICE * 1.1
             and f"{t}-{wk}" not in sent]
    hits = 0
    for t, df in download_batches(cands, 50, period="10d", interval="30m", prepost=False):
        try:
            r = frimon_check(daily[t], mkt4h_candles(df), now)
            if not r:
                continue
            key = f"{t}-{wk}"
            sent.add(key)
            _append_line(FRIMON_SENT_FILE, key)
            opt = None
            try:
                opt = frimon_pick_option(t, r["entry"])
            except Exception as e:
                log(f"سحب الجمعة/الاثنين: {t}: العقد: {e}")
            send_telegram(frimon_message(t, r, opt), kind="frimon")
            hits += 1
        except Exception as e:
            log(f"سحب الجمعة/الاثنين: {t}: {e}")
    log(f"[{datetime.now():%H:%M}] سحب الجمعة/الاثنين: فحص {len(cands)} سهم — {hits} تنبيه")
    free_memory()


def frimon_send_test_once():
    """يرسل تنبيه تجريبي للقسم مرة وحدة (يتذكرها في /data عشان ما تتكرر مع كل تشغيل)."""
    marker = os.path.join(os.environ.get("RAILWAY_VOLUME_MOUNT_PATH", "."), "frimon_test_sent.txt")
    try:
        with open(marker, encoding="utf-8") as f:
            if f.read().strip() == FRIMON_TEST_ID:
                return
    except Exception:
        pass
    tz = NY
    now = pd.Timestamp.now(tz=tz)
    r = {"fh": 156.00, "fri_day": (now - pd.Timedelta(days=5)).date(), "pwl": 147.50,
         "pwl_day": (now - pd.Timedelta(days=8)).date(), "mon_high": 157.20, "entry": 148.40,
         "stop": 147.00, "sig_start": now.floor("h"),
         "targets": [("مقاومة الجمعة", 156.00), ("أقرب مقاومة يومية فوقها", 159.40), ("قمة الأسبوع السابق", 161.80)]}
    exp = (now + pd.Timedelta(days=14)).date()
    fake = (exp, 155.0, 0.32, 1.80, 1.95, "TEST", 0.38, 0.03, 850, "test")
    send_telegram("🧪 رسالة تجريبية - هذا مو تنبيه حقيقي (السهم والأرقام وهمية)\n\n"
                  + frimon_message("TEST", r, (fake, 850, 2400))
                  + "\n\nلو وصلتك هالرسالة، تنبيهات القسم الحقيقية بتوصل لنفس المكان.", kind="frimon")
    try:
        with open(marker, "w", encoding="utf-8") as f:
            f.write(FRIMON_TEST_ID)
    except Exception as e:
        log(f"سحب الجمعة/الاثنين: ما قدرت أحفظ علامة الرسالة التجريبية: {e}")


def frimon_run_forever():
    frimon_send_test_once()
    sent = _load_set(FRIMON_SENT_FILE)
    done = set()
    symbols = stocks_only(WATCH_SYMBOLS)
    log(f"سحب الجمعة/الاثنين (4 ساعات): بدأ — {len(symbols)} سهم من القائمة، السعر {FRIMON_MIN_PRICE}$-{FRIMON_MAX_PRICE}$")
    while True:
        try:
            now = pd.Timestamp.now(tz=NY)
            if now.weekday() < 5:
                for end_m in (_MKT4H_SPLIT, _MKT4H_END):
                    end = now.normalize() + pd.Timedelta(minutes=end_m)
                    key = f"{now.date()}-{end_m}"
                    if (key not in done and end + pd.Timedelta(minutes=FRIMON_SCAN_AFTER_MIN) <= now
                            <= end + pd.Timedelta(minutes=FRIMON_SCAN_WINDOW_MIN)):
                        done.add(key)
                        frimon_scan(symbols, sent, now)
        except Exception as e:
            log(f"سحب الجمعة/الاثنين: خطأ {e}")
        time.sleep(60)


def frimon_self_test():
    """python short_bot.py --frimontest — يجرب النموذج على بيانات وهمية بدون نت."""
    tz = NY
    days = pd.to_datetime(["2026-10-15", "2026-10-16", "2026-10-19", "2026-10-20", "2026-10-21",
                           "2026-10-22", "2026-10-23",
                           "2026-10-26", "2026-10-27", "2026-10-28", "2026-10-29", "2026-10-30"]).tz_localize(tz)
    daily = pd.DataFrame({"Open":  [155, 156, 157, 158, 157, 156, 156, 158, 152, 151, 153, 154],
                          "High":  [156, 157, 159.4, 158, 157.5, 157, 158, 161.8, 154, 152, 155, 156],
                          "Low":   [154, 155, 156, 156, 155, 155, 155, 151, 147.5, 149, 150, 152],
                          "Close": [156, 157, 158, 157, 156, 156, 157, 152, 151, 151, 154, 155]}, index=days)
    rows = []   # (اليوم، بداية الشمعة، O,H,L,C)
    data = [("2026-11-02", "09:30", 155, 157.2, 154.5, 155.5),   # الاثنين: سحب قمة الجمعة 156
            ("2026-11-02", "13:30", 155.5, 156.3, 153, 153.5),   # إعادة اختبار وما قفل فوقها
            ("2026-11-03", "09:30", 153.5, 154, 150, 150.5),
            ("2026-11-03", "13:30", 150.5, 151, 148.5, 149),
            ("2026-11-04", "09:30", 149, 150, 147.0, 148.4)]     # سحب دعم 147.5 والإغلاق فوقه
    for d, h, o, hi, lo, cl in data:
        st = pd.Timestamp(f"{d} {h}").tz_localize(tz)
        end = st + (pd.Timedelta(hours=4) if h == "09:30" else pd.Timedelta(minutes=150))
        rows.append((st, o, hi, lo, cl, end))
    c4 = pd.DataFrame([{"Open": o, "High": hi, "Low": lo, "Close": cl, "end": e, "n": 8, "need": 8}
                       for st, o, hi, lo, cl, e in rows], index=[r[0] for r in rows])
    now = pd.Timestamp("2026-11-04 13:35").tz_localize(tz)
    r = frimon_check(daily, c4, now)
    print("النموذج:", "✅ تحقق" if r else "❌ ما تحقق")
    if r:
        fake = (pd.Timestamp("2026-11-18").date(), 155.0, 0.32, 1.80, 1.95, "TEST261118C00155000",
                0.38, 0.03, 850, "test")
        print(frimon_message("TEST", r, (fake, 850, 2400)))
    # لو شمعة قفلت فوق قمة الجمعة → ما ينبه
    c4b = c4.copy(); c4b.iloc[1, c4b.columns.get_loc("Close")] = 156.5
    print("إغلاق فوق قمة الجمعة:", "❌ ما ينبه (صح)" if not frimon_check(daily, c4b, now) else "⚠️ نبه (غلط)")


# ================== (6) كشف خوارزميات التنفيذ - ألباكا ==================
from collections import deque

ALGO_URL = "https://data.alpaca.markets/v2/stocks/trades"


def trading_hours(now=None):
    """4 الفجر - 8 بالليل نيويورك، أيام الأسبوع."""
    now = now or pd.Timestamp.now(tz=NY)
    m = now.hour * 60 + now.minute
    return now.weekday() < 5 and 4 * 60 <= m <= 20 * 60


_alpaca_lock = threading.Lock()
_alpaca_next = [0.0]
ALPACA_MIN_GAP_SEC = 0.35    # ≈ 170 طلب بالدقيقة (حد الباقة المجانية 200) - للقسمين مع بعض


def _alpaca_wait():
    """القسمين (الصغيرة والكبيرة) يشتركون بنفس حد الطلبات، فنوزعها بالدور."""
    with _alpaca_lock:
        now = time.time()
        wait = _alpaca_next[0] - now
        _alpaca_next[0] = max(now, _alpaca_next[0]) + ALPACA_MIN_GAP_SEC
    if wait > 0:
        time.sleep(wait)


def fetch_alpaca_trades(symbols, start, end=None):
    """الصفقات من وقت start لين الحين لمجموعة أسهم. يرجع {الرمز: [صفقات]} أو None لو فشل."""
    headers = {"APCA-API-KEY-ID": ALPACA_KEY, "APCA-API-SECRET-KEY": ALPACA_SECRET}
    params = {"symbols": ",".join(symbols), "start": start.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
              "feed": ALGO_FEED, "limit": 10000, "sort": "asc"}
    if end is not None:
        params["end"] = end.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    out = {}
    for _ in range(20):                          # صفحات (لو الصفقات كثيرة)
        _alpaca_wait()
        try:
            r = requests.get(ALGO_URL, headers=headers, params=params, timeout=20)
        except Exception as e:
            log("ألباكا: فشل الاتصال -", e)
            return None
        if r.status_code == 403 and "subscription" in r.text.lower():
            log("ألباكا: الاشتراك ما يسمح ببيانات sip اللحظية - تأكد إن المفاتيح من الحساب المشترك،"
                " أو حط ALGO_DELAY_MIN = 16 في Railway")
            return None
        if r.status_code in (401, 403):
            log(f"ألباكا: المفاتيح مرفوضة ({r.status_code}) - تأكد من ALPACAAPIKEY و ALPACASECRETKEY")
            return None
        if r.status_code == 429:
            log("ألباكا: طلبات كثيرة، أستنى شوي")
            time.sleep(10)
            continue
        if r.status_code != 200:
            log(f"ألباكا: خطأ {r.status_code} - {r.text[:200]}")
            return None
        data = r.json()
        for sym, trades in (data.get("trades") or {}).items():
            out.setdefault(sym, []).extend(trades or [])
        token = data.get("next_page_token")
        if not token:
            break
        params["page_token"] = token
    return out


class AlgoDetector:
    """يعد الصفقات الصغيرة اللي بنفس الحجم بالضبط خلال آخر ALGO_WINDOW_MIN دقيقة لكل سهم.
    ويقدّر الشراء/البيع من اتجاه السعر: صفقة أعلى من اللي قبلها = شراء، أقل = بيع (تقريبي)."""
    def __init__(self):
        self.win = {}         # (الرمز، الحجم) -> deque[(الوقت، السعر، الجهة)]
        self.seen = {}
        self.last_px = {}
        self.last_side = {}
        self.alerted = {}

    def add(self, sym, trade):
        tid = trade.get("i")
        seen = self.seen.setdefault(sym, deque(maxlen=50000))
        if tid is not None:
            if tid in seen:
                return None
            seen.append(tid)
        size = float(trade.get("s") or 0)
        price = float(trade.get("p") or 0)
        if size <= 0 or price <= 0:
            return None
        prev = self.last_px.get(sym)
        side = self.last_side.get(sym, 0)
        if prev is not None and price != prev:
            side = 1 if price > prev else -1          # نفس السعر = نفس جهة اللي قبلها
        self.last_px[sym], self.last_side[sym] = price, side
        if size > ALGO_MAX_SIZE:
            return None
        ts = pd.Timestamp(trade["t"])
        q = self.win.setdefault((sym, size), deque())
        q.append((ts, price, side))
        cutoff = ts - pd.Timedelta(minutes=ALGO_WINDOW_MIN)
        while q and q[0][0] < cutoff:
            q.popleft()
        n = len(q)
        level = ("strong" if n >= ALGO_STRONG_STREAK else
                 "normal" if n >= ALGO_MIN_STREAK else None)
        if level is None:
            return None
        if ALGO_MIN_VALUE and sum(x[1] for x in q) * size < ALGO_MIN_VALUE:
            return None                                # المبلغ صغير: مو أمر كبير متقطع
        k = (sym, size, level)
        last = self.alerted.get(k)
        if last is not None and ts - last < pd.Timedelta(minutes=ALGO_REALERT_MIN):
            return None
        self.alerted[k] = ts
        prices = [x[1] for x in q]
        buys = sum(1 for x in q if x[2] > 0)
        sells = sum(1 for x in q if x[2] < 0)
        return {"size": size, "count": n, "first_t": q[0][0], "last_t": ts,
                "low": min(prices), "high": max(prices), "last": price,
                "buys": buys, "sells": sells, "level": level}


def _side_lines(b, s_, total, size):
    """الشراء والبيع مع بعض (تقدير من اتجاه السعر: صفقة أعلى من اللي قبلها = شراء، أقل = بيع)."""
    pct = lambda x: f"{x / total * 100:.0f}%" if total else "0%"
    n = total - b - s_
    return (f"🟢 شراء: {b:,} صفقة ({pct(b)}) = {b * size:,.0f} سهم\n"
            f"🔴 بيع: {s_:,} صفقة ({pct(s_)}) = {s_ * size:,.0f} سهم\n"
            + (f"⚪ بدون اتجاه: {n:,} صفقة\n" if n else ""))


def _algo_message(sym, a, cap=None, section="", note=""):
    strength = "🔥 قوي" if a["level"] == "strong" else "⚡ رصد"
    mins = max((a["last_t"] - a["first_t"]).total_seconds() / 60, 0.1)
    b, s_, total = a["buys"], a["sells"], a["count"]
    return (f"🤖 خوارزمية تقطيع محتملة — {strength}\n"
            + (f"القسم: {section}\n" if section else "")
            + f"السهم: ${sym}\n"
            f"السعر: ${a['last']:.4g} (من {a['low']:.4g} إلى {a['high']:.4g})\n"
            f"الحجم المتكرر: {a['size']:g} سهم\n"
            f"التكرار: {total} صفقة خلال {mins:.1f} دقيقة\n"
            + _side_lines(b, s_, total, a["size"])
            + (f"القيمة السوقية: {_cap_txt(cap)}\n" if cap else "")
            + (f"{note}\n" if note else "")
            + f"المصدر: {ALGO_FEED.upper()} عبر Alpaca"
            + (f" (متأخر {ALGO_DELAY_MIN - 1} دقيقة)" if ALGO_DELAY_MIN else "") + "\n"
            f"وقت آخر صفقة: {a['last_t'].tz_convert(LOCAL_TZ):%H:%M:%S} (توقيتك)")


FLOAT_CACHE_SEC = 6 * 60 * 60    # تحديث بيانات الفلوت كل 6 ساعات (يستخدمها ماسح السيولة)
_algo_float_cache = {}


def get_algo_float(sym):
    now = time.time(); old = _algo_float_cache.get(sym)
    if old and now - old[0] < FLOAT_CACHE_SEC:
        return old[1]
    try:
        import yfinance as yf
        info = yf.Ticker(sym).info or {}; val = info.get("floatShares")
        val = float(val) if val is not None else None
    except Exception:
        val = None
    _algo_float_cache[sym] = (now, val)
    return val


def _cap_txt(cap):
    return f"{cap / 1e9:.2f} مليار$" if cap >= 1e9 else f"{cap / 1e6:.1f} مليون$"


def _nasdaq_rows():
    """كل أسهم ناسداك من السكرينر الرسمي: [(الرمز، القيمة السوقية، حجم اليوم، السعر)]."""
    url = ("https://api.nasdaq.com/api/screener/stocks"
           "?tableonly=true&limit=10000&exchange=nasdaq&download=true")
    r = requests.get(url, headers={**HEADERS, "Accept": "application/json"}, timeout=30)
    data = r.json().get("data") or {}
    rows = data.get("rows") or (data.get("table") or {}).get("rows") or []
    out = []
    for row in rows:
        sym = str(row.get("symbol", "")).strip().upper()
        if sym.isalpha() and len(sym) <= 5:
            out.append((sym, _to_number(row.get("marketCap")), _to_number(row.get("volume")),
                        _to_number(row.get("lastsale"))))
    return out


RSPLIT_ALGO_SYMS = set()   # أسهم قسم التجزئة العكسية (عشان قسم البني ستوك ما يكررها)


def _recent_rsplits(syms, days):
    """{الرمز: (تاريخ آخر تجزئة عكسية، النسبة)} للي سوت تجزئة عكسية خلال آخر days يوم."""
    since = pd.Timestamp.now(tz=NY).date() - pd.Timedelta(days=days)
    out = {}
    for t, df in download_batches(sorted(syms), UNIVERSE_BATCH, period="6mo", interval="1d",
                                  prepost=False, actions=True):
        try:
            if "Stock Splits" not in df:
                continue
            sp = df["Stock Splits"].fillna(0)
            rev = sp[(sp > 0) & (sp < 1)]
            rev = [(pd.Timestamp(i).date(), float(r)) for i, r in rev.items()
                   if pd.Timestamp(i).date() >= since]
            if rev:
                out[t] = rev[-1]
        except Exception:
            continue
    free_memory()
    return out


def _price_universe(min_px, max_px, max_cap, max_n):
    """أسهم ناسداك داخل نطاق السعر (وتحت حد القيمة السوقية لو فيه)، الأنشط أول.
    يرجع [(الرمز، القيمة السوقية)]."""
    picks = []
    for sym, cap, vol, px in _nasdaq_rows():
        if not (min_px <= px <= max_px) or vol < ALGO_MIN_DAY_VOLUME:
            continue
        if max_cap and not (0 < cap <= max_cap):
            continue
        picks.append((vol, sym, cap))
    picks.sort(reverse=True)
    return [(sym, cap) for _, sym, cap in picks[:max_n]]


def get_microcaps():
    """قسم (6): 1$-15$ وسوت تجزئة عكسية آخر 3 شهور. يرجع {الرمز: (القيمة السوقية، ملاحظة)}."""
    global RSPLIT_ALGO_SYMS
    if ONE_LIST:
        return {sym: (None, "") for sym in stocks_only(WATCH_SYMBOLS)}
    try:
        base = _price_universe(ALGO_MIN_PRICE, ALGO_MAX_PRICE, ALGO_MAX_MARKET_CAP, 100_000)
        if not ALGO_RSPLIT_DAYS:
            return {sym: (cap, "") for sym, cap in base[:ALGO_MAX_SYMBOLS]}
        log(f"كشف الخوارزميات: أدور التجزئات العكسية بين {len(base)} سهم سعرها "
            f"{ALGO_MIN_PRICE:g}$-{ALGO_MAX_PRICE:g}$ ...")
        rs = _recent_rsplits([sym for sym, _ in base], ALGO_RSPLIT_DAYS)
        out = {}
        for sym, cap in base:                         # base مرتبة بالأنشط
            if sym in rs and len(out) < ALGO_MAX_SYMBOLS:
                d, ratio = rs[sym]
                out[sym] = (cap, f"تجزئة عكسية: {d:%Y-%m-%d} (كل {1 / ratio:g} أسهم = سهم)")
        RSPLIT_ALGO_SYMS = set(out)
        return out
    except Exception as e:
        log("كشف الخوارزميات: ما قدرت أجيب قائمة الأسهم -", e)
        return {}


def get_pennies():
    """قسم (6ج): 1$-5$ وقيمتها 40 مليون وتحت. يرجع {الرمز: (القيمة السوقية، ملاحظة)}."""
    if ONE_LIST:
        return {}          # نفس منطق (6) بالضبط، فلو اشتغل على نفس القائمة بيكرر التنبيهات
    try:
        return {sym: (cap, "") for sym, cap in _price_universe(
            ALGO_PENNY_MIN_PRICE, ALGO_PENNY_MAX_PRICE, ALGO_PENNY_MAX_MARKET_CAP,
            ALGO_PENNY_MAX_SYMBOLS)}
    except Exception as e:
        log("البني ستوك: ما قدرت أجيب قائمة الأسهم -", e)
        return {}


# ================== (6ب) خوارزميات الأسهم الكبيرة + (6د) الآيس بيرغ ==================
def get_bigcaps():
    """أسهم ناسداك اللي قيمتها السوقية مليار وفوق، الأنشط تداولاً أول. يرجع {الرمز: القيمة السوقية}."""
    if ONE_LIST:
        return {sym: None for sym in stocks_only(WATCH_SYMBOLS)}
    try:
        picks = [(vol, sym, cap) for sym, cap, vol, px in _nasdaq_rows()
                 if cap >= ALGO_BIG_MIN_MARKET_CAP and vol > 0]
        picks.sort(reverse=True)
        return {sym: cap for _, sym, cap in picks[:ALGO_BIG_MAX_SYMBOLS]}
    except Exception as e:
        log("خوارزميات الكبيرة: ما قدرت أجيب القيم السوقية من ناسداك -", e)
        return {}


def _ts_sec(t):
    """وقت الصفقة بالثواني (سريع، لأن الأسهم الكبيرة فيها آلاف الصفقات بكل سحبة)."""
    if isinstance(t, str) and len(t) >= 19:
        base = datetime.fromisoformat(t[:19]).replace(tzinfo=timezone.utc).timestamp()
        frac = t[19:].split("+")[0].rstrip("Z")
        if frac.startswith(".") and len(frac) > 1:
            base += float("0" + frac[:10])
        return base
    return pd.Timestamp(t).timestamp()


class StreakDetector:
    """يعد الصفقات المتتالية بنفس الحجم لكل سهم: أي صفقة بحجم مختلف (أو فاصل أكثر من
    ALGO_BIG_MAX_GAP_SEC ثانية) تقطع السلسلة وتبدأ وحدة جديدة.
    ينبه عند ALGO_BIG_MIN_STREAK، ثم كل ما تتضاعف (600، 1200، 2400 ...).
    same_price=True = لازم نفس السعر بعد (الآيس بيرغ)."""
    def __init__(self, min_streak=None, min_size=0, max_size=None, max_gap=None,
                 realert_min=None, same_price=False):
        self.min_streak = min_streak or ALGO_BIG_MIN_STREAK
        self.min_size = min_size
        self.max_size = ALGO_BIG_MAX_SIZE if max_size is None else max_size   # 0 = بدون حد
        self.max_gap = ALGO_BIG_MAX_GAP_SEC if max_gap is None else max_gap
        self.realert = (ALGO_BIG_REALERT_MIN if realert_min is None else realert_min) * 60
        self.same_price = same_price
        self.st = {}          # الرمز -> السلسلة الحالية
        self.recent = {}      # الرمز -> (deque[(الوقت، رقم الصفقة)], set) لآخر 60 ثانية - لمنع التكرار
        self.alerted = {}     # (الرمز، الحجم) -> وقت آخر تنبيه

    def _dup(self, sym, tid, ts):
        if tid is None:
            return False
        q, ids = self.recent.setdefault(sym, (deque(), set()))
        while q and q[0][0] < ts - 60:
            ids.discard(q.popleft()[1])
        if tid in ids:
            return True
        q.append((ts, tid))
        ids.add(tid)
        return False

    def add(self, sym, trade):
        ts = _ts_sec(trade["t"])
        if self._dup(sym, trade.get("i"), ts):
            return None
        size = float(trade.get("s") or 0)
        price = float(trade.get("p") or 0)
        if size <= 0 or price <= 0:
            return None
        s = self.st.get(sym)
        side = s["side"] if s else 0
        if s and price != s["px"]:
            side = 1 if price > s["px"] else -1       # نفس السعر = نفس جهة اللي قبلها
        moment = round(ts, 3)                         # "نفس اللحظة" = نفس الملي ثانية
        prev_px = s["px"] if s else None
        if s and s["size"] == size and ts - s["last"] <= self.max_gap \
                and (not self.same_price or price == prev_px):
            s["n"] += 1
            s["same"] = s["same"] + 1 if moment == s["moment"] else 1
            s["max_same"] = max(s["max_same"], s["same"])
            s["low"], s["high"] = min(s["low"], price), max(s["high"], price)
            s["value"] += size * price
        else:
            s = {"size": size, "n": 1, "first": ts, "low": price, "high": price,
                 "value": size * price, "buys": 0, "sells": 0, "same": 1, "max_same": 1,
                 "next_alert": self.min_streak}
            self.st[sym] = s
        s["buys"] += side > 0
        s["sells"] += side < 0
        s["last"], s["px"], s["side"], s["moment"] = ts, price, side, moment
        if s["n"] < s["next_alert"] or size < self.min_size \
                or (self.max_size and size > self.max_size):
            return None
        s["next_alert"] *= 2
        k = (sym, size, price if self.same_price else None)
        first_alert = s["n"] == self.min_streak
        last = self.alerted.get(k)
        if first_alert and last is not None and ts - last < self.realert:
            return None
        self.alerted[k] = ts
        return {"size": size, "count": s["n"], "first_t": s["first"], "last_t": ts,
                "low": s["low"], "high": s["high"], "last": price, "value": s["value"],
                "buys": s["buys"], "sells": s["sells"], "max_same": s["max_same"],
                "update": not first_alert}


def _ice_message(sym, a, cap=None):
    secs = a["last_t"] - a["first_t"]
    b, s_, total = a["buys"], a["sells"], a["count"]
    t1 = pd.Timestamp(a["first_t"], unit="s", tz="UTC").tz_convert(LOCAL_TZ)
    t2 = pd.Timestamp(a["last_t"], unit="s", tz="UTC").tz_convert(LOCAL_TZ)
    head = ("🔁 تحديث: الآيس بيرغ مستمر" if a["update"] else
            "🧊 آيس بيرغ — صفقات متتالية بنفس الحجم ونفس السعر")
    return (f"{head}\n"
            f"السهم: ${sym}\n"
            + (f"القيمة السوقية: {_cap_txt(cap)}\n" if cap else "")
            + f"الحجم: {a['size']:g} سهم × {total:,} صفقة ورا بعض\n"
            f"السعر: {a['last']:.2f} (نفس السعر كلها)\n"
            f"المبلغ: ≈ {a['value']:,.0f}$ ({a['size'] * total:,.0f} سهم)\n"
            f"خلال: {secs:.1f} ثانية | أكثر عدد صفقات بنفس اللحظة: {a['max_same']}\n"
            + _side_lines(b, s_, total, a["size"])
            + f"المصدر: {ALGO_FEED.upper()} عبر Alpaca (كل البورصات)"
            + (f" - متأخر {ALGO_DELAY_MIN - 1} دقيقة" if ALGO_DELAY_MIN else "") + "\n"
            f"من {t1:%H:%M:%S} إلى {t2:%H:%M:%S} (توقيتك)")


def _big_message(sym, a, cap=None):
    secs = max(a["last_t"] - a["first_t"], 0.001)
    b, s_, total = a["buys"], a["sells"], a["count"]
    t1 = pd.Timestamp(a["first_t"], unit="s", tz="UTC").tz_convert(LOCAL_TZ)
    t2 = pd.Timestamp(a["last_t"], unit="s", tz="UTC").tz_convert(LOCAL_TZ)
    if a.get("one_side") == "buy":
        head = "🟢🤖 خوارزمية شراء كامل — صفقات سهم واحد متتالية"
    elif a.get("one_side") == "sell":
        head = "🔴🤖 خوارزمية بيع كامل — صفقات سهم واحد متتالية"
    else:
        head = ("🔁 تحديث: السلسلة مستمرة" if a["update"] else
                "🏦🤖 خوارزمية على سهم كبير — صفقات متتالية بنفس الحجم")
    return (f"{head}\n"
            f"السهم: ${sym}\n"
            + (f"القيمة السوقية: {_cap_txt(cap)}\n" if cap else "")
            + f"الحجم المتكرر: {a['size']:g} سهم\n"
            f"عدد الصفقات المتتالية: {total:,} (ولا صفقة بحجم ثاني بينها)\n"
            f"المدة: {secs:.1f} ثانية (≈ {total / secs:.0f} صفقة/ثانية)\n"
            f"أكثر عدد صفقات بنفس اللحظة: {a['max_same']}\n"
            f"قيمتها: ≈ {a['value']:,.0f}$\n"
            f"السعر: ${a['last']:.2f} (من {a['low']:.2f} إلى {a['high']:.2f})\n"
            + _side_lines(b, s_, total, a["size"])
            + f"المصدر: {ALGO_FEED.upper()} عبر Alpaca"
            + (f" (متأخر {ALGO_DELAY_MIN - 1} دقيقة)" if ALGO_DELAY_MIN else "") + "\n"
            f"من {t1:%H:%M:%S} إلى {t2:%H:%M:%S} (توقيتك)")


def algo_big_loop():
    det = StreakDetector() if ALGO_BIG else None
    ice = (StreakDetector(ALGO_ICE_MIN_STREAK, ALGO_ICE_MIN_SIZE, ALGO_ICE_MAX_SIZE,
                          ALGO_ICE_MAX_GAP_SEC, ALGO_ICE_REALERT_MIN, same_price=True)
           if ALGO_BIG and ALGO_ICE else None)
    last_end, was_on = None, None
    caps, caps_day = {}, None
    while True:
        try:
            now = pd.Timestamp.now(tz="UTC")
            end = now - pd.Timedelta(minutes=ALGO_DELAY_MIN)
            end_ny = end.tz_convert(NY)
            on = (end_ny.weekday() < 5 and (9, 30) <= (end_ny.hour, end_ny.minute) < (16, 0)
                  if ALGO_BIG_REGULAR_ONLY else trading_hours(end_ny))
            if on != was_on:
                log("خوارزميات الكبيرة: " + ("بدأ المراقبة" if on else "السوق مسكر، أنتظر"))
                was_on = on
            if not on:
                last_end = None
                time.sleep(60)
                continue
            today = pd.Timestamp.now(tz=NY).date()
            if caps_day != today or not caps:
                caps = (get_bigcaps() if ONE_LIST or not ALGO_BIG_SYMBOLS
                        else {s_: None for s_ in ALGO_BIG_SYMBOLS})
                caps_day = today
                log(f"خوارزميات الكبيرة: يراقب {len(caps)} سهم (قائمة المراقبة) - شراء كامل/بيع كامل - تنبيه عند "
                    f"{ALGO_BIG_MIN_STREAK} صفقة متتالية بنفس الحجم ({ALGO_BIG_MAX_SIZE:g} أسهم وأقل)"
                    + (f" | الآيس بيرغ: {ALGO_ICE_MIN_STREAK} صفقة متتالية بنفس الحجم والسعر" if ALGO_ICE else ""))
            syms = list(caps)
            if not syms:
                time.sleep(300)
                continue
            start = last_end or end - pd.Timedelta(seconds=60)
            got = None
            for i in range(0, len(syms), ALGO_BIG_CHUNK):
                part = fetch_alpaca_trades(syms[i:i + ALGO_BIG_CHUNK], start, end)
                if part is not None:
                    got = got or {}
                    got.update(part)
            if got is not None:
                last_end = end
                for sym, trades in got.items():
                    for tr in sorted(trades, key=lambda x: x.get("t", "")):
                        res = det.add(sym, tr) if det is not None else None
                        if res and not res["update"]:      # تنبيه واحد لكل سلسلة
                            directional = res["buys"] + res["sells"]
                            need = ALGO_BIG_ONE_SIDE_PCT / 100
                            if directional and res["buys"] / directional >= need:
                                res["one_side"] = "buy"
                            elif directional and res["sells"] / directional >= need:
                                res["one_side"] = "sell"
                            else:
                                res = None                 # مخلوطة بيع وشراء: ما ينبه
                            if res:
                                send_telegram(_big_message(sym, res, caps.get(sym)), kind="algo_big", sym=sym)
                        if ice is not None:
                            res = ice.add(sym, tr)
                            if res:
                                send_telegram(_ice_message(sym, res, caps.get(sym)), kind="ice", sym=sym)
                del got
        except Exception as e:
            log("خوارزميات الكبيرة: خطأ -", e)
        time.sleep(ALGO_BIG_POLL_SEC)


def _once_load(tag):
    """آخر تنبيه لكل سهم في هالقسم: {الرمز: الوقت}."""
    out = {}
    for line in _load_set(ALGO_ONCE_FILE):
        try:
            t, sym, ts = line.split("|")
            if t == tag:
                ts = pd.Timestamp(ts)
                out[sym] = max(ts, out.get(sym, ts))
        except Exception:
            continue
    return out


def algo_loop(name, section, get_universe, fixed=None, exclude=None, once_hours=0,
              det_cls=None, msg_fn=None):
    """يشتغل بخيط لحاله في الخلفية، عشان ما يتأخر بسبب الفحوصات الثانية الطويلة.
    get_universe يرجع {الرمز: (القيمة السوقية، ملاحظة)} - تتجدد مرة باليوم.
    exclude = دالة ترجع أسهم ما نراقبها هنا (موجودة بقسم ثاني).
    once_hours = تنبيه واحد بس لكل سهم، وبعدها يسكت عنه كذا ساعة (0 = بدون حد)."""
    det = (det_cls or AlgoDetector)()
    msg_fn = msg_fn or _algo_message
    once_tag = section
    once_last = _once_load(once_tag) if once_hours else {}
    last_end = None
    was_on = None
    caps, caps_day = {}, None
    while True:
        try:
            now = pd.Timestamp.now(tz="UTC")
            end = now - pd.Timedelta(minutes=ALGO_DELAY_MIN)
            on = trading_hours(end.tz_convert(NY))
            if on != was_on:
                log(f"{name}: " + ("بدأ المراقبة" if on else "السوق مسكر، أنتظر"))
                was_on = on
            if not on:
                last_end = None
                time.sleep(60)
                continue
            today = pd.Timestamp.now(tz=NY).date()
            if caps_day != today or not caps:
                caps = {s_: (None, "") for s_ in fixed} if fixed else get_universe()
                caps_day = today
                log(f"{name}: ألباكا ({ALGO_FEED}"
                    + (f"، متأخر {ALGO_DELAY_MIN - 1} دقيقة" if ALGO_DELAY_MIN else "، لحظي")
                    + f") - يراقب {len(caps)} سهم ({section}): "
                    + ", ".join(list(caps)[:30]) + (" ..." if len(caps) > 30 else ""))
                if not caps:
                    time.sleep(600)                   # ما لقى أسهم، يعيد المحاولة بعد 10 دقايق
                    caps_day = None
                    continue
            skip = exclude() if exclude else set()
            syms = [x for x in caps if x not in skip]
            if not syms:
                time.sleep(300)
                continue
            # نرجع شوي لورا عشان الصفقات المتأخرة، والتكرار ينشال بأرقام الصفقات
            start = (last_end or end - pd.Timedelta(seconds=60)) - pd.Timedelta(seconds=5)
            got = None
            for i in range(0, len(syms), 30):
                part = fetch_alpaca_trades(syms[i:i + 30], start, end)
                if part is not None:
                    got = got or {}
                    got.update(part)
            if got is not None:
                last_end = end
                for sym, trades in got.items():
                    for tr in sorted(trades, key=lambda x: x.get("t", "")):
                        res = det.add(sym, tr)
                        if res:
                            if once_hours:
                                now_utc = pd.Timestamp.now(tz="UTC")
                                prev = once_last.get(sym)
                                if prev is not None and now_utc - prev < pd.Timedelta(hours=once_hours):
                                    continue        # جاه تنبيه خلال آخر 24 ساعة، يسكت
                                once_last[sym] = now_utc
                                _append_line(ALGO_ONCE_FILE, f"{once_tag}|{sym}|{now_utc.isoformat()}")
                            cap, note = caps.get(sym, (None, ""))
                            send_telegram(msg_fn(sym, res, cap, section, note), kind="algo", sym=sym)
        except Exception as e:
            log(f"{name}: خطأ -", e)
        time.sleep(ALGO_POLL_SEC)


def start_algo_thread():
    if not ENABLE_ALGO:
        log("كشف الخوارزميات: مطفي (حط ALPACAAPIKEY و ALPACASECRETKEY في Railway عشان يشتغل)")
        return
    if ALGO_SMALL:
        sec = (f"{ALGO_MIN_PRICE:g}$-{ALGO_MAX_PRICE:g}$"
               + (f" + تجزئة عكسية آخر {ALGO_RSPLIT_DAYS} يوم" if ALGO_RSPLIT_DAYS else ""))
        threading.Thread(target=algo_loop, daemon=True, name="algo",
                         args=("كشف الخوارزميات (تجزئة عكسية)", sec, get_microcaps, ALGO_SYMBOLS,
                               None, ALGO_SMALL_ONCE_HOURS)).start()
    if ALGO_PENNY:
        sec = (f"بني ستوك {ALGO_PENNY_MIN_PRICE:g}$-{ALGO_PENNY_MAX_PRICE:g}$ وقيمتها "
               f"{ALGO_PENNY_MAX_MARKET_CAP / 1e6:g} مليون وتحت")
        threading.Thread(target=algo_loop, daemon=True, name="algo_penny",
                         args=("خوارزميات البني ستوك", sec, get_pennies, None,
                               lambda: RSPLIT_ALGO_SYMS, ALGO_PENNY_ONCE_HOURS)).start()
    if ALGO_BIG:   # (6ب) + (6د) يشتركون بنفس الصفقات
        threading.Thread(target=algo_big_loop, daemon=True, name="algo_big").start()


def algo_self_test():
    global ALGO_MIN_VALUE
    t0 = pd.Timestamp("2026-01-02T15:00:00Z")
    # شرط القيمة: 300 صفقة بسهم واحد على 2.27$ = 681$ بس، فما ينبه
    det = AlgoDetector()
    small = [det.add("YJ", {"i": k + 1, "s": 1, "p": 2.27, "t": t0 + pd.Timedelta(milliseconds=k * 700)})
             for k in range(320)]
    assert not any(small), "تنبيه على مبلغ صغير"
    print(f"ALGO TEST OK: 300 trades worth ~681$ ignored (min {ALGO_MIN_VALUE:,.0f}$)")
    saved, ALGO_MIN_VALUE = ALGO_MIN_VALUE, 0
    det = AlgoDetector(); alerts = []
    for k in range(650):          # 650 صفقة بحجم سهم واحد خلال 3 دقايق وشوي، السعر يطلع
        tr = {"i": k + 1, "s": 1, "p": 0.50 + (k % 5) * 0.001,
              "t": t0 + pd.Timedelta(milliseconds=k * 300)}
        a = det.add("TEST", tr)
        if a: alerts.append(a)
    for k in range(400):          # صفقات حجمها كبير = تتجاهل
        a = det.add("BIG", {"i": k + 1, "s": 500, "p": 1.0, "t": t0 + pd.Timedelta(seconds=k)})
        assert a is None
    assert [a["count"] for a in alerts] == [300, 600], [a["count"] for a in alerts]
    ALGO_MIN_VALUE = saved
    print("ALGO TEST OK: 300 / 600 same-size trades")
    print(_algo_message("TEST", alerts[-1], 12_300_000))

    # (6ب) الكبيرة: 1100 صفقة متتالية بحجم سهم واحد (كل 3 ورا بعض بنفس اللحظة)، ثم صفقة بحجم ثاني تقطعها
    det = StreakDetector(); big = []
    for k in range(1100):
        tr = {"i": k + 1, "s": 1, "p": 180.00 - (k // 50) * 0.01,
              "t": (t0 + pd.Timedelta(milliseconds=(k // 3) * 40)).strftime("%Y-%m-%dT%H:%M:%S.%f000Z")}
        a = det.add("BIGCAP", tr)
        if a: big.append(a)
    assert det.add("BIGCAP", {"i": 1101, "s": 1, "p": 180, "t": "2026-01-02T15:00:00.000000000Z"}) is None  # مكرر
    det.add("BIGCAP", {"i": 9999, "s": 37, "p": 179.9, "t": "2026-01-02T15:00:10Z"})   # حجم ثاني = تنقطع
    for k in range(ALGO_BIG_MIN_STREAK - 1):   # أقل من الحد بوحدة = ما ينبه
        a = det.add("BIGCAP", {"i": 10000 + k, "s": 1, "p": 179.9, "t": t0 + pd.Timedelta(seconds=11 + k * 0.01)})
        assert a is None
    # تنبيه عند الحد (300)، وعند الضعف (600) تحديث - والتشغيل يرسل الأول بس (تنبيه واحد لكل سلسلة)
    assert [a["count"] for a in big] == [ALGO_BIG_MIN_STREAK, ALGO_BIG_MIN_STREAK * 2], [a["count"] for a in big]
    assert not big[0]["update"] and big[1]["update"]
    for k in range(1300):         # حجم 100 (أكبر من 10) = يتجاهل
        assert det.add("BIG100", {"i": k + 1, "s": 100, "p": 50, "t": t0 + pd.Timedelta(milliseconds=k * 10)}) is None
    assert big[0]["max_same"] == 3
    print(f"ALGO BIG TEST OK: {ALGO_BIG_MIN_STREAK} consecutive same-size trades")

    # (6د) آيس بيرغ: 600 صفقة × سهم واحد على 228.15 ورا بعض (بعد صفقة أقل سعر = شراء)
    ice = StreakDetector(ALGO_ICE_MIN_STREAK, ALGO_ICE_MIN_SIZE, ALGO_ICE_MAX_SIZE,
                         ALGO_ICE_MAX_GAP_SEC, ALGO_ICE_REALERT_MIN, same_price=True)
    ice.add("NVDA", {"i": 1, "s": 13, "p": 228.10, "t": t0})
    got = [a for k in range(600) if (a := ice.add("NVDA", {"i": k + 2, "s": 1, "p": 228.15,
                                                         "t": t0 + pd.Timedelta(milliseconds=50 * k)}))]
    assert [a["count"] for a in got] == [500] and got[0]["buys"] == 500, got
    # حجم 70 (أكبر من 10) = يتجاهل
    for k in range(300):
        assert ice.add("MSFT", {"i": k, "s": 70, "p": 400, "t": t0 + pd.Timedelta(milliseconds=50 * k)}) is None
    # نفس الحجم بس السعر تغير = تنقطع
    ice2 = StreakDetector(ALGO_ICE_MIN_STREAK, ALGO_ICE_MIN_SIZE, ALGO_ICE_MAX_SIZE,
                          ALGO_ICE_MAX_GAP_SEC, ALGO_ICE_REALERT_MIN, same_price=True)
    for k in range(1000):
        assert ice2.add("AMD", {"i": k, "s": 1, "p": 150 + (k % 2) * 0.01,
                                "t": t0 + pd.Timedelta(milliseconds=50 * k)}) is None
    # فاصل أكثر من ثانيتين = تنقطع
    for k in range(1000):
        assert ice2.add("AAPL", {"i": k, "s": 1, "p": 200, "t": t0 + pd.Timedelta(seconds=3 * k)}) is None
    print("ICEBERG TEST OK: 500 same-size same-price trades (1-10 shares)")
    print(_ice_message("NVDA", got[0], 5_500_000_000_000))
    print(_big_message("BIGCAP", big[0], 45_600_000_000))


# ================== (1-24) الإنفيرجن على 24 ساعة ==================
_I24_BARS_URL = "https://data.alpaca.markets/v2/stocks/bars"
_i24_feed_warned = set()


def _i24_fetch_bars(symbols, start, feed):
    """شموع 15 دقيقة من ألباكا. يرجع {الرمز: DataFrame بتوقيت نيويورك}."""
    out = {}
    # ألباكا ما تعرف المؤشرات (^GSPC) ولو انرسل واحد ترفض الدفعة كاملة
    symbols = [x for x in symbols if x.replace(".", "").isalpha()]
    hdr = {"APCA-API-KEY-ID": ALPACA_KEY, "APCA-API-SECRET-KEY": ALPACA_SECRET}
    for i in range(0, len(symbols), 100):
        params = {"symbols": ",".join(symbols[i:i + 100]), "timeframe": "15Min",
                  "start": start.tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
                  "limit": 10000, "feed": feed, "adjustment": "raw", "sort": "asc"}
        raw = {}
        for _ in range(200):
            try:
                r = requests.get(_I24_BARS_URL, headers=hdr, params=params, timeout=30)
            except Exception as e:
                log(f"الإنفيرجن 24: ألباكا ({feed}): فشل الاتصال - {e}")
                break
            if r.status_code == 429:
                time.sleep(3)
                continue
            if r.status_code != 200:
                if feed not in _i24_feed_warned:
                    _i24_feed_warned.add(feed)
                    log(f"الإنفيرجن 24: ألباكا ({feed}): خطأ {r.status_code} - {r.text[:200]}")
                break
            data = r.json()
            for sym, bars in (data.get("bars") or {}).items():
                raw.setdefault(sym, []).extend(bars or [])
            token = data.get("next_page_token")
            if not token:
                break
            params["page_token"] = token
        for sym, bars in raw.items():
            if not bars:
                continue
            df = pd.DataFrame(bars)
            idx = pd.to_datetime(df["t"], utc=True).dt.tz_convert(NY)
            df = pd.DataFrame({"Open": df["o"].astype(float), "High": df["h"].astype(float),
                               "Low": df["l"].astype(float), "Close": df["c"].astype(float)}
                              ).set_index(pd.DatetimeIndex(idx))
            out[sym] = df.sort_index()
    return out


def _i24_merge(day, night):
    """النهار (SIP) من 4 الفجر لين 8 بالليل، والليل (BOATS) من 8 بالليل لين 4 الفجر."""
    parts = []
    if day is not None and not day.empty:
        h = day.index.hour
        parts.append(day[(h >= 4) & (h < 20)])
    if night is not None and not night.empty:
        h = night.index.hour
        parts.append(night[(h >= 20) | (h < 4)])
    if not parts:
        return pd.DataFrame(columns=OHLC)
    df = pd.concat(parts).sort_index()
    return df[~df.index.duplicated(keep="first")]


def _i24_frame(df, minutes):
    """شموع 15 دقيقة → شموع (ساعة/4 ساعات) على 24 ساعة، بداية اليوم 8 بالليل نيويورك."""
    df = df.dropna(subset=OHLC)
    if df.empty:
        return df
    if df.index.tz is None:
        df = df.tz_localize("UTC")
    df = df.tz_convert(NY)
    m = df.index.hour * 60 + df.index.minute
    offset = ((m - 20 * 60) % 1440) % minutes
    start = df.index.floor("min") - pd.to_timedelta(offset, unit="m")
    out = df.groupby(start).agg(Open=("Open", "first"), High=("High", "max"),
                                Low=("Low", "min"), Close=("Close", "last"),
                                n=("Close", "size"))
    out["end"] = out.index + pd.Timedelta(minutes=minutes)
    return out


def _i24_closed(c, now):
    return c if c.empty else c[(c["end"] <= now).values]


def _i24_pattern(c, min_size, strict=False):
    """آخر 4 شموع مقفلة: جاب بين الأولى والثالثة، الثانية تغطيه، والرابعة تقفل وراه."""
    if len(c) < 4:
        return None
    c1, c2, c3, c4 = (c.iloc[i] for i in (-4, -3, -2, -1))
    info = {"price": c4["Close"], "open": c4["Open"], "candle_time": c.index[-1], "end": c4["end"]}
    res = None
    if c1["Low"] > c3["High"]:
        lo, hi = c3["High"], c1["Low"]
        if c2["High"] >= hi and c2["Low"] <= lo and c4["Close"] > hi:
            res = {"side": "bull", "gap_bottom": lo, "gap_top": hi, **info}
    if res is None and c1["High"] < c3["Low"]:
        lo, hi = c1["High"], c3["Low"]
        if c2["High"] >= hi and c2["Low"] <= lo and c4["Close"] < lo:
            res = {"side": "bear", "gap_bottom": lo, "gap_top": hi, **info}
    if not res or round(res["gap_top"] - res["gap_bottom"], 4) <= min_size:
        return None
    res["candles"] = c.iloc[-4:]
    if not strict:
        return res
    bull = res["side"] == "bull"
    for a, b in ((c1, c2), (c2, c3)):
        if b["Low"] > a["High"] or b["High"] < a["Low"]:
            return None
    if bull and not (c2["Low"] < c1["Low"] and c3["Low"] < c2["Low"]
                     and c2["High"] < c1["High"] and c3["High"] < c2["High"]):
        return None
    if not bull and not (c2["High"] > c1["High"] and c3["High"] > c2["High"]
                         and c2["Low"] > c1["Low"] and c3["Low"] > c2["Low"]):
        return None
    if bull != (c4["Close"] > c4["Open"]):
        return None
    return res


def _i24_message(t, res, frame):
    lo, hi, px = (round(float(res[k]), 2) for k in ("gap_bottom", "gap_top", "price"))
    if res["side"] == "bull":
        head, line = f"🟢 Inversion Gap - {frame}", f"الشمعة قفلت فوق أعلى الـ IFVG ({hi})"
    else:
        head, line = f"🔴 Inversion Gap - {frame}", f"الشمعة قفلت تحت أسفل الـ IFVG ({lo})"
    closed_at = pd.Timestamp(res["end"]).tz_convert(LOCAL_TZ)
    msg = (f"{head}\n"
           f"السهم: ${t}\n"
           f"IFVG: {lo} ← {hi}  (حجمه {hi - lo:.2f}$)\n"
           f"{line}\n"
           f"سعر الإغلاق: {px}\n"
           f"وقت الإغلاق: {closed_at:%H:%M} (توقيتك)")
    cs = res.get("candles")
    if IFVG_SHOW_CANDLES and cs is not None:
        rows = []
        for k, (ts, r) in enumerate(cs.iterrows(), 1):
            lt = pd.Timestamp(ts).tz_convert(LOCAL_TZ)
            col = "🟢" if r["Close"] > r["Open"] else "🔴"
            rows.append(f"{k}) {lt:%m/%d %H:%M} {col} أعلى {r['High']:.2f} | أقل {r['Low']:.2f}")
        msg += "\nالشموع (بتوقيتك):\n" + "\n".join(rows)
    return msg


def _i24_load(symbols, now):
    start = now - pd.Timedelta(days=IFVG24_LOOKBACK_DAYS)
    day = _i24_fetch_bars(symbols, start, IFVG24_DAY_FEED)
    night = _i24_fetch_bars(symbols, start, IFVG24_NIGHT_FEED)
    if not night:
        log(f"الإنفيرجن 24: ⚠️ ما جات بيانات ليل من ألباكا ({IFVG24_NIGHT_FEED}) - الشموع بتكون ناقصة")
    return {s: _i24_merge(day.get(s), night.get(s)) for s in symbols}


def scan_ifvg24(symbols, sent):
    now = pd.Timestamp.now(tz=NY)
    data = _i24_load(symbols, now)
    frames = [(on, minutes, tag, label, size, strict) for on, minutes, tag, label, size, strict in (
        (ENABLE_IFVG24_4H, 240, "4h24", "فريم 4 ساعات (24 ساعة)", IFVG24_4H_MIN_SIZE, IFVG24_STRICT_4H),
        (ENABLE_IFVG24_1H, 60, "1h24", "فريم ساعة (24 ساعة)", IFVG24_1H_MIN_SIZE, False)) if on]
    hits = {tag: 0 for _, _, tag, _, _, _ in frames}
    for t, df in data.items():
        try:
            if df.empty:
                continue
            for _, minutes, tag, label, size, strict in frames:
                res = _i24_pattern(_i24_closed(_i24_frame(df, minutes), now), size, strict)
                if not res or (now - pd.Timestamp(res["end"])).total_seconds() / 60 > IFVG24_MAX_ALERT_DELAY_MIN:
                    continue
                key = f"{t}-{tag}-{res['side']}-{res['candle_time']}"
                if key in sent:
                    continue
                sent.add(key)
                _append_line(IFVG24_SENT_FILE, key)
                hits[tag] += 1
                msg = _i24_message(t, res, label)
                if IFVG24_GAMMA:
                    msg = with_gamma(msg, t, float(res["price"]))
                send_telegram(msg, kind="gap", sym=t)
        except Exception as e:
            log(f"الإنفيرجن 24: {t}: خطأ - {e}")
    log(f"[{datetime.now():%H:%M}] الإنفيرجن 24 ساعة: {len(data)} سهم — "
        + " + ".join(f"{n} تنبيه ({'4 ساعات' if tag == '4h24' else 'ساعة'})" for tag, n in hits.items()))


def _i24_weekend(now):
    """من 8:30 بالليل الجمعة لين 7:30 بالليل الأحد نيويورك ما فيه تداول."""
    wd, m = now.weekday(), now.hour * 60 + now.minute
    return (wd == 4 and m >= 20 * 60 + 30) or wd == 5 or (wd == 6 and m < 19 * 60 + 30)


def ifvg24_run_forever():
    if not (ALPACA_KEY and ALPACA_SECRET):
        log("الإنفيرجن 24: ❌ يحتاج ALPACAAPIKEY و ALPACASECRETKEY - القسم مطفي")
        return
    log(f"الإنفيرجن 24 ساعة: بدأ - النهار {IFVG24_DAY_FEED.upper()}، الليل {IFVG24_NIGHT_FEED.upper()}، "
        f"{len(WATCH_SYMBOLS)} رمز")
    sent = _load_set(IFVG24_SENT_FILE)
    try:
        scan_ifvg24(list(WATCH_SYMBOLS), sent)   # فحص أول ما يشتغل (ينبه بس لو الشمعة قفلت من أقل من 45 دقيقة)
    except Exception as e:
        log(f"الإنفيرجن 24: خطأ - {e}")
    done = set()
    while True:
        try:
            now = pd.Timestamp.now(tz=NY)
            if not _i24_weekend(now):
                base = now.floor("h")
                for d in IFVG24_SCAN_AFTER_MIN:
                    slot = base + pd.Timedelta(minutes=d)
                    if slot <= now < slot + pd.Timedelta(minutes=4) and slot not in done:
                        done.add(slot)
                        scan_ifvg24(list(WATCH_SYMBOLS), sent)
            done = {x for x in done if now - x < pd.Timedelta(hours=6)}
        except Exception as e:
            log(f"الإنفيرجن 24: خطأ - {e}")
        time.sleep(20)


def ifvg24_self_test():
    """python gap_scanner.py --ifvg24test — يجرب التقسيم والنموذج على شموع وهمية بدون نت."""
    idx = pd.date_range("2026-10-12 20:00", periods=4 * 16, freq="15min", tz=NY)
    plan = [(110, 112, 108, 108.5), (108.5, 109, 105, 105.5), (105.5, 106, 103, 103.5),
            (103.5, 111, 103.4, 110)]
    rows = []
    for o, h, lo, cl in plan:
        for k in range(16):
            px = o + (cl - o) * k / 15
            rows.append({"Open": px, "High": max(px, o) + 0.01, "Low": min(px, o) - 0.01, "Close": px})
        rows[-16]["High"], rows[-15]["Low"] = h, lo
    full = pd.DataFrame(rows, index=idx)
    h = full.index.hour
    merged = _i24_merge(full[(h >= 4) & (h < 20)], full[(h >= 20) | (h < 4)])
    c = _i24_frame(merged, 240)
    starts = [f"{t:%H:%M}" for t in c.index]
    assert starts == ["20:00", "00:00", "04:00", "08:00"], starts
    assert list(c["n"]) == [16] * 4
    res = _i24_pattern(_i24_closed(c, idx[-1] + pd.Timedelta(minutes=20)), IFVG24_4H_MIN_SIZE, True)
    assert res and res["side"] == "bull", res
    print(_i24_message("TEST", res, "فريم 4 ساعات (24 ساعة)"))
    assert len(_i24_frame(merged, 60)) == 16
    print("TEST OK")


def main():
    if "--algotest" in sys.argv:
        algo_self_test()
        return
    if "--pwltest" in sys.argv:
        pwl_self_test()
        return
    if "--pd1dtest" in sys.argv:
        pd1d_self_test()
        return
    if "--pd1dnow" in sys.argv:   # تجربة حقيقية: python short_bot.py --pd1dnow [--send] [NVDA ...]
        _load_chats()
        syms = [a.upper() for a in sys.argv[1:] if not a.startswith("--")] or list(WATCH_SYMBOLS)
        day, hits, ready = pd1d_scan(syms)
        if "--send" in sys.argv:
            pd1d_send(day, hits, prefix="🧪 تجربة\n")
        else:
            for t, s, r in hits:
                print(_pd1d_line(t, s, r) + "\n")
            print(f"{day}: {len(hits)} سحب من {ready} سهم")
        return
    if "--pw4hnow" in sys.argv:   # تجربة حقيقية: python short_bot.py --pw4hnow [--send]
        _load_chats()
        pw4h_now(list(WATCH_SYMBOLS), send="--send" in sys.argv)
        return
    if "--frimontest" in sys.argv:
        frimon_self_test()
        return
    if "--wkopttest" in sys.argv:
        wkopt_self_test()
        return
    if "--ifvgtest" in sys.argv:
        ifvg_self_test()
        return
    if "--gextest" in sys.argv:
        gex_self_test()
        return
    if "--gexnow" in sys.argv:    # تجربة حقيقية: python short_bot.py --gexnow [--send] [NVDA SPY ...]
        _load_chats()
        syms = [a.upper() for a in sys.argv[1:] if not a.startswith("--")] or GEX_SYMBOLS or list(WATCH_SYMBOLS)
        if "--send" in sys.argv:
            gex_daily_send(syms, prefix="🧪 تجربة\n")
        else:
            lines, miss = gex_daily_lines(syms)
            print("\n\n".join(lines) + (f"\n\nما فيه بيانات: {' '.join(miss)}" if miss else ""))
        return
    if "--ifvg24test" in sys.argv:
        ifvg24_self_test()
        return
    once = "--once" in sys.argv
    _load_chats()
    discover_groups()
    log(f"التنبيهات بتروح لـ {len(CHATS)} محادثة: {', '.join(CHATS) or 'ولا وحدة'}")
    if TEST_ON_START and not once:
        pw4h = [n for on, n in ((ENABLE_PWL_4H, "دعم"), (ENABLE_PWH_4H, "مقاومة")) if on]
        pw4h_txt = (f" + سحب {' و'.join(pw4h)} الأسبوع السابق 4 ساعات (كول/بوت، {len(WATCH_SYMBOLS)} رمز)"
                    if pw4h else "")
        pd1h = [n for on, n in ((ENABLE_PDL_1H, "دعم"), (ENABLE_PDH_1H, "مقاومة")) if on]
        if pd1h:
            pw4h_txt += f" + سحب {' و'.join(pd1h)} اليوم السابق فريم ساعة (ذيل بس)"
        if ENABLE_PD1D:
            pw4h_txt += " + قائمة سحب قمة/قاع أمس (إغلاق يومي، كل يوم بعد الإغلاق)"
        if ENABLE_WKOPT:
            pw4h_txt += (f" + سحب السيولة الأسبوعي 4 ساعات مع عقد (الأسهم {WKOPT_MIN_PRICE}$-{WKOPT_MAX_PRICE}$، "
                         "تنبيه واحد لكل سهم بالأسبوع)")
        if ENABLE_IFVG and (ENABLE_IFVG_1H or ENABLE_IFVG_4H):
            fr = [n for on, n in ((ENABLE_IFVG_1H, "ساعة"), (ENABLE_IFVG_4H, "4 ساعات")) if on]
            pw4h_txt += f" + الإنفيرجن IFVG فريم {' و'.join(fr)} ({len(WATCH_SYMBOLS)} رمز)"
        if ENABLE_IFVG24 and (ENABLE_IFVG24_1H or ENABLE_IFVG24_4H):
            fr = [n for on, n in ((ENABLE_IFVG24_1H, "ساعة"), (ENABLE_IFVG24_4H, "4 ساعات")) if on]
            pw4h_txt += f" + الإنفيرجن 24 ساعة فريم {' و'.join(fr)}"
        send_telegram("🧪 رسالة اختبار - بوت الشورت اشتغل\n"
                      "الأقسام: " + " + ".join(n for on, n in (
                          (ENABLE_BORROW_ZERO and (BZ_ZERO_ALERTS or BZ_DROP_ALERTS), "الشورت صفر"),
                          (ENABLE_BORROW_ZERO and BZ_WEEKLY_ZERO, "قائمة الشورت صفر الأسبوعية"),
                          (ENABLE_ALGO and ALGO_SMALL, "خوارزميات التقطيع"),
                          (ENABLE_ALGO and ALGO_PENNY, "خوارزميات البني ستوك"),
                          (ENABLE_ALGO and ALGO_BIG, "خوارزميات الأسهم الكبيرة"),
                          (ENABLE_ALGO and ALGO_BIG and ALGO_ICE, "الآيس بيرغ"),
                          (ENABLE_FRIMON, "سحب الجمعة/الاثنين (كول)"),
                          (ENABLE_RSPLIT_SHORT, "التجزئة العكسية")) if on)
                      + (f" + تقرير القاما اليومي ({len(GEX_SYMBOLS or WATCH_SYMBOLS)} رمز، "
                         f"{GEX_DAILY_AT_NY[0]}:{GEX_DAILY_AT_NY[1]:02d} نيويورك)" if ENABLE_GEX_DAILY else "")
                      + f"{pw4h_txt}\n"
                      f"الوقت: {pd.Timestamp.now(tz=LOCAL_TZ):%Y-%m-%d %H:%M} (توقيتك)")
    if not once:
        start_algo_thread()
        if ENABLE_FRIMON:        # (11) سحب قمة الجمعة/الاثنين + دعم الأسبوع السابق → كول
            threading.Thread(target=frimon_run_forever, daemon=True, name="frimon").start()
        if ENABLE_BORROW_ZERO:   # الشورت صفر اللحظي
            threading.Thread(target=bz_run_forever, daemon=True, name="borrow_zero").start()
        if ENABLE_IFVG24 and (ENABLE_IFVG24_1H or ENABLE_IFVG24_4H):   # (1-24) الإنفيرجن على 24 ساعة
            threading.Thread(target=ifvg24_run_forever, daemon=True, name="ifvg24").start()

    pwl_last = 0.0
    ifvg_last = None
    was_open = None
    gap_sent = _load_set(GAP_SENT_FILE)       # مفاتيح تنبيهات سحب الأسبوع السابق (4 ساعات)
    rsplit_new_sent = _load_set(RSPLIT_NEW_FILE)
    rsplit_state = _rsplit_state()

    while True:
        discover_groups()

        # (1ك-2) سحب سيولة دعم ومقاومة الأسبوع السابق - فريم 4 ساعات - كل 5 دقايق وقت السوق
        # + (1ي) سحب دعم ومقاومة اليوم السابق - فريم ساعة (نفس الفحص ونفس البيانات)
        if (ENABLE_PWL_4H or ENABLE_PWH_4H or ENABLE_WKOPT or ENABLE_PDL_1H or ENABLE_PDH_1H) \
                and (once or us_market_open()) \
                and time.time() - pwl_last >= PWL_EVERY_MIN * 60:
            scan_pwl_4h(list(WATCH_SYMBOLS), gap_sent)
            pwl_last = time.time()

        # (1) الإنفيرجن IFVG - فريم ساعة و4 ساعات - بعد إغلاق كل ساعة بدقيقة
        if ENABLE_IFVG and (ENABLE_IFVG_1H or ENABLE_IFVG_4H):
            now_ny = pd.Timestamp.now(tz=NY)
            slot = ifvg_scan_due(now_ny, ifvg_last)
            if once or (slot is not None and us_market_open(now_ny, overnight=False)):
                scan_ifvg(list(WATCH_SYMBOLS), gap_sent, now_ny)
                ifvg_last = slot or now_ny

        # (15) تقرير القاما اليومي - قبل الافتتاح، مرة باليوم (بخيط لحاله)
        if not once:
            gex_daily_maybe_start()
            # (1ي-2) قائمة سحب قمة/قاع أمس - أول ما يشتغل + كل يوم بعد الإغلاق (بخيط لحاله)
            pd1d_maybe_start(list(WATCH_SYMBOLS))

        # (4ب) التجزئة العكسية - الجديد كل يوم، وقائمة كل جمعة
        if ENABLE_RSPLIT_SHORT:
            rsplit_job(rsplit_state, rsplit_new_sent, force=once)

        is_open = us_market_open()
        if not is_open and was_open is not False:
            log(f"[{datetime.now():%H:%M}] السوق مسكر، أنتظر...")
        was_open = is_open

        if once:
            break
        time.sleep(LOOP_SLEEP_SEC)


if __name__ == "__main__":
    main()
