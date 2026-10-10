"""
بوت التنبيهات - يشتغل على Railway ويرسل على تيليجرام
=====================================================

(1) نموذج الـ IFVG - ثلاث فريمات: يومي + 4 ساعات + ساعة
    اليومي: يفحص مرة باليوم بعد إغلاق السوق (4:20 العصر نيويورك = 11:20 بالليل بتوقيتك)
    الأسهم: كل أسهم ناسداك + بورصة نيويورك (GAP_EXCHANGES) اللي قيمتها السوقية 2 مليار دولار وفوق
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

    📦 صناديق SPY و QQQ داخلة في فريم الساعة والأربع ساعات بس (GAP_ETFS)

    فلتر: السهم سعره فوق 10$ ، وحجم الجاب (الفرق بين الحدين) 1$ أو أكثر (الساعة والأربع ساعات)

    ⭐ فريم 4 ساعات له شروط أشد (check_pattern_4h):
      - بدون شرط حجم الجاب (GAP4H_MIN_SIZE = 0)
      - أسهم ناسداك بس، قيمتها السوقية 2 مليار وفوق (GAP4H_NASDAQ_ONLY)
      - الشموع الثلاث متراصة هابطة وما بينها فراغ (ذيل كل وحدة يلمس اللي قبلها)
      - لونها ما يهم (GAP4H_REQUIRE_RED = True يخليها لازم حمراء)
      - الرابعة خضراء وتقفل فوق قاع الأولى (والهبوطي بالعكس)

(1ج) IFVG فريم 15 دقيقة - قسم جديد (الساعة والأربع ساعات ما تغيروا)
    - نفس الأسهم: ناسداك 2 مليار وفوق، وسعر السهم 10$ وفوق
    - نفس النموذج بالضبط (صعودي وهبوطي) + شرط: الشموع الثلاث ما بينها فراغ
        * ورا بعض بالوقت (ما فيه قفزة بين جلستين)
        * كل شمعة تفتح عند إغلاق اللي قبلها، وذيولها تلتقي
    - الرابعة تقفل فوق أعلى الجاب (صعودي) أو تحت أسفله (هبوطي) - لونها ما يهم
    - حجم الجاب 2$ أو أكثر
    - ENABLE_GAP_15M_CLEAN = False يطفيه

(1د) سحب سيولة دعمين - الفريم اليومي
    - الأسهم: ناسداك + نيويورك اللي قيمتها السوقية 2 مليار دولار وفوق، وسعرها 5$ وفوق
    - الدعم = قاع يومي سابق (أنزل من 3 شموع قبله و3 بعده) خلال آخر 60 يوم،
      وما قفلت ولا شمعة تحته من يوم تكوّن (يعني الدعم لسا صامد)
    - الشرط: شمعة اليوم ذيلها نزل تحت دعمين أو أكثر، وقفلت فوقهم كلهم
    - يفحص مرة باليوم بعد الإغلاق (4:20 العصر نيويورك = 11:20 بالليل بتوقيتك)
    - ENABLE_SWEEP = False يطفيه | python gap_scanner.py --sweeptest يجربه بدون نت

(1و) سحب سيولة دعمين - الفريم الأسبوعي
    - الأسهم: ناسداك + نيويورك اللي قيمتها السوقية 10 مليار دولار وفوق
    - الدعم = قاع أسبوعي سابق (أنزل من شمعتين قبله وشمعتين بعده) خلال آخر سنة، ولسا صامد
    - الشرط: شمعة الأسبوع ذيلها نزل تحت دعمين أو أكثر، وقفلت فوقهم كلهم
    - يفحص كل جمعة بعد الإغلاق (4:20 العصر نيويورك = 11:20 بالليل بتوقيتك)
    - ENABLE_WSWEEP = False يطفيه | python gap_scanner.py --wsweeptest يجربه بدون نت

(2) ماسح السيولة (البني ستوك) - كل 5 دقايق وقت السوق الرسمي
    - أسهم ناسداك من 1$ إلى 5$
    - الشروط كلها مع بعض:
        * الحجم النسبي: حجم اليوم 5 أضعاف متوسط آخر 20 يوم أو أكثر
        * اختراق: السعر فوق أعلى قمة آخر 20 يوم، وقريب من قمة اليوم (ما رجع أكثر من 3%)
        * الفلوت أقل من 20 مليون سهم
        * طالع 5% أو أكثر عن إغلاق أمس
    - كل سهم يتنبه عليه مرة وحدة باليوم

(3) نموذج القاع المزدوج (W) - الفريم اليومي - أسهم ناسداك 2 مليار وفوق
    - قاعين متقاربين (فرق 3% أو أقل) + اختراق خط العنق لفوق خلال آخر أسبوعين (10 أيام تداول)
    - رسالة وحدة بالأسبوع: كل جمعة بعد إغلاق السوق، فيها كل الأسهم

(4) الشورت صفر - أسهم ناسداك من 0.10$ إلى 15$
    - إذا بيانات الشورت الرسمية (من ياهو) صارت صفر  =>  تنبيه
    - البيانات الرسمية تنزل مرتين بالشهر وبتأخير أسبوعين تقريباً، فيفحصها مرة باليوم

(4ب) التجزئة العكسية - أسهم ناسداك
    - كل يوم سوق (بعد 10 الصبح نيويورك): يرسل الأسهم اللي سوت تجزئة عكسية جديدة بس
      ولو ما فيه جديد ما يرسل شي
    - لكل سهم: تاريخ التجزئة، النسبة، سعر الافتتاح بعدها، السعر الحين، وكم مرة سوى تجزئة عكسية بالسنة
    - كل جمعة: قائمة بتجزئات الأسبوع | أول كل شهر: قائمة بتجزئات الشهر اللي راح
    - وتنبيه لو سهم جديد منها سعره 5$ أو أقل والشورت عنده صفر

التشغيل:
  pip install yfinance pandas requests lxml pillow
  python gap_scanner.py          # يشتغل باستمرار
  python gap_scanner.py --once   # فحص مرة وحدة بس
  python gap_scanner.py --test   # يجرب نموذج الجاب على مثال NVDA (بدون نت)
  python gap_scanner.py --algotest   # يجرب كشف الأوامر المتكررة (بدون نت)

(6) كشف خوارزميات التقطيع - من ألباكا
    - الأسهم: أسهم ناسداك اللي سعرها من 1$ إلى 15$ وسوت تجزئة عكسية خلال آخر 3 شهور
    - يدور على صفقات صغيرة (10 أسهم وأقل) بنفس الحجم بالضبط، مثل 1، 1، 1، 1...
    - تنبيه لو تكررت 300 مرة أو أكثر خلال 5 دقايق، وقوي عند 600
    - يقدّر هل غالبها شراء ولا بيع من اتجاه السعر (تقريبي)
    - البيانات من كل البورصات (sip) بتأخير 15 دقيقة في باقة ألباكا المجانية
    - يحتاج المتغيرين ALPACAAPIKEY و ALPACASECRETKEY في Railway

(6ج) خوارزميات البني ستوك - نفس منطق (6) بالضبط
    - الأسهم: ناسداك من 1$ إلى 5$ وقيمتها السوقية 40 مليون دولار وتحت (أنشط 300)
    - ALGO_PENNY=0 يطفيه
    - تنبيه واحد بس لكل سهم كل 24 ساعة (ALGO_PENNY_ONCE_HOURS، ونفسه للتجزئة العكسية ALGO_SMALL_ONCE_HOURS)

(6د) الآيس بيرغ - نفس أسهم (6ب) (ناسداك مليار وفوق)
    - 500 صفقة أو أكثر ورا بعض بنفس الحجم ونفس السعر بالضبط، والفاصل بين كل صفقتين ثانيتين أو أقل
    - حجم الصفقة من سهم إلى 10 أسهم (سهم سهم سهم ...)، ويرسل تحديث عند 1000 ثم 2000 ...
    - ALGO_ICE=0 يطفيه

(6ب) خوارزميات الأسهم الكبيرة - صفقات متتالية بنفس الحجم - من ألباكا
    - الأسهم: أسهم ناسداك اللي قيمتها السوقية مليار دولار وفوق (أنشط 200)
    - صفقات حجمها 10 أسهم وأقل: تنبيه لما تجي 600 صفقة أو أكثر ورا بعض بنفس الحجم بالضبط،
      وما بينها ولا صفقة بحجم ثاني، والفاصل بين كل صفقتين 5 ثواني أو أقل
    - يوضح كم صفقة منها نزلت بنفس اللحظة، والمدة، والقيمة، وتقدير شراء/بيع
    - لو السلسلة كملت يرسل تحديث عند 1200 ثم 2400 ...
    - نفس مفاتيح ألباكا | ALGO_BIG=0 يطفيه | ALGO_SMALL=0 يطفي القسم (6)

(7) الأخبار الإيجابية - من ألباكا (نفس المفاتيح) - 24 ساعة، كل دقيقة
    - اندماج/استحواذ، موافقة FDA، نتائج دراسة إيجابية، عقود وشراكات، نتائج قوية ورفع توقعات،
      ترقية محلل، إعادة شراء وتوزيعات
    - يتجاهل الخبر لو فيه كلمة سلبية (طرح أسهم، تجزئة عكسية، دعوى، تخفيض، إفلاس، إلغاء ...)
    - الأسهم: سعرها من 1$ إلى 15$ وقيمتها السوقية من 5 مليون إلى 100 مليون دولار
    - NEWS=0 يطفيه
    - python gap_scanner.py --newstest   # يجرب التصنيف (بدون نت)

(8) صياد العقود THE LEGENDARY 🗽⚡️ - داخل هذا الملف (قسم 8 تحت قبل main)
    - يشتغل في Thread لحاله وقت السوق الرسمي (9:30 - 4 نيويورك)
    - 20 سهم: AXON COIN T CRWD SWKS MU HOOD TSLA META AAPL
              SPCX HPE VST MET INTC AMD AVGO PLTR NFLX ORCL
      (تغيرها بمتغير LEGENDARY_SYMBOLS في Railway)
    - يتوقع منطقة الارتداد قبل ما يوصلها السعر: طالع لمنطقة رفض = PUT، نازل لمنطقة دعم = CALL
    - يختار العقد (السترايك + الانتهاء)، يرسل التنبيه مع صورة، ويتابع العقد لين يوصل الهدف
    - البيانات: Polygon (POLYGON_API_KEY) + Tradier اختياري للعقود (TRADIER_API_TOKEN)
    - التنبيهات تروح لنفس قروبات السكانر. LEGENDARY_OWN_TG=1 يرجعها لقناة البوت الأصلية
    - pip install pillow (للصورة بس؛ بدونه يرسل التنبيه بدون صورة)
    - LEGENDARY=0 يطفيه | python gap_scanner.py --optionstest يجرب الإرسال والتشغيل
"""

import gc
import io
import logging
import os
import random
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import csv
import math
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from zoneinfo import ZoneInfo

import pandas as pd
import requests

try:   # لصورة عقد صياد العقود (اختياري)
    from PIL import Image, ImageDraw, ImageFont
except Exception:
    Image = ImageDraw = ImageFont = None

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
GAP_EXTENDED = True              # يشمل ما قبل الفتح وبعد الإغلاق (4 الفجر - 8 بالليل نيويورك)

# الجلسة الليلية (8 بالليل - 4 الفجر نيويورك) = إعداد الـ24 ساعة في تريدنج فيو
# ياهو ما يعطيها، فتجي من Tiingo: حط المفتاح كمتغير TIINGO_TOKEN على Railway
TIINGO_TOKEN = os.environ.get("TIINGO_TOKEN", "")
GAP_OVERNIGHT = bool(TIINGO_TOKEN)   # يتفعل لحاله لو حطيت المفتاح
TIINGO_WORKERS = 8

GAP_MIN_STOCK_PRICE = 10         # يتجاهل الأسهم اللي سعرها أقل من كذا (لفريم 4 ساعات والساعة)
GAP_MIN_SIZE = 1.00              # فريم الساعة والأربع ساعات: يتجاهل الجاب اللي حجمه أقل من 1$
ENABLE_GAP_4H = True             # فريم 4 ساعات - ينبه عند إغلاق الشمعة
# ---- شروط فريم 4 ساعات (خاصة فيه، الساعة واليومي ما تغيروا) ----
GAP4H_MIN_SIZE = 0               # فريم 4 ساعات: بدون شرط حجم الجاب
GAP4H_REQUIRE_RED = False        # True = الشموع الثلاث لازم حمراء | False = لونها ما يهم
GAP4H_REQUIRE_STEP = True        # الشموع الثلاث متراصة: كل وحدة أنزل من اللي قبلها (صعودي) وأعلى (هبوطي)
GAP4H_REQUIRE_COLOR4 = True      # الرابعة خضراء (صعودي) أو حمراء (هبوطي)
GAP4H_MIN_FILL = 0.9             # كل شمعة لازم فيها 90% من شموع الربع ساعة وأكثر، وإلا بياناتها ناقصة وتنرفض
GAP_SHOW_CANDLES = True          # يكتب الشموع الأربع (وقت، أعلى، أقل) في التنبيه عشان تقارنها بالشارت
ENABLE_GAP_1H = True             # فريم ساعة - ينبه عند إغلاق الشمعة
ENABLE_GAP_15M = False           # فريم 15 دقيقة - مطفي
ENABLE_GAP_1D = True             # فريم يومي - ينبه بعد إغلاق السوق كل يوم
GAP_1D_AFTER_NY = (16, 20)       # يفحص بعد الإغلاق: 4:20 العصر نيويورك = 11:20 بالليل بتوقيتك
GAP_1D_MIN_SIZE = 0.50           # أقل حجم للجاب اليومي (دولار)

# ---- فريم 15 دقيقة له قائمة أسهم مستقلة: من 1$ إلى 15$ وبدون شرط القيمة السوقية ----
GAP15_MIN_PRICE = 1              # أقل سعر لأسهم فريم 15 دقيقة
GAP15_MAX_PRICE = 15             # أعلى سعر لأسهم فريم 15 دقيقة
GAP15_MIN_AVG_VOLUME = 100_000   # يشيل الأسهم الميتة اللي ما عليها تداول
GAP15_MIN_SIZE = 0.05            # الجاب على الأسهم الرخيصة أصغر، فحجم أقل
# ---- (1ج) جاب 15 دقيقة "النظيف": نفس أسهم الساعة والأربع ساعات (ناسداك 2 مليار وفوق، سعر 10$ وفوق) ----
#   الشرط الزايد: الشموع الثلاث ما بينها فراغ، والجاب دولارين أو أكثر
ENABLE_GAP_15M_CLEAN = True      # True = شغال | False = مطفي
GAP15C_MIN_SIZE = 2.00           # أقل حجم للجاب (دولار)
GAP15C_OPEN_TOL = 0.01           # سماحية فرق الافتتاح عن إغلاق الشمعة اللي قبلها (سنت واحد)
# ---- (1هـ) قائمة المراقبة الخاصة: IFVG على 15 دقيقة + ساعة + 4 ساعات، الجاب أكثر من 15 سنت ----
#   الجاب 15 سنت أو أقل يتجاهله. الأسهم هذي تنشال من الفحص العادي عشان ما يجيك تنبيهين
ENABLE_WATCH = True              # True = شغال | False = مطفي
WATCH_SYMBOLS = [
    "TSLA", "AAPL", "NVDA", "MSFT", "INTC", "MSTR", "COIN", "SPCX", "CRCL", "OKTA",
    "META", "AVGO", "NOW", "ORCL", "LLY", "CRWD", "GOOGL", "ADBE", "SNDK", "AMD",
    "MU", "DELL", "QCOM", "RKLB", "CRDO",
]
WATCH_MIN_SIZE = 0.16            # حجم الجاب: أكثر من 15 سنت (يعني 16 سنت وفوق) | 0 = بدون شرط
GAP_REQUIRE_MIDDLE_COVER = True  # الشمعة الثانية لازم تغطي الجاب كامل (من قمة الثالثة لقاع الأولى)
GAP_BASE_MIN = 15                # البيانات تنحمّل بشموع 15 دقيقة، وكل الفريمات تنبني منها
GAP_SCAN_AFTER_CLOSE_MIN = (1, 5, 12)   # يفحص بعد الإغلاق بكذا دقيقة (الأولى هي الأساسية)
GAP_MAX_ALERT_DELAY_MIN = 30     # ما ينبه على شمعة قفلت من أكثر من كذا دقيقة (عشان ما يرسل قديم أول ما يشتغل)
GAP_SENT_FILE = "gap_sent.txt"   # عشان ما يعيد نفس التنبيه لو البوت أعاد التشغيل

# ---- (1د) سحب سيولة دعمين - الفريم اليومي ----
#   شمعة اليوم ذيلها نزل تحت دعمين (قاعين سابقين) وقفلت فوقهم الاثنين
ENABLE_SWEEP = True              # True = شغال | False = مطفي
SWEEP_MIN_MARKET_CAP = 2_000_000_000   # القيمة السوقية 2 مليار دولار وفوق (ناسداك + نيويورك)
SWEEP_MIN_SUPPORTS = 2           # كم دعم لازم ينسحب بنفس الشمعة
SWEEP_PIVOT_BARS = 3             # الدعم = قاع أنزل من 3 شموع قبله و3 بعده
SWEEP_LOOKBACK = 60              # يدور على الدعوم خلال آخر 60 يوم تداول (3 شهور تقريباً)
SWEEP_MERGE_PCT = 0.003          # دعمين الفرق بينهم أقل من 0.3% = نفس الدعم (ما ينحسبون اثنين)
SWEEP_MIN_PRICE = 5              # يتجاهل الأسهم اللي سعرها أقل من كذا
SWEEP_AFTER_NY = (16, 20)        # يفحص بعد الإغلاق: 4:20 العصر نيويورك = 11:20 بالليل بتوقيتك

# ---- (1و) سحب سيولة دعمين - الفريم الأسبوعي ----
ENABLE_WSWEEP = True             # True = شغال | False = مطفي
WSWEEP_MIN_MARKET_CAP = 10_000_000_000   # القيمة السوقية 10 مليار دولار وفوق (ناسداك + نيويورك)
WSWEEP_PIVOT_BARS = 2            # الدعم الأسبوعي = قاع أنزل من شمعتين قبله وشمعتين بعده
WSWEEP_LOOKBACK = 52             # يدور على الدعوم خلال آخر 52 أسبوع (سنة)
WSWEEP_WEEKDAY = 4               # الجمعة
WSWEEP_AFTER_NY = (16, 20)       # بعد الإغلاق: 4:20 العصر نيويورك = 11:20 بالليل بتوقيتك
WSWEEP_WEEK_FILE = "wsweep_week.txt"   # عشان ما يرسل مرتين بنفس الأسبوع لو البوت أعاد التشغيل

USE_PRICE_FILTER = False         # True = يطبق فلتر السعر تحت مع فلتر القيمة السوقية
MIN_PRICE = 50
MAX_PRICE = 500

# ---- (2) الأخبار - 24 ساعة ----
ENABLE_FLOW = True               # ماسح السيولة للبني ستوك
FLOW_MIN_PRICE = 1               # أقل سعر
FLOW_MAX_PRICE = 5               # أعلى سعر
FLOW_MIN_AVG_VOLUME = 100_000    # يشيل الأسهم الميتة
FLOW_RVOL = 5                    # حجم اليوم لازم يكون كذا ضعف متوسط آخر 20 يوم
FLOW_AVG_DAYS = 20               # عدد الأيام لمتوسط الحجم وقمة الاختراق
FLOW_MAX_FLOAT = 20_000_000      # الفلوت أقل من كذا سهم
FLOW_MIN_CHANGE = 0.05           # طالع 5% أو أكثر عن إغلاق أمس
FLOW_MAX_PULLBACK = 0.03         # ما رجع أكثر من 3% عن قمة اليوم
FLOW_EVERY_MIN = 5               # كل كم دقيقة يفحص
FLOW_SENT_FILE = "flow_sent.txt" # عشان ما يعيد نفس السهم بنفس اليوم

# ---- (3) نماذج الفريم اليومي ----
ENABLE_DAILY = True
ENABLE_DOUBLE_BOTTOM = True      # W
DAILY_MIN_PRICE = 1              # أقل سعر سهم
DAILY_MIN_AVG_VOLUME = 300_000   # يشيل الأسهم الميتة (عدد أسهم يومي)
DAILY_WEEKDAY = 4                # يرسل مرة بالأسبوع: 4 = الجمعة (0 = الاثنين)
DAILY_AFTER_NY = (16, 15)        # بعد إغلاق السوق الجمعة (4:15 العصر نيويورك = 11:15 بالليل بتوقيتك)
DAILY_WEEK_FILE = "daily_week.txt"   # عشان ما يرسل مرتين بنفس الأسبوع لو البوت أعاد التشغيل
DOUBLE_TOLERANCE = 0.03          # 3% أقصى فرق بين القاعين أو القمتين
PATTERN_MIN_DEPTH = 0.04         # خط العنق لازم يبعد عن القاع/القمة 4% على الأقل (عشان يشيل النماذج الصغيرة)
PIVOT_BARS = 5                   # القمة/القاع لازم تكون أعلى/أنزل من 5 شموع قبلها و5 بعدها
PATTERN_MIN_BARS = 10            # أقل مسافة بين القاعين/القمتين (أيام تداول)
PATTERN_MAX_BARS = 120           # أقصى طول للنموذج (تقريباً 6 شهور)
DAILY_LOOKBACK_DAYS = 10         # النماذج اللي اخترقت خلال آخر أسبوعين (10 أيام تداول)
DAILY_MIN_MARKET_CAP = 2_000_000_000   # نموذج W على الأسهم اللي قيمتها 2 مليار وفوق بس

# ---- (4) الشورت صفر ----
ENABLE_SHORT = True             # الشورت صفر شغال
SHORT_MIN_PRICE = 0.10
SHORT_MAX_PRICE = 15
SHORT_MIN_AVG_VOLUME = 50_000
SHORT_WORKERS = 3
SHORT_SENT_FILE = "short_sent.txt"   # عشان ما يعيد نفس التنبيه لو البوت أعاد التشغيل

# ---- (4ب) تجزئة عكسية + شورت صفر (أسهم البني ستوك) ----
ENABLE_RSPLIT_SHORT = True
RSPLIT_MAX_PRICE = 5                 # الشورت صفر: يفحصه لأسهم البني ستوك (5$ أو أقل) من اللي سوت تجزئة
RSPLIT_NEW_DAYS = 4                  # "جديد" = تجزئة صارت خلال آخر كذا يوم (يغطي الويكند) وما انرسلت قبل
RSPLIT_CHECK_AFTER_NY = 10           # الفحص اليومي بعد الساعة 10 الصبح نيويورك (عشان سعر الافتتاح يكون موجود)
RSPLIT_WORKERS = 3
RSPLIT_SENT_FILE = "rsplit_sent.txt"     # تنبيهات الشورت صفر
RSPLIT_NEW_FILE = "rsplit_new.txt"       # التجزئات الجديدة اللي انرسلت
RSPLIT_WEEKLY = True                 # قائمة كل جمعة بتجزئات آخر 7 أيام
RSPLIT_MONTHLY = True                # قائمة أول كل شهر بتجزئات الشهر اللي راح
RSPLIT_STATE_FILE = "rsplit_state.txt"   # يحفظ آخر يوم/أسبوع/شهر انرسل عشان ما يتكرر

# ---- (6) كشف خوارزميات التنفيذ (أوامر متكررة بنفس الحجم) - من ألباكا ----
# يراقب الصفقات لحظياً (بورصة IEX المجانية) ويدور على صفقات ورا بعض بنفس الحجم بالضبط
# مثال: 1، 1، 1، 1، 1، 1 أو 4، 4، 4، 4، 4، 4 = غالباً خوارزمية تقسيم أو آيس بيرغ
ALPACA_KEY = (os.environ.get("ALPACAAPIKEY") or os.environ.get("ALPACA_API_KEY")
              or os.environ.get("APCA_API_KEY_ID", ""))
ALPACA_SECRET = (os.environ.get("ALPACASECRETKEY") or os.environ.get("ALPACA_SECRET_KEY")
                 or os.environ.get("APCA_API_SECRET_KEY", ""))
ENABLE_ALGO = bool(ALPACA_KEY and ALPACA_SECRET)   # يتفعل لحاله لو المفاتيح موجودة
# sip = كل البورصات (المجاني يعطيها بتأخير 15 دقيقة) | iex = لحظي بس بورصة وحدة صغيرة
# الأسهم الصغيرة تقريباً ما تتداول على IEX، فـ sip أدق بكثير لهالنوع
ALGO_FEED = os.environ.get("ALGO_FEED", "sip").lower()
ALGO_DELAY_MIN = 16 if ALGO_FEED == "sip" else 0   # الباقة المجانية: بيانات sip عمرها 15 دقيقة وفوق
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
ALGO_SMALL_ONCE_HOURS = 24            # قسم التجزئة العكسية (1$-15$): تنبيه واحد لكل سهم كل كذا ساعة (0 = بدون حد)
ALGO_ONCE_FILE = "algo_once.txt"      # يحفظ وقت آخر تنبيه لكل سهم عشان ما يعيده لو البوت أعاد التشغيل
ALGO_REALERT_MIN = 15                 # ما يعيد نفس مستوى التنبيه لنفس السهم والحجم قبل كذا دقيقة

# ---- (6ج) خوارزميات البني ستوك: من 1$ إلى 5$ وقيمتها السوقية 40 مليون وتحت ----
# نفس منطق القسم (6) بالضبط: صفقات 10 أسهم وأقل بنفس الحجم، تنبيه 300 وقوي 600 خلال 5 دقايق
# السهم اللي داخل قائمة التجزئة العكسية (6) ما يتكرر هنا
ALGO_PENNY = os.environ.get("ALGO_PENNY", "1") != "0"   # 0 = يطفي هالقسم
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
ALGO_BIG_MIN_STREAK = 600                 # أقل عدد صفقات متتالية بنفس الحجم
ALGO_BIG_MAX_SIZE = 10                    # حجم الصفقة 10 أسهم أو أقل
ALGO_BIG_MAX_GAP_SEC = 5                  # لو مر أكثر من كذا ثانية بين صفقتين، تنقطع السلسلة
ALGO_BIG_MAX_SYMBOLS = int(os.environ.get("ALGO_BIG_MAX_SYMBOLS", "200"))   # الأنشط أول
ALGO_BIG_SYMBOLS = [s.strip().upper() for s in os.environ.get("ALGO_BIG_SYMBOLS", "").split(",")
                    if s.strip()]         # قائمة ثابتة بدل التلقائية (اختياري)
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

# ---- (7) الأخبار الإيجابية - من ألباكا (نفس المفاتيح) ----
# اندماج، استحواذ، موافقة FDA، عقود وشراكات، نتائج قوية، رفع توقعات، ترقية، إعادة شراء ...
NEWS = os.environ.get("NEWS", "1") != "0"   # 0 = يطفي هالقسم
NEWS_POLL_SEC = 60                    # كل كم ثانية يسحب الأخبار الجديدة (24 ساعة، كل الأيام)
NEWS_MAX_AGE_MIN = 30                 # يتجاهل الخبر اللي عمره أكثر من كذا دقيقة (عشان ما يرسل قديم أول ما يشتغل)
NEWS_MAX_SYMBOLS = 3                  # يتجاهل الخبر اللي فيه أكثر من كذا سهم (ملخصات السوق العامة)
NEWS_MIN_PRICE = 1                    # أقل سعر سهم (0 = بدون حد)
NEWS_MAX_PRICE = 15                   # أعلى سعر سهم (0 = بدون حد)
NEWS_MAX_MARKET_CAP = 100_000_000     # القيمة السوقية أقل من 100 مليون دولار (0 = بدون حد)
NEWS_MIN_MARKET_CAP = 5_000_000       # القيمة السوقية 5 مليون دولار وفوق
NEWS_EXCHANGES = ("nasdaq", "nyse", "amex")   # البورصات اللي تنجاب منها القيم السوقية
NEWS_SENT_FILE = "news_sent.txt"      # عشان ما يعيد نفس الخبر لو البوت أعاد التشغيل

# ---- (8) صياد العقود THE LEGENDARY - الكود كامل في قسم (8) تحت ----
ENABLE_LEGENDARY = os.environ.get("LEGENDARY", "1") != "0"     # 0 = يطفي صياد العقود
LEGENDARY_OWN_TG = os.environ.get("LEGENDARY_OWN_TG", "0") == "1"   # 1 = يرسل لقناة البوت الأصلية بدل قروبات السكانر

# ---- المحتوى التعليمي ----
ADD_EDUCATION = True             # يضيف شرح تعليمي قصير للنموذج تحت كل تنبيه
ADD_DISCLAIMER = True            # يضيف سطر إخلاء المسؤولية تحت كل رسالة
DISCLAIMER = "⚠️ محتوى تعليمي فقط، وليس توصية بيع أو شراء."

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


EDUCATION = {
    "gap": ("📚 للتعلّم - IFVG:\n"
            "IFVG بين ذيل الشمعة الأولى والثالثة. لما تقفل الشمعة الرابعة وراه، ينقلب "
            "من مقاومة لدعم (أو العكس)، وكثير يراقبون إعادة اختبارها.\n"
            "يضعف لو رجع السعر وقفل داخل الـ IFVG، أو كان الحجم ضعيف."),
    "sweep": ("📚 للتعلّم - سحب السيولة:\n"
              "تحت كل قاع واضح تتجمع أوامر وقف خسارة. لما السعر ينزل تحتها ويضربها ثم يرجع ويقفل "
              "فوقها، يعني اللي نزّله أخذ السيولة وما قدر يثبّت تحت.\n"
              "يضعف لو رجع السعر وقفل تحت الدعوم، أو كان حجم شمعة السحب ضعيف."),
    "flow": ("📚 للتعلّم - دخول السيولة:\n"
             "الحجم النسبي يقارن تداول اليوم بمعدّله. حجم أضعاف المعتاد مع اختراق قمة وفلوت صغير "
             "يعني طلب غير عادي على سهم قليل المعروض، فالحركة تكون عنيفة.\n"
             "البني ستوك ترتد بسرعة لو ما وراها سبب حقيقي، والسبريد والتذبذب عالي."),
    "w": ("📚 للتعلّم - القاع المزدوج (W):\n"
          "السعر ينزل لقاع، يرتد، يرجع لنفس المستوى تقريباً ويصمد، ثم يخترق خط العنق "
          "(أعلى نقطة بين القاعين). الاختراق هو التأكيد.\n"
          "يضعف لو رجع السعر تحت خط العنق بعد الاختراق."),
    "short": ("📚 للتعلّم - الشورت صفر:\n"
              "يعني ما فيه مراكز بيع على المكشوف مسجلة في آخر بيانات رسمية. البيانات تنشر مرتين "
              "بالشهر وبتأخير، فالوضع الحالي ممكن يكون تغيّر.\n"
              "صفر أحياناً يعني نقص بيانات أو قيود على الإقراض، مو بالضرورة إشارة إيجابية."),
    "rsplit": ("📚 للتعلّم - التجزئة العكسية:\n"
               "الشركة تدمج أسهمها (مثلاً كل 10 أسهم = سهم) عشان ترفع السعر، غالباً لتفادي "
               "الشطب من البورصة. عدد الأسهم يقل والقيمة ما تتغير.\n"
               "كثير منها يكمل نزول بعدها، وأحياناً يتبعها طرح أسهم جديدة."),
    "algo": ("📚 للتعلّم - خوارزميات التقطيع:\n"
             "مئات الصفقات الصغيرة بنفس الحجم بالضبط (سهم، سهم، سهم...) علامة على برنامج "
             "يقسّم أمر كبير على قطع صغيرة عشان ما يحرك السعر ولا يبان.\n"
             "تقدير الشراء/البيع من اتجاه السعر تقريبي، وفي الأسهم الصغيرة ممكن يكون تلاعب أو صانع سوق."),
    "ice": ("📚 للتعلّم - الآيس بيرغ:\n"
            "أمر كبير مخفي يطلع للسوق على قطع صغيرة بنفس الحجم وعلى نفس السعر، وكل ما تنفذ قطعة "
            "تطلع اللي بعدها. تكرار نفس الحجم على نفس السعر ورا بعض = غالباً أمر واحد كبير.\n"
            "ما يوضح مين وراه، والجهة (شراء/بيع) تقدير من حركة السعر قبله."),
    "algo_big": ("📚 للتعلّم - صفقات متتالية بنفس الحجم:\n"
                 "في سهم كبير عليه آلاف المتداولين، إن مئات الصفقات تجي ورا بعض بنفس الحجم بالضبط "
                 "وبدون ولا صفقة ثانية بينها = غالباً برنامج واحد (TWAP/VWAP أو آيس بيرغ) ينفذ أمر كبير.\n"
                 "ما يوضح مين وراه، وتقدير الشراء/البيع من اتجاه السعر تقريبي."),
    "news": ("📚 للتعلّم - الأخبار:\n"
             "التصنيف \"إيجابي\" آلي من كلمات العنوان، مو قراءة للخبر كامل، فاقرأ الخبر قبل أي قرار.\n"
             "كثير من حركة السعر تصير قبل وصول الخبر، وأحياناً السهم ينزل رغم إن الخبر إيجابي."),
}


def send_telegram(text, kind=None):
    text = "للمتابعة\n" + text
    if ADD_EDUCATION and kind in EDUCATION:
        text += "\n\n" + EDUCATION[kind]
    if ADD_DISCLAIMER:
        text += "\n\n" + DISCLAIMER
    log(text)
    if "ضع_" in TELEGRAM_TOKEN:
        return  # ما حطيت التوكن، يطبع بالشاشة بس
    for chat_id in list(CHATS):
        _send_one(chat_id, text)


def send_options_alert(message, image_path=None):
    """إرسال تنبيهات صياد العقود لنفس قروبات السكانر: النص بتنسيق Markdown + صورة العقد."""
    text = message.strip()
    if ADD_DISCLAIMER:
        text += "\n\n" + DISCLAIMER
    log(text)
    if "ضع_" in TELEGRAM_TOKEN:
        return  # ما حطيت التوكن، يطبع بالشاشة بس
    for chat_id in list(CHATS):
        try:
            r = requests.post(f"{TG_API}/sendMessage",
                              data={"chat_id": chat_id, "text": text, "parse_mode": "Markdown",
                                    "disable_web_page_preview": True}, timeout=10).json()
            if not r.get("ok"):          # لو التنسيق خرب، يرسله نص عادي
                _send_one(chat_id, text.replace("*", "").replace("`", ""))
            if image_path and os.path.exists(image_path):
                with open(image_path, "rb") as ph:
                    requests.post(f"{TG_API}/sendPhoto", data={"chat_id": chat_id},
                                  files={"photo": ph}, timeout=15)
        except Exception as e:
            log(f"صياد العقود: فشل الإرسال لـ {chat_id}:", e)


def start_legendary_thread():
    global EXTERNAL_SENDER
    if not ENABLE_LEGENDARY:
        log("صياد العقود: مطفي (LEGENDARY=0)")
        return
    send = None if LEGENDARY_OWN_TG else send_options_alert
    threading.Thread(target=run_forever, kwargs={"send": send},
                     daemon=True, name="legendary").start()
    log(f"صياد العقود: شغال على {len(TARGET_ASSETS)} سهم: {' '.join(TARGET_ASSETS)}"
        + ("" if Image is not None else "  (بدون صور: pillow مو منزّل)"))


def legendary_self_test():
    """يجرب صياد العقود بدون ما يرسل تيليجرام: الصورة وصياغة الرسالة ومسار الإرسال."""
    global EXTERNAL_SENDER
    sent = []
    EXTERNAL_SENDER = lambda m, img=None: sent.append((m, img))
    img = generate_card_image("TSLA", "CALL", 250, "2026-10-16", mode="PRE-HUNT")
    send_telegram_alert("🗽⚡️ *تجربة صياد العقود*", img)
    EXTERNAL_SENDER = None
    log(f"الأسهم ({len(TARGET_ASSETS)}): {' '.join(TARGET_ASSETS)}")
    log(f"الصورة: {img or 'بدون (pillow مو منزّل)'} | الرسالة وصلت لدالة السكانر: {bool(sent)}")
    log("✅ صياد العقود جاهز" if sent else "❌ فيه مشكلة")
    return bool(sent)


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
    # 20 دقيقة: ياهو أحياناً ما يعطي كل شموع الربع ساعة بعد الإغلاق، فالشمعة تعتبر مقفلة
    # بعد 15 دقيقة (only_closed). لو الوقت أقصر من كذا تضيع آخر شمعة باليوم (4-8 بالليل)
    buf = max(max(GAP_SCAN_AFTER_CLOSE_MIN) + 2, 20)
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


GAP_EXCHANGES = ("nasdaq", "nyse")   # بورصات أسهم الجاب: احذف "nyse" لو تبي ناسداك بس
# صناديق تنضاف لفحص الجاب على فريم الساعة والأربع ساعات بس (صعودي وهبوطي، الجاب 1$ وفوق)
GAP_ETFS = ["SPY", "QQQ"]
GAP4H_NASDAQ_ONLY = True   # فريم 4 ساعات: أسهم ناسداك بس (الساعة واليومي وسحب السيولة ما تغيروا)
GAP_NASDAQ_SET = set()     # تتعبى لحالها من سكرينر ناسداك


def get_gap_universe():
    """أسهم الجاب (4 ساعات، ساعة، يومي): كل البورصات في GAP_EXCHANGES
    اللي قيمتها السوقية MIN_MARKET_CAP وفوق، من سكرينر ناسداك الرسمي."""
    out = set()
    for ex in GAP_EXCHANGES:
        url = ("https://api.nasdaq.com/api/screener/stocks"
               f"?tableonly=true&limit=10000&exchange={ex}&download=true")
        try:
            r = requests.get(url, headers={**HEADERS, "Accept": "application/json"}, timeout=30)
            data = r.json().get("data") or {}
            rows = data.get("rows") or (data.get("table") or {}).get("rows") or []
            n = 0
            for row in rows:
                sym = str(row.get("symbol", "")).strip().upper()
                if sym.isalpha() and len(sym) <= 5 and _to_number(row.get("marketCap")) >= MIN_MARKET_CAP:
                    out.add(sym)
                    if ex == "nasdaq":
                        GAP_NASDAQ_SET.add(sym)
                    n += 1
            log(f"الجاب: {ex.upper()} - {n} سهم")
        except Exception as e:
            log(f"ما قدرت أجيب أسهم {ex.upper()}:", e)
    if len(out) > 50:
        return sorted(out)
    log("قائمة أسهم الجاب رجعت فاضية تقريباً، أستخدم الاحتياطية")
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
    expected = ((c["end"] - starts).dt.total_seconds() / (GAP_BASE_MIN * 60)).round()
    done = (c["end"] <= now) & ((c["n"] >= expected) | (last_bar >= c["end"])
                                | (now >= c["end"] + pd.Timedelta(minutes=15)))
    return c[done.values]


def check_pattern(c):
    """يفحص آخر 4 شموع مقفلة بالاتجاهين. يرجع تفاصيل النموذج لو تحقق، وإلا None.
    لون الشموع ما يهم - المهم الجاب بين ذيل الأولى والثالثة، والثانية تغطي الجاب كامل
    (من قمة الثالثة لقاع الأولى)، والرابعة تقفل وراه."""
    if len(c) < 4:
        return None
    c1, c2, c3, c4 = (c.iloc[i] for i in (-4, -3, -2, -1))
    info = {"price": c4["Close"], "open": c4["Open"], "candle_time": c.index[-1],
            "end": c4["end"] if "end" in c else c.index[-1]}

    # 🟢 صعودي: قاع الأولى فوق قمة الثالثة، والرابعة تقفل فوق أعلى الجاب (الافتتاح ما يهم)
    if ENABLE_BULLISH and c1["Low"] > c3["High"]:
        gap_bottom = c3["High"]   # قمة الشمعة الثالثة
        gap_top = c1["Low"]       # قاع الشمعة الأولى = الخط المطلوب
        covered = c2["High"] >= gap_top and c2["Low"] <= gap_bottom   # الثانية تغطي الجاب كامل
        if (covered or not GAP_REQUIRE_MIDDLE_COVER) and c4["Close"] > gap_top:
            return {"side": "bull", "gap_bottom": gap_bottom, "gap_top": gap_top, **info}

    # 🔴 هبوطي: قمة الأولى تحت قاع الثالثة، والرابعة تقفل تحت أسفل الجاب (الافتتاح ما يهم)
    if ENABLE_BEARISH and c1["High"] < c3["Low"]:
        gap_bottom = c1["High"]   # قمة الشمعة الأولى = الخط المطلوب
        gap_top = c3["Low"]       # قاع الشمعة الثالثة
        covered = c2["High"] >= gap_top and c2["Low"] <= gap_bottom   # الثانية تغطي الجاب كامل
        if (covered or not GAP_REQUIRE_MIDDLE_COVER) and c4["Close"] < gap_bottom:
            return {"side": "bear", "gap_bottom": gap_bottom, "gap_top": gap_top, **info}

    return None


def no_void_between(c, n=3):
    """(1ج) يتأكد إن الشموع الثلاث الأولى (قبل الرابعة) ما بينها فراغ:
    - ورا بعض بالوقت: ما فيه شمعة ناقصة ولا قفزة بين جلستين
    - كل شمعة تفتح عند إغلاق اللي قبلها (بسماحية GAP15C_OPEN_TOL)
    - ذيول الشموع المتجاورة تلتقي (مدى كل وحدة يلمس اللي قبلها)"""
    if len(c) < n + 1:
        return False
    rows = c.iloc[-(n + 1):-1]                   # الأولى والثانية والثالثة
    for i in range(1, n):
        prev, cur = rows.iloc[i - 1], rows.iloc[i]
        if "end" in rows and pd.Timestamp(prev["end"]) != pd.Timestamp(rows.index[i]):
            return False                         # فيه فراغ بالوقت
        if abs(cur["Open"] - prev["Close"]) > GAP15C_OPEN_TOL:
            return False                         # فتحت بفجوة عن إغلاق اللي قبلها
        if cur["Low"] > prev["High"] or cur["High"] < prev["Low"]:
            return False                         # الذيول ما التقت
    return True


def check_pattern_clean(c):
    """نفس check_pattern بالضبط + شرط إن الشموع الثلاث ما بينها فراغ."""
    res = check_pattern(c)
    if res and no_void_between(c):
        return res
    return None


def check_pattern_4h(c):
    """فريم 4 ساعات - الشروط:
    🟢 صعودي:
      1) ثلاث شموع متراصة هابطة: كل شمعة قاعها وقمتها أنزل من اللي قبلها
      2) ما بينها فراغ: ذيل كل شمعة يلمس اللي قبلها (الأولى مع الثانية، والثانية مع الثالثة)
      3) قاع الأولى ما يلتقي مع قمة الثالثة، والفرق بينهم (الجاب) 1$ أو أكثر
      4) الشمعة الرابعة خضراء وتقفل فوق قاع الأولى (أعلى الجاب)
    🔴 هبوطي: نفس الشي بالعكس (متراصة طالعة، والرابعة حمراء تقفل تحت قمة الأولى)."""
    res = check_pattern(c)
    if not res:
        return None
    res["candles"] = c.iloc[-4:]
    if res["gap_top"] - res["gap_bottom"] < GAP4H_MIN_SIZE:
        return None
    c1, c2, c3, c4 = (c.iloc[i] for i in (-4, -3, -2, -1))
    bull = res["side"] == "bull"

    # بيانات كاملة: ياهو في ما قبل الفتح وبعد الإغلاق ينقصه شموع ربع ساعة كثير، فتطلع الشمعة
    # أصغر من الحقيقة في تريدنج فيو ويبان "جاب" وهو مو موجود. نرفض أي شمعة بياناتها ناقصة
    if "n" in c and "end" in c:
        for i in (-4, -3, -2, -1):
            row = c.iloc[i]
            expected = (pd.Timestamp(row["end"]) - pd.Timestamp(c.index[i])).total_seconds() / (GAP_BASE_MIN * 60)
            if expected > 0 and row["n"] / expected < GAP4H_MIN_FILL:
                return None

    # ما بينها فراغ: ذيول الشموع المتجاورة تلتقي
    for a, b in ((c1, c2), (c2, c3)):
        if b["Low"] > a["High"] or b["High"] < a["Low"]:
            return None

    # متراصة: هابطة للصعودي، طالعة للهبوطي
    if GAP4H_REQUIRE_STEP:
        if bull and not (c2["Low"] < c1["Low"] and c3["Low"] < c2["Low"]
                         and c2["High"] < c1["High"] and c3["High"] < c2["High"]):
            return None
        if not bull and not (c2["High"] > c1["High"] and c3["High"] > c2["High"]
                             and c2["Low"] > c1["Low"] and c3["Low"] > c2["Low"]):
            return None

    # لون الشموع الثلاث (اختياري)
    if GAP4H_REQUIRE_RED:
        want_down = bull
        for x in (c1, c2, c3):
            if (x["Close"] < x["Open"]) != want_down:
                return None

    # الرابعة: خضراء تقفل فوق الجاب (صعودي) / حمراء تقفل تحته (هبوطي)
    if GAP4H_REQUIRE_COLOR4:
        if bull and not c4["Close"] > c4["Open"]:
            return None
        if not bull and not c4["Close"] < c4["Open"]:
            return None
    return res


def _gap_message(t, res, frame):
    lo, hi, px = (round(float(res[k]), 2) for k in ("gap_bottom", "gap_top", "price"))
    if res["side"] == "bull":
        head = f"🟢 Inversion Gap - {frame}"
        line = f"الشمعة قفلت فوق أعلى الـ IFVG ({hi})"
    else:
        head = f"🔴 Inversion Gap - {frame}"
        line = f"الشمعة قفلت تحت أسفل الـ IFVG ({lo})"
    closed_at = pd.Timestamp(res["end"]).tz_convert(LOCAL_TZ)
    msg = (f"{head}\n"
           f"السهم: ${t}\n"
           f"IFVG: {lo} ← {hi}  (حجمه {hi - lo:.2f}$)\n"
           f"{line}\n"
           f"سعر الإغلاق: {px}\n"
           f"وقت الإغلاق: {closed_at:%H:%M} (توقيتك)")
    cs = res.get("candles")
    if GAP_SHOW_CANDLES and cs is not None:
        rows = []
        for k, (ts, r) in enumerate(cs.iterrows(), 1):
            lt = pd.Timestamp(ts).tz_convert(LOCAL_TZ)
            col = "🟢" if r["Close"] > r["Open"] else "🔴"
            rows.append(f"{k}) {lt:%m/%d %H:%M} {col} أعلى {r['High']:.2f} | أقل {r['Low']:.2f}")
        msg += "\nالشموع (بتوقيتك):\n" + "\n".join(rows)
    return msg


def _watch_message(t, res, frame):
    """رسالة قائمة المراقبة: IFVG مع الاتجاه 🟢 صعودي / 🔴 هبوطي."""
    lo, hi, px = (round(float(res[k]), 2) for k in ("gap_bottom", "gap_top", "price"))
    closed_at = pd.Timestamp(res["end"]).tz_convert(LOCAL_TZ)
    if res["side"] == "bull":
        head, side = "🟢 Inversion Gap", f"الشمعة قفلت فوق أعلى الـ IFVG ({hi})"
    else:
        head, side = "🔴 Inversion Gap", f"الشمعة قفلت تحت أسفل الـ IFVG ({lo})"
    return (f"{head} - {frame}\n"
            f"السهم: ${t}\n"
            f"IFVG: {lo} ← {hi}  (حجمه {hi - lo:.2f}$)\n"
            f"{side}\n"
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
                                 "resampleFreq": f"{GAP_BASE_MIN}min", "token": TIINGO_TOKEN},
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


def scan_gap(tickers, already_sent, frames=None, min_price=None, max_price=None,
             min_size=None, tag_label="", msg_fn=None):
    """frames = الفريمات اللي يفحصها. لو ما انعطت، يفحص 4 ساعات والساعة بس."""
    hits = 0
    now = pd.Timestamp.now(tz=NY)
    if frames is None:
        frames = [(ENABLE_GAP_4H, 240, "4h", "فريم 4 ساعات", check_pattern_4h),
                  (ENABLE_GAP_1H, 60, "1h", "فريم ساعة")]
    min_price = GAP_MIN_STOCK_PRICE if min_price is None else min_price
    min_size = GAP_MIN_SIZE if min_size is None else min_size
    boats = load_boats(tickers, now) if GAP_OVERNIGHT else {}
    for t, df in download_batches(tickers, 100, period="7d", interval=f"{GAP_BASE_MIN}m",
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
            if last < min_price:
                continue
            if max_price is not None and last > max_price:
                continue
            last_bar = df.index.max()

            for fr in frames:
                enabled, minutes, tag, label = fr[:4]
                checker = fr[4] if len(fr) > 4 else check_pattern
                if not enabled:
                    continue
                if (tag == "4h" and GAP4H_NASDAQ_ONLY and GAP_NASDAQ_SET
                        and t not in GAP_NASDAQ_SET and t not in GAP_ETFS):
                    continue                    # فريم 4 ساعات: ناسداك بس
                res = checker(only_closed(to_frame(df, minutes), last_bar, now))
                # فريم 4 ساعات له حده الخاص (GAP4H_MIN_SIZE) ينفحص داخل check_pattern_4h
                need = min(min_size, GAP4H_MIN_SIZE) if tag == "4h" else min_size
                if not res or round(res["gap_top"] - res["gap_bottom"], 2) < need:
                    continue
                if (now - res["end"]).total_seconds() / 60 > GAP_MAX_ALERT_DELAY_MIN:
                    continue                    # شمعة قديمة، مو إغلاق جديد
                key = f"{t}-{tag}-{res['side']}-{res['candle_time']}"
                if key in already_sent:
                    continue
                already_sent.add(key)
                _append_line(GAP_SENT_FILE, key)
                hits += 1
                send_telegram((msg_fn or _gap_message)(t, res, label), kind="gap")
        except Exception as e:
            log(f"{t}: خطأ - {e}")
    free_memory()
    log(f"[{datetime.now():%H:%M}] الجاب{tag_label}: خلص الفحص - {hits} تنبيه جديد")


def scan_gap_daily(tickers, already_sent):
    """IFVG على الفريم اليومي (الجلسة الرسمية، نفس شموع تريدنج فيو اليومية).
    ينبه بس لو الشمعة الرابعة هي شمعة اليوم (قفلت الحين)."""
    hits = 0
    today = pd.Timestamp.now(tz=NY).date()
    for t, df in download_batches(tickers, 200, period="1mo", interval="1d", prepost=False):
        try:
            df = df.dropna(subset=OHLC)[OHLC].copy()
            if len(df) < 4 or pd.Timestamp(df.index[-1]).date() != today:
                continue
            last = float(df["Close"].iloc[-1])
            if last < GAP_MIN_STOCK_PRICE:
                continue
            days = [pd.Timestamp(d).date() for d in df.index]
            df.index = pd.DatetimeIndex([pd.Timestamp(d, tz=NY) for d in days])
            df["end"] = df.index + pd.Timedelta(hours=16)       # الشمعة اليومية تقفل 4 العصر
            res = check_pattern(df)
            if not res or res["gap_top"] - res["gap_bottom"] < GAP_1D_MIN_SIZE:
                continue
            key = f"{t}-1d-{res['side']}-{today}"
            if key in already_sent:
                continue
            already_sent.add(key)
            _append_line(GAP_SENT_FILE, key)
            hits += 1
            send_telegram(_gap_message(t, res, "فريم يومي"), kind="gap")
        except Exception as e:
            log(f"{t}: خطأ جاب يومي - {e}")
    free_memory()
    log(f"[{datetime.now():%H:%M}] الجاب اليومي: خلص الفحص - {hits} تنبيه جديد")


# ================== (1د) سحب سيولة دعمين - يومي ==================
def check_sweep(df, pivot_bars=None, lookback=None):
    """df = شموع يومية أو أسبوعية (آخر شمعة = الحالية). يرجع التفاصيل لو ذيلها نزل تحت
    SWEEP_MIN_SUPPORTS دعم أو أكثر وقفل فوقهم كلهم، وإلا None."""
    df = df.dropna(subset=OHLC)
    n = SWEEP_PIVOT_BARS if pivot_bars is None else pivot_bars
    lookback = SWEEP_LOOKBACK if lookback is None else lookback
    if len(df) < 2 * n + 3:
        return None
    df = df.iloc[-(lookback + 1):]
    lo, cl = df["Low"].astype(float).values, df["Close"].astype(float).values
    t = len(df) - 1
    low_t, close_t = lo[t], cl[t]

    # القيعان المؤكدة قبل اليوم (لازم 3 شموع بعدها قبل اليوم)
    supports = []
    for i in range(n, t - n):
        win = lo[i - n:i + n + 1]
        if lo[i] != win.min():
            continue
        lvl = lo[i]
        # الدعم لسا صامد: ما قفلت ولا شمعة تحته بعد ما تكوّن (قبل اليوم)
        if (cl[i + 1:t] < lvl).any():
            continue
        # ذيل اليوم تحته والإغلاق فوقه
        if low_t < lvl < close_t:
            supports.append((i, lvl))

    # دمج الدعوم المتقاربة (نفس المستوى تقريباً)
    supports.sort(key=lambda x: x[1])
    merged = []
    for i, lvl in supports:
        if merged and (lvl - merged[-1][1]) / merged[-1][1] < SWEEP_MERGE_PCT:
            continue
        merged.append((i, lvl))
    if len(merged) < SWEEP_MIN_SUPPORTS:
        return None

    vol_rel = None
    if "Volume" in df:
        v = df["Volume"].astype(float).values
        avg = v[max(0, t - 20):t].mean() if t > 0 else 0
        if avg > 0:
            vol_rel = v[t] / avg
    return {"supports": [(df.index[i], lvl) for i, lvl in sorted(merged, key=lambda x: -x[1])],
            "low": low_t, "close": close_t, "open": float(df["Open"].iloc[-1]),
            "high": float(df["High"].iloc[-1]), "vol_rel": vol_rel}


def _sweep_message(t, r, frame="فريم يومي", bar="اليوم", unit="يوم"):
    lines = [f"  • {lvl:.2f}  (قاع {pd.Timestamp(d):%Y-%m-%d})" for d, lvl in r["supports"]]
    deepest = min(lvl for _, lvl in r["supports"])
    msg = (f"💧 سحب سيولة {len(r['supports'])} دعوم - {frame}\n"
           f"السهم: ${t}\n"
           f"الدعوم اللي انسحبت:\n" + "\n".join(lines) + "\n"
           f"أقل سعر {bar}: {r['low']:.2f}  ({(r['low'] / deepest - 1) * 100:.1f}% تحت أنزل دعم)\n"
           f"الإغلاق: {r['close']:.2f}  (فوق الدعوم كلها ✅)\n"
           f"شمعة {bar}: فتح {r['open']:.2f} | أعلى {r['high']:.2f} | "
           f"{'🟢 خضراء' if r['close'] > r['open'] else '🔴 حمراء'}")
    if r.get("vol_rel"):
        msg += f"\nالحجم: {r['vol_rel']:.1f} ضعف متوسط 20 {unit}"
    return msg


def scan_sweep_daily(tickers, already_sent):
    """يفحص شمعة اليوم بعد الإغلاق لكل الأسهم."""
    hits = 0
    today = pd.Timestamp.now(tz=NY).date()
    for t, df in download_batches(tickers, 200, period="6mo", interval="1d", prepost=False):
        try:
            if pd.Timestamp(df.index[-1]).date() != today:
                continue                          # ما فيه شمعة اليوم
            if float(df["Close"].iloc[-1]) < SWEEP_MIN_PRICE:
                continue
            r = check_sweep(df)
            if not r:
                continue
            key = f"{t}-sweep-{today}"
            if key in already_sent:
                continue
            already_sent.add(key)
            _append_line(GAP_SENT_FILE, key)
            hits += 1
            send_telegram(_sweep_message(t, r), kind="sweep")
        except Exception as e:
            log(f"{t}: خطأ سحب السيولة - {e}")
    free_memory()
    log(f"[{datetime.now():%H:%M}] سحب سيولة الدعوم (يومي): خلص الفحص - {hits} تنبيه جديد")


def sweep_self_test():
    """يجرب كشف سحب السيولة على بيانات مصطنعة (بدون نت)."""
    days = pd.bdate_range("2026-06-01", periods=40, tz=NY)
    # سعر يتذبذب ويكوّن قاعين: 95 (يوم 10) و 97 (يوم 22)، واليوم ينزل لـ 94 ويقفل 99
    lows = [100 - (i % 7) * 0.3 for i in range(40)]
    lows[10], lows[22] = 95.0, 97.0
    rows = []
    for i, l in enumerate(lows):
        rows.append((l + 1.0, l + 2.5, l, l + 1.5, 1_000_000))
    rows[-1] = (98.0, 100.0, 94.0, 99.0, 3_000_000)   # شمعة السحب
    df = pd.DataFrame(rows, index=days, columns=OHLC + ["Volume"])
    r = check_sweep(df)
    print(_sweep_message("TEST", r) if r else "ما فيه تنبيه ❌")
    print()
    df2 = df.copy()
    df2.iloc[-1, 3] = 96.0                             # قفل فوق دعم واحد بس
    print("قفل فوق دعم واحد بس:", "تنبيه ❌ (غلط)" if check_sweep(df2) else "ما فيه تنبيه ✅ (صح)")


def scan_sweep_weekly(tickers, already_sent):
    """(1و) يفحص شمعة الأسبوع (بعد إغلاق الجمعة): سحب دعمين أسبوعيين والإغلاق فوقهم."""
    hits = 0
    now = pd.Timestamp.now(tz=NY)
    week_start = (now - pd.Timedelta(days=now.weekday())).date()     # اثنين هالأسبوع
    iso = now.isocalendar()
    wk = f"{iso[0]}-W{iso[1]:02d}"
    for t, df in download_batches(tickers, 200, period="2y", interval="1wk", prepost=False):
        try:
            df = df.dropna(subset=OHLC)
            df = df[~df.index.duplicated(keep="last")]
            if df.empty or pd.Timestamp(df.index[-1]).date() < week_start:
                continue                          # ما فيه شمعة هالأسبوع
            r = check_sweep(df, WSWEEP_PIVOT_BARS, WSWEEP_LOOKBACK)
            if not r:
                continue
            key = f"{t}-wsweep-{wk}"
            if key in already_sent:
                continue
            already_sent.add(key)
            _append_line(GAP_SENT_FILE, key)
            hits += 1
            send_telegram(_sweep_message(t, r, "فريم أسبوعي", "الأسبوع", "أسبوع"), kind="sweep")
        except Exception as e:
            log(f"{t}: خطأ سحب السيولة الأسبوعي - {e}")
    free_memory()
    log(f"[{datetime.now():%H:%M}] سحب سيولة الدعوم (أسبوعي): خلص الفحص - {hits} تنبيه جديد")


def wsweep_self_test():
    """يجرب السحب الأسبوعي على بيانات مصطنعة (بدون نت)."""
    weeks = pd.date_range("2025-10-06", periods=40, freq="W-MON", tz=NY)
    lows = [100 - (i % 5) * 0.4 for i in range(40)]
    lows[12], lows[25] = 95.0, 97.0
    rows = [(l + 1.0, l + 3.0, l, l + 2.0, 5_000_000) for l in lows]
    rows[-1] = (98.0, 101.0, 94.0, 99.5, 12_000_000)
    df = pd.DataFrame(rows, index=weeks, columns=OHLC + ["Volume"])
    r = check_sweep(df, WSWEEP_PIVOT_BARS, WSWEEP_LOOKBACK)
    print(_sweep_message("TEST", r, "فريم أسبوعي", "الأسبوع", "أسبوع") if r else "ما فيه تنبيه ❌")


def gap_scan_due(now, last_run):
    """بعد إغلاق كل شمعة بدقيقة (وإعادة بعد 5 و16 دقيقة). يرجع وقت الجولة لو جا وقتها."""
    step = f"{GAP_BASE_MIN}min"          # كل ربع ساعة تقفل شمعة (15 دقيقة)
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
        path = [o + (c - o) * k / 15 for k in range(16)]
        for k in range(16):                                    # 16 شمعة ربع ساعة لكل 4 ساعات
            op = path[k - 1] if k else o
            rows.append((s + pd.Timedelta(minutes=15 * k), op,
                         h if k == 6 else max(op, path[k]),
                         l if k == 10 else min(op, path[k]), path[k]))
    df = pd.DataFrame(rows, columns=["t"] + OHLC).set_index("t")

    for label, now in (("قبل إغلاق الرابعة (7:59 نيويورك)", "2026-09-28 07:59"),
                       ("بعد الإغلاق بدقيقة (8:01 نيويورك)", "2026-09-28 08:01")):
        now = pd.Timestamp(now, tz=NY)
        part = df[df.index <= now - pd.Timedelta(minutes=15)]
        c = only_closed(to_frame(part, 240), part.index.max(), now)
        res = check_pattern(c)
        print(f"--- {label} ---")
        print(c[OHLC + ["n"]].tail(4).to_string())
        print(_gap_message("NVDA", res, "فريم 4 ساعات") if res else "ما فيه تنبيه")
        print()


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
    stats = _universe_stats(include_nyse)
    keep = [t for t, (last, avg_vol) in stats.items()
            if min_price <= last <= max_price and avg_vol >= min_vol]
    log(f"{label}: {len(keep)} سهم سعرها {min_price}-{max_price}$ وعليها تداول")
    return keep


# ================== (2) ماسح السيولة - البني ستوك ==================
def check_flow(df):
    """df = شموع يومية (آخر شمعة = اليوم). يرجع التفاصيل لو الشروط كلها تحققت (ما عدا الفلوت)."""
    if len(df) < FLOW_AVG_DAYS + 2:
        return None
    today, past = df.iloc[-1], df.iloc[-(FLOW_AVG_DAYS + 1):-1]
    avg_vol = float(past["Volume"].mean())
    vol, close, high = float(today["Volume"]), float(today["Close"]), float(today["High"])
    prev_close = float(past["Close"].iloc[-1])
    top = float(past["High"].max())
    if avg_vol <= 0 or prev_close <= 0 or high <= 0:
        return None
    rvol = vol / avg_vol
    change = close / prev_close - 1
    pullback = 1 - close / high
    if not (FLOW_MIN_PRICE <= close <= FLOW_MAX_PRICE):
        return None
    if rvol < FLOW_RVOL or change < FLOW_MIN_CHANGE:
        return None
    if close <= top or pullback > FLOW_MAX_PULLBACK:
        return None
    return {"close": close, "high": high, "prev": prev_close, "top": top, "vol": vol,
            "avg_vol": avg_vol, "rvol": rvol, "change": change, "dollar": close * vol}


def _flow_message(t, r, flt):
    return (f"💰 دخول سيولة + اختراق\n"
            f"السهم: ${t}\n"
            f"السعر: {r['close']:.2f}$ ({r['change'] * 100:+.1f}% عن إغلاق أمس)\n"
            f"الحجم النسبي: {r['rvol']:.1f} ضعف متوسط {FLOW_AVG_DAYS} يوم\n"
            f"حجم اليوم: {int(r['vol']):,} سهم (≈ {r['dollar']:,.0f}$)\n"
            f"اخترق قمة {FLOW_AVG_DAYS} يوم: {r['top']:.2f}$ | قمة اليوم: {r['high']:.2f}$\n"
            f"الفلوت: {int(flt):,} سهم\n"
            f"الوقت: {pd.Timestamp.now(tz=LOCAL_TZ):%H:%M} (توقيتك)")


def scan_flow(tickers, already_sent):
    hits = 0
    day = pd.Timestamp.now(tz=NY).date()
    cands = []
    for t, df in download_batches(tickers, UNIVERSE_BATCH, period="3mo", interval="1d", prepost=False):
        try:
            if pd.Timestamp(df.index[-1]).date() != day:
                continue                          # ما فيه شمعة اليوم
            if f"{t}-{day}" in already_sent:
                continue
            r = check_flow(df)
            if r:
                cands.append((t, r))
        except Exception:
            continue
    for t, r in sorted(cands, key=lambda x: -x[1]["rvol"]):
        flt = get_algo_float(t)                   # الفلوت يتجاب للمرشحين بس (أسرع)
        if flt is None or flt <= 0 or flt >= FLOW_MAX_FLOAT:
            continue
        key = f"{t}-{day}"
        already_sent.add(key)
        _append_line(FLOW_SENT_FILE, key)
        hits += 1
        send_telegram(_flow_message(t, r, flt), kind="flow")
    free_memory()
    log(f"[{datetime.now():%H:%M}] ماسح السيولة: خلص الفحص - {len(cands)} مرشح، {hits} تنبيه جديد")


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


DAILY_PATTERNS = [
    # (مفعّل، الاسم، الكاشف، بالمقلوب؟)
    ("W", "🟢 قاع مزدوج (W)", _double_bottom, False),
]


def _pattern_enabled(code):
    return {"W": ENABLE_DOUBLE_BOTTOM}.get(code, False)


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


def _scan_patterns_frame(tickers):
    """يرجع {الاسم: [(التاريخ، السطر)]} - سطر واحد لكل سهم (آخر اختراق خلال آخر أسبوعين)."""
    found = {}
    for t, df in download_batches(tickers, 200, prepost=False, period="1y", interval="1d"):
        try:
            last = float(df["Close"].iloc[-1])
            for code, name, i, neck in check_daily_patterns(df, DAILY_LOOKBACK_DAYS):
                day = pd.Timestamp(df.index[i]).strftime("%Y-%m-%d")
                chg = (last / neck - 1) * 100
                row = (day, f"• ${t} | الاختراق: {day} | خط العنق: {neck:.2f} | "
                            f"السعر الحين: {last:.2f} ({chg:+.1f}%)")
                found.setdefault(name, {})
                if t not in found[name] or day > found[name][t][0]:
                    found[name][t] = row
        except Exception as e:
            log(f"{t}: خطأ يومي - {e}")
    return {name: list(rows.values()) for name, rows in found.items()}


def scan_daily(tickers):
    """قائمة وحدة بالأسبوع بكل الأسهم اللي سوت قاع مزدوج واخترقت خط العنق آخر أسبوعين."""
    found = _scan_patterns_frame(tickers)
    hits = 0
    label = "فريم يومي - آخر أسبوعين | أسهم ناسداك 2 مليار وفوق"
    for name, rows in found.items():
        rows.sort(reverse=True)                   # الأحدث فوق
        hits += len(rows)
        for i in range(0, len(rows), 40):         # رسالة وحدة، إلا لو الأسهم كثيرة مرة
            part = rows[i:i + 40]
            send_telegram(f"📅 القائمة الأسبوعية - {name}\n{label}\n\n"
                          + "\n".join(r[1] for r in part), kind="w")
            time.sleep(3)
    if not found:
        send_telegram(f"📅 القائمة الأسبوعية - القاع المزدوج (W)\n{label}\n\n"
                      "ما فيه ولا سهم هالأسبوعين", kind="w")
    free_memory()
    log(f"[{datetime.now():%H:%M}] نموذج W (أسبوعي): {hits} سهم")


def nasdaq_above_cap(min_cap):
    """رموز ناسداك اللي قيمتها السوقية فوق الحد (نفس مصدر الجاب)."""
    global MIN_MARKET_CAP
    old = MIN_MARKET_CAP
    MIN_MARKET_CAP = min_cap
    try:
        return set(get_nasdaq_midcap_plus())
    finally:
        MIN_MARKET_CAP = old


def nasdaq_nyse_above_cap(min_cap):
    """رموز ناسداك + نيويورك اللي قيمتها السوقية فوق الحد (نفس مصدر أسهم الجاب)."""
    global MIN_MARKET_CAP
    old = MIN_MARKET_CAP
    MIN_MARKET_CAP = min_cap
    try:
        return set(get_gap_universe())
    finally:
        MIN_MARKET_CAP = old


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
                f"السهم: ${t}\n"
                f"السعر: {price}\n"
                f"الشورت الحالي: 0\n"
                f"الشورت الشهر اللي قبله: {prior_txt}\n"
                f"تاريخ البيانات: {d}", kind="short"
            )
    free_memory()
    log(f"[{datetime.now():%H:%M}] الشورت: خلص الفحص - {hits} تنبيه جديد")


# ================== (4ب) تجزئة عكسية + شورت صفر ==================
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
    return (f"• ${t}\n"
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


def scan_rsplit_short(new, already_sent):
    """من التجزئات الجديدة: البني ستوك اللي الشورت عندها صفر."""
    cands = {t: (info, sp) for t, info, sp in new if info["last"] <= RSPLIT_MAX_PRICE}
    hits = 0
    if cands:
        with ThreadPoolExecutor(max_workers=RSPLIT_WORKERS) as pool:
            for t, short, prior, date, price in pool.map(fetch_short, list(cands)):
                if short is None or short != 0:
                    continue                      # لازم الشورت صفر بالضبط (مو ناقص بيانات)
                info, (sdate, ratio, opn) = cands[t]
                key = f"{t}-{sdate:%Y-%m-%d}"
                if key in already_sent:
                    continue
                already_sent.add(key)
                _append_line(RSPLIT_SENT_FILE, key)
                hits += 1
                d = pd.Timestamp(int(date), unit="s").strftime("%Y-%m-%d") if date else "غير معروف"
                send_telegram(
                    f"🔻 تجزئة عكسية + شورت صفر\n"
                    f"السهم: ${t}\n"
                    f"السعر: {price or info['last']:.2f}$\n"
                    f"التجزئة العكسية: {sdate:%Y-%m-%d} (كل {1 / ratio:g} أسهم = سهم)\n"
                    f"الشورت الحالي: 0\n"
                    f"تاريخ بيانات الشورت: {d}", kind="rsplit"
                )
    log(f"[{datetime.now():%H:%M}] التجزئة العكسية + شورت صفر: {hits} تنبيه جديد")


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


def rsplit_job(state, new_sent, short_sent, force=False):
    """مرة باليوم (أيام السوق، بعد 10 الصبح نيويورك):
    الجديد كل يوم + قائمة الأسبوع يوم الجمعة + قائمة الشهر أول يوم سوق بالشهر."""
    now = pd.Timestamp.now(tz=NY)
    today = now.date()
    if not force and (now.weekday() >= 5 or now.hour < RSPLIT_CHECK_AFTER_NY):
        return
    if not force and state.get("day") == str(today):
        return
    tickers = build_universe("التجزئة العكسية", 0.01, 100_000, 0, include_nyse=False)
    data = load_rsplits(tickers)
    log(f"التجزئة العكسية: {len(data)} سهم سوى تجزئة عكسية آخر سنة")

    new = scan_rsplit_new(data, new_sent)
    scan_rsplit_short(new, short_sent)

    week = f"{today.isocalendar()[0]}-W{today.isocalendar()[1]:02d}"
    if RSPLIT_WEEKLY and now.weekday() == 4 and state.get("week") != week:     # الجمعة
        items = splits_between(data, today - pd.Timedelta(days=6), today)
        if items:
            _send_rsplit_list(f"📋 قائمة الأسبوع - تجزئات عكسية آخر 7 أيام ({len(items)} سهم)", items)
        state["week"] = week

    month = f"{today:%Y-%m}"
    if RSPLIT_MONTHLY and state.get("month") != month:
        if today.day <= 4:                             # أول أيام الشهر بس (لو البوت اشتغل نص الشهر ما يرسل)
            last_day = today.replace(day=1) - pd.Timedelta(days=1)
            items = splits_between(data, last_day.replace(day=1), last_day)
            if items:
                _send_rsplit_list(f"🗓️ قائمة الشهر - تجزئات عكسية {last_day:%Y-%m} ({len(items)} سهم)",
                                  items)
        state["month"] = month

    state["day"] = str(today)
    _save_rsplit_state(state)
    free_memory()


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
    try:
        return {sym: (cap, "") for sym, cap in _price_universe(
            ALGO_PENNY_MIN_PRICE, ALGO_PENNY_MAX_PRICE, ALGO_PENNY_MAX_MARKET_CAP,
            ALGO_PENNY_MAX_SYMBOLS)}
    except Exception as e:
        log("البني ستوك: ما قدرت أجيب قائمة الأسهم -", e)
        return {}


def get_bigcaps():
    """أسهم ناسداك اللي قيمتها السوقية مليار وفوق، الأنشط تداولاً أول. يرجع {الرمز: القيمة السوقية}."""
    try:
        picks = [(vol, sym, cap) for sym, cap, vol, px in _nasdaq_rows()
                 if cap >= ALGO_BIG_MIN_MARKET_CAP and vol > 0]
        picks.sort(reverse=True)
        return {sym: cap for _, sym, cap in picks[:ALGO_BIG_MAX_SYMBOLS]}
    except Exception as e:
        log("خوارزميات الكبيرة: ما قدرت أجيب القيم السوقية من ناسداك -", e)
        return {}


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


def algo_loop(name, section, get_universe, fixed=None, exclude=None, once_hours=0):
    """يشتغل بخيط لحاله في الخلفية، عشان ما يتأخر بسبب الفحوصات الثانية الطويلة.
    get_universe يرجع {الرمز: (القيمة السوقية، ملاحظة)} - تتجدد مرة باليوم.
    exclude = دالة ترجع أسهم ما نراقبها هنا (موجودة بقسم ثاني).
    once_hours = تنبيه واحد بس لكل سهم، وبعدها يسكت عنه كذا ساعة (0 = بدون حد)."""
    det = AlgoDetector()
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
                            send_telegram(_algo_message(sym, res, cap, section, note), kind="algo")
        except Exception as e:
            log(f"{name}: خطأ -", e)
        time.sleep(ALGO_POLL_SEC)


# ---------- (6ب) الأسهم الكبيرة: صفقات متتالية بنفس الحجم ----------
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
    det = StreakDetector()
    ice = (StreakDetector(ALGO_ICE_MIN_STREAK, ALGO_ICE_MIN_SIZE, ALGO_ICE_MAX_SIZE,
                          ALGO_ICE_MAX_GAP_SEC, ALGO_ICE_REALERT_MIN, same_price=True)
           if ALGO_ICE else None)
    last_end, was_on = None, None
    caps, caps_day = {}, None
    while True:
        try:
            now = pd.Timestamp.now(tz="UTC")
            end = now - pd.Timedelta(minutes=ALGO_DELAY_MIN)
            on = trading_hours(end.tz_convert(NY))
            if on != was_on:
                log("خوارزميات الكبيرة: " + ("بدأ المراقبة" if on else "السوق مسكر، أنتظر"))
                was_on = on
            if not on:
                last_end = None
                time.sleep(60)
                continue
            today = pd.Timestamp.now(tz=NY).date()
            if caps_day != today or not caps:
                caps = ({s_: None for s_ in ALGO_BIG_SYMBOLS} if ALGO_BIG_SYMBOLS
                        else get_bigcaps())
                caps_day = today
                log(f"خوارزميات الكبيرة: يراقب {len(caps)} سهم ناسداك قيمتها "
                    f"{ALGO_BIG_MIN_MARKET_CAP / 1e9:g} مليار وفوق - تنبيه عند "
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
                        res = det.add(sym, tr)
                        if res:
                            send_telegram(_big_message(sym, res, caps.get(sym)), kind="algo_big")
                        if ice is not None:
                            res = ice.add(sym, tr)
                            if res:
                                send_telegram(_ice_message(sym, res, caps.get(sym)), kind="ice")
                del got
        except Exception as e:
            log("خوارزميات الكبيرة: خطأ -", e)
        time.sleep(ALGO_BIG_POLL_SEC)


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
    if ALGO_BIG:
        threading.Thread(target=algo_big_loop, daemon=True, name="algo_big").start()


def algo_self_test():
    det = AlgoDetector(); t0 = pd.Timestamp("2026-01-02T15:00:00Z"); alerts = []
    for k in range(650):          # 650 صفقة بحجم سهم واحد خلال 3 دقايق وشوي، السعر يطلع
        tr = {"i": k + 1, "s": 1, "p": 0.50 + (k % 5) * 0.001,
              "t": t0 + pd.Timedelta(milliseconds=k * 300)}
        a = det.add("TEST", tr)
        if a: alerts.append(a)
    for k in range(400):          # صفقات حجمها كبير = تتجاهل
        a = det.add("BIG", {"i": k + 1, "s": 500, "p": 1.0, "t": t0 + pd.Timedelta(seconds=k)})
        assert a is None
    assert [a["count"] for a in alerts] == [300, 600], [a["count"] for a in alerts]
    print("ALGO TEST OK: 300 / 600 same-size trades")
    print(_algo_message("TEST", alerts[-1], 12_300_000))

    # (6ب) الكبيرة: 1100 صفقة متتالية بحجم 100 (كل 3 ورا بعض بنفس اللحظة)، ثم صفقة بحجم ثاني تقطعها
    det = StreakDetector(); big = []
    for k in range(1100):
        tr = {"i": k + 1, "s": 1, "p": 180.00 - (k // 50) * 0.01,
              "t": (t0 + pd.Timedelta(milliseconds=(k // 3) * 40)).strftime("%Y-%m-%dT%H:%M:%S.%f000Z")}
        a = det.add("BIGCAP", tr)
        if a: big.append(a)
    assert det.add("BIGCAP", {"i": 1101, "s": 1, "p": 180, "t": "2026-01-02T15:00:00.000000000Z"}) is None  # مكرر
    det.add("BIGCAP", {"i": 9999, "s": 37, "p": 179.9, "t": "2026-01-02T15:00:10Z"})   # حجم ثاني = تنقطع
    for k in range(599):          # 599 ما توصل الحد
        a = det.add("BIGCAP", {"i": 10000 + k, "s": 1, "p": 179.9, "t": t0 + pd.Timedelta(seconds=11 + k * 0.01)})
        assert a is None
    assert [a["count"] for a in big] == [600], [a["count"] for a in big]
    for k in range(1300):         # حجم 100 (أكبر من 10) = يتجاهل
        assert det.add("BIG100", {"i": k + 1, "s": 100, "p": 50, "t": t0 + pd.Timedelta(milliseconds=k * 10)}) is None
    assert big[0]["max_same"] == 3
    print("ALGO BIG TEST OK: 600 consecutive same-size trades")

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


# ================== (7) الأخبار الإيجابية - ألباكا ==================
import re

NEWS_URL = "https://data.alpaca.markets/v1beta1/news"
SNAP_URL = "https://data.alpaca.markets/v2/stocks/snapshots"

# (الاسم، الكلمات) - أول تصنيف ينطبق على العنوان هو اللي يطلع بالتنبيه
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
    ("⬆️ ترقية محلل", r"\bupgrades?\b|\bupgraded\b|\braises?\b.*\bprice target\b|\binitiates?\b.*\b(buy|outperform|overweight)"),
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


def classify_news(headline):
    """يرجع اسم التصنيف لو الخبر إيجابي، وإلا None."""
    h = headline or ""
    if _NEWS_NEG.search(h):
        return None
    for name, rx in _NEWS_POS:
        if rx.search(h):
            return name
    return None


def _alpaca_headers():
    return {"APCA-API-KEY-ID": ALPACA_KEY, "APCA-API-SECRET-KEY": ALPACA_SECRET}


def fetch_news(start):
    """كل الأخبار من وقت start لين الحين (كل الأسهم). يرجع قائمة أو None لو فشل."""
    params = {"start": start.strftime("%Y-%m-%dT%H:%M:%SZ"), "limit": 50, "sort": "asc",
              "include_content": "false"}
    out = []
    for _ in range(10):
        _alpaca_wait()
        try:
            r = requests.get(NEWS_URL, headers=_alpaca_headers(), params=params, timeout=20)
        except Exception as e:
            log("الأخبار: فشل الاتصال -", e)
            return None
        if r.status_code == 429:
            time.sleep(10)
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
    """آخر سعر لكل سهم من ألباكا: {الرمز: السعر}."""
    if not symbols:
        return {}
    _alpaca_wait()
    try:
        r = requests.get(SNAP_URL, headers=_alpaca_headers(),
                         params={"symbols": ",".join(symbols), "feed": ALGO_FEED}, timeout=15)
        if r.status_code != 200:
            return {}
        out = {}
        for sym, snap in (r.json() or {}).items():
            snap = snap or {}
            px = ((snap.get("latestTrade") or {}).get("p")
                  or (snap.get("dailyBar") or {}).get("c"))
            if px:
                out[sym] = float(px)
        return out
    except Exception:
        return {}


_news_caps = {"day": None, "caps": {}}


def news_caps():
    """{الرمز: القيمة السوقية} للأسهم اللي قيمتها تحت NEWS_MAX_MARKET_CAP. تتجدد مرة باليوم."""
    today = pd.Timestamp.now(tz=NY).date()
    if _news_caps["day"] == today and _news_caps["caps"]:
        return _news_caps["caps"]
    caps = {}
    for ex in NEWS_EXCHANGES:
        url = ("https://api.nasdaq.com/api/screener/stocks"
               f"?tableonly=true&limit=10000&exchange={ex}&download=true")
        try:
            r = requests.get(url, headers={**HEADERS, "Accept": "application/json"}, timeout=30)
            data = r.json().get("data") or {}
            rows = data.get("rows") or (data.get("table") or {}).get("rows") or []
            for row in rows:
                sym = str(row.get("symbol", "")).strip().upper()
                cap = _to_number(row.get("marketCap"))
                if sym.isalpha() and len(sym) <= 5 and max(0, NEWS_MIN_MARKET_CAP) < cap < NEWS_MAX_MARKET_CAP:
                    caps[sym] = cap
        except Exception as e:
            log(f"الأخبار: ما قدرت أجيب القيم السوقية من {ex.upper()} -", e)
    if caps:
        _news_caps.update(day=today, caps=caps)
        log(f"الأخبار: {len(caps)} سهم قيمتها السوقية أقل من {NEWS_MAX_MARKET_CAP / 1e6:g} مليون")
    return caps


def _news_message(item, cat, syms, prices, caps=None):
    t = pd.Timestamp(item.get("created_at")).tz_convert(LOCAL_TZ)
    lines = []
    for s in syms:
        px = prices.get(s)
        lines.append(f"${s} ({px:.2f}$)" if px else f"${s}")
    return (f"📰 خبر إيجابي — {cat}\n"
            f"السهم: {' | '.join(lines)}\n"
            + (f"القيمة السوقية: {' | '.join(_cap_txt(caps[s]) for s in syms if s in caps)}\n"
               if caps and any(s in caps for s in syms) else "")
            + f"العنوان: {item.get('headline', '').strip()}\n"
            f"المصدر: {item.get('source') or item.get('author') or 'غير معروف'}\n"
            f"الوقت: {t:%H:%M} (توقيتك)\n"
            + (f"الرابط: {item['url']}" if item.get("url") else ""))


def news_loop():
    """يشتغل بخيط لحاله: يسحب الأخبار كل NEWS_POLL_SEC ثانية ويرسل الإيجابي بس."""
    sent = _load_set(NEWS_SENT_FILE)
    last = pd.Timestamp.now(tz="UTC") - pd.Timedelta(minutes=NEWS_MAX_AGE_MIN)
    log("الأخبار: بدأ المراقبة (ألباكا) - "
        + (f"أسهم سعرها {NEWS_MIN_PRICE or 0:g}$-{NEWS_MAX_PRICE:g}$" if NEWS_MAX_PRICE else "كل الأسعار")
        + (f" وقيمتها أقل من {NEWS_MAX_MARKET_CAP / 1e6:g} مليون$" if NEWS_MAX_MARKET_CAP else ""))
    while True:
        try:
            now = pd.Timestamp.now(tz="UTC")
            items = fetch_news(last - pd.Timedelta(minutes=2))   # نرجع شوي عشان الأخبار المتأخرة
            if items is not None:
                last = now
                hits = []
                for it in items:
                    key = str(it.get("id"))
                    if key in sent:
                        continue
                    created = pd.Timestamp(it.get("created_at"))
                    if (now - created).total_seconds() / 60 > NEWS_MAX_AGE_MIN:
                        continue
                    syms = [s for s in (it.get("symbols") or []) if s.isalpha() and len(s) <= 5]
                    if not syms or len(syms) > NEWS_MAX_SYMBOLS:
                        continue
                    cat = classify_news(it.get("headline"))
                    if not cat:
                        continue
                    if NEWS_MAX_MARKET_CAP:
                        caps = news_caps()
                        if not caps:
                            continue            # ما قدر يجيب القيم السوقية، ما يرسل بدون فلتر
                        syms = [x for x in syms if x in caps]
                        if not syms:
                            continue
                    sent.add(key)
                    _append_line(NEWS_SENT_FILE, key)
                    hits.append((it, cat, syms))
                prices = fetch_prices(sorted({s for _, _, ss in hits for s in ss})) if hits else {}
                for it, cat, syms in hits:
                    if NEWS_MIN_PRICE or NEWS_MAX_PRICE:
                        ok = [s for s in syms if s in prices
                              and prices[s] >= NEWS_MIN_PRICE
                              and (not NEWS_MAX_PRICE or prices[s] <= NEWS_MAX_PRICE)]
                        if not ok:
                            continue
                        syms = ok
                    send_telegram(_news_message(it, cat, syms, prices, _news_caps["caps"]), kind="news")
        except Exception as e:
            log("الأخبار: خطأ -", e)
        time.sleep(NEWS_POLL_SEC)


def start_news_thread():
    if not NEWS:
        log("الأخبار: مطفي (NEWS=0)")
        return
    if not (ALPACA_KEY and ALPACA_SECRET):
        log("الأخبار: مطفي (يحتاج ALPACAAPIKEY و ALPACASECRETKEY في Railway)")
        return
    threading.Thread(target=news_loop, daemon=True, name="news").start()


def news_self_test():
    cases = [
        ("Acme Corp To Acquire Beta Inc For $2.1B In Cash", True),
        ("XYZ Announces Definitive Merger Agreement With ABC", True),
        ("BioCo Receives FDA Approval For Lead Drug", True),
        ("BioCo Announces Positive Topline Results From Phase 3 Trial", True),
        ("TechCo Awarded $50M Contract By US Army", True),
        ("RetailCo Q3 EPS Beats Estimates, Raises FY Guidance", True),
        ("Morgan Stanley Upgrades NVDA To Overweight", True),
        ("SmallCap Announces $10M Registered Direct Offering", False),
        ("Halper Sadeh Investigating Whether Sale Of XYZ Is Fair To Shareholders", False),
        ("BioCo Receives Complete Response Letter From FDA", False),
        ("RetailCo Misses Estimates, Cuts Guidance", False),
        ("Acme Terminates Merger Agreement With Beta", False),
        ("Analyst Downgrades AAPL To Neutral", False),
        ("Stocks Moving In Thursday's Pre-Market Session", False),
    ]
    bad = [(h, want) for h, want in cases if bool(classify_news(h)) != want]
    for h, want in cases:
        print(("✅" if (h, want) not in bad else "❌"), classify_news(h) or "-", "|", h)
    assert not bad, bad
    print("NEWS TEST OK")
    print(_news_message({"headline": cases[0][0], "source": "benzinga",
                         "created_at": "2026-10-02T13:05:00Z", "url": "https://example.com"},
                        classify_news(cases[0][0]), ["ACME"], {"ACME": 4.12}, {"ACME": 62_500_000}))


# ======================================================================
# (8) صياد العقود THE LEGENDARY 🗽⚡️ (كان ملف bot 2 / legendary_options.py)
# ======================================================================
# THE LEGENDARY 🗽⚡️
# Adaptive Pre-Hunt Options Explosion Hunter V2 — No Alert Cap
#
# Design:
# - Stocks only; SPX intentionally excluded.
# - 30-stock universe.
# - The core goal is EARLY prediction of a future decision/turning zone,
#   not chasing a move after it has already started.
# - Rising into a future rejection/absorption zone -> hunt PUT early.
# - Falling into a future rejection/absorption zone -> hunt CALL early.
# - Early alert is a WATCH, not an entry confirmation.
# - 15m = structural map, 5m = approach, 1m = trigger only for near-zone candidates.
# - Fib + volume profile + prior session levels + price/volume behaviour are fused.
# - Rejection, continuation and absorption are measured as behaviour, not single candles.
# - Strike + expiry are selected together; premium < $3 is a preference, not a filter.
# - Potential/reachability are scenario estimates, not guarantees.
# - Target reachability is separate from signal/entry timing.
# - +100% potential is the minimum contract scenario; +1000%+ is exceptional 🏌🏼‍♂️.
# - Central adaptive API limiter/cache/backoff. Options are queried only for qualified candidates.
# - Lower-timeframe requests are staged; 1m is reserved for near-trigger candidates.
# - A short stale-bar fallback protects structural scanning during temporary 429s.
# - One centralized contract monitor loop avoids one thread/request stream per alert.
# - Every alert is logged; there is no alert-count cap.

# Connection settings from the supplied bot source.
# Keep these private.
# ⚠️ الأفضل تحطها كمتغيرات في Railway (POLYGON_API_KEY, LEGENDARY_TG_TOKEN, LEGENDARY_TG_CHAT)
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "SjxOZh1bBhcXuLjv6fSX2KQbhgnLWRQT").strip()
TELEGRAM_BOT_TOKEN = os.getenv("LEGENDARY_TG_TOKEN", "8517634702:AAFIQ9ntnSQQlnchs16-GSYsEnzmBvurosg").strip()
LEGENDARY_TG_CHAT_ID = os.getenv("LEGENDARY_TG_CHAT", "@marbot92").strip()

# لما يشتغل داخل السكانر، السكانر يحط هنا دالة الإرسال حقته (نفس قروبات السكانر)
# الدالة تاخذ (message, image_path). None = يرسل بتوكن وقناة البوت الأصلية فوق
EXTERNAL_SENDER = None

# Optional live options provider.
# Stock/structure data remains on Polygon. When a Tradier production token is
# configured, options discovery/monitoring can use Tradier first, with Polygon
# retained as a fallback. No hunt/scoring/alert logic is changed.
TRADIER_API_TOKEN = os.getenv("TRADIER_API_TOKEN", "").strip()
TRADIER_BASE_URL = os.getenv("TRADIER_BASE_URL", "https://api.tradier.com/v1").rstrip("/")
TRADIER_MIN_INTERVAL = float(os.getenv("TRADIER_MIN_INTERVAL", "0.20"))
TRADIER_EXPIRATIONS_CACHE_SECONDS = int(os.getenv("TRADIER_EXPIRATIONS_CACHE_SECONDS", "300"))
TRADIER_CHAIN_CACHE_SECONDS = int(os.getenv("TRADIER_CHAIN_CACHE_SECONDS", "20"))
TRADIER_MAX_EXPIRIES = int(os.getenv("TRADIER_MAX_EXPIRIES", "4"))
TRADIER_MAX_DTE = int(os.getenv("TRADIER_MAX_DTE", "45"))


TARGET_ASSETS = [
    "AXON","COIN","T","CRWD","SWKS","MU","HOOD","TSLA","META","AAPL",
    "SPCX","HPE","VST","MET","INTC","AMD","AVGO","PLTR","NFLX","ORCL"
]
# تقدر تغير القائمة من Railway بمتغير LEGENDARY_SYMBOLS (بينها فاصلة)
_env_syms = [x.strip().upper() for x in os.getenv("LEGENDARY_SYMBOLS", "").split(",") if x.strip()]
if _env_syms:
    TARGET_ASSETS = _env_syms

# API/load controls.
REQUEST_MIN_INTERVAL = float(os.getenv("REQUEST_MIN_INTERVAL", "0.35"))
MAX_BACKOFF_SECONDS = int(os.getenv("MAX_BACKOFF_SECONDS", "60"))
SCAN_INTERVAL_SECONDS = int(os.getenv("SCAN_INTERVAL_SECONDS", "75"))
MONITOR_INTERVAL_SECONDS = int(os.getenv("MONITOR_INTERVAL_SECONDS", "90"))
OPTIONS_CACHE_SECONDS = int(os.getenv("OPTIONS_CACHE_SECONDS", "25"))
MAX_ACTIVE_MONITORS = int(os.getenv("MAX_ACTIVE_MONITORS", "8"))

# Smart search scheduling. This changes request timing/order only; it does not
# change hunt, scoring, direction, contract, or alert thresholds.
MAX_STRUCTURAL_SCANS_PER_CYCLE = int(os.getenv("MAX_STRUCTURAL_SCANS_PER_CYCLE", "2"))
NORMAL_SCAN_COOLDOWN_SECONDS = int(os.getenv("NORMAL_SCAN_COOLDOWN_SECONDS", "600"))
ACTIVE_SCAN_COOLDOWN_SECONDS = int(os.getenv("ACTIVE_SCAN_COOLDOWN_SECONDS", "150"))
HOT_SCAN_COOLDOWN_SECONDS = int(os.getenv("HOT_SCAN_COOLDOWN_SECONDS", "75"))


# Adaptive API traffic controls. These change request scheduling only;
# hunt/scoring thresholds remain unchanged.
ADAPTIVE_MIN_INTERVAL = max(REQUEST_MIN_INTERVAL, float(os.getenv("ADAPTIVE_MIN_INTERVAL", "0.35")))
ADAPTIVE_MAX_INTERVAL = float(os.getenv("ADAPTIVE_MAX_INTERVAL", "1.50"))
ADAPTIVE_RECOVERY_STEP = float(os.getenv("ADAPTIVE_RECOVERY_STEP", "0.05"))
RATE_LIMIT_BACKOFF_BASE = int(os.getenv("RATE_LIMIT_BACKOFF_BASE", "5"))
STALE_BAR_FALLBACK_SECONDS = int(os.getenv("STALE_BAR_FALLBACK_SECONDS", "120"))

# Scoring.
MIN_POTENTIAL_RETURN = 100.0
EXCEPTIONAL_RETURN = 1000.0
PREFERRED_MAX_CONTRACT_PRICE = 3.00

# Early-zone controls.
EARLY_ZONE_MIN_SCORE = 64.0
EARLY_ZONE_NEAR_SCORE = 72.0
ZONE_LOOKAHEAD_BARS = 20          # 5 hours on 15m map
ZONE_MIN_DISTANCE_ATR = 0.35
ZONE_MAX_DISTANCE_ATR = 5.0
APPROACH_DISTANCE_ATR = 1.35
TRIGGER_DISTANCE_ATR = 0.55

# Memory/cache.
_cache = {}
_cache_lock = threading.Lock()
_request_lock = threading.Lock()
_last_request_time = 0.0
_backoff_until = 0.0
_adaptive_interval = ADAPTIVE_MIN_INTERVAL
_last_429_time = 0.0
_stale_cache = {}

# Polygon HTTP transport controls (used only by api_get).
POLYGON_CONNECT_TIMEOUT = float(os.getenv("POLYGON_CONNECT_TIMEOUT", "10"))
POLYGON_READ_TIMEOUT = float(os.getenv("POLYGON_READ_TIMEOUT", "30"))
POLYGON_MAX_ATTEMPTS = 3
_TRANSIENT_HTTP_STATUSES = (500, 502, 503, 504)
_session = None
_options_forbidden_until = 0.0
_forbidden_logged = set()

_tradier_request_lock = threading.Lock()
_tradier_last_request_time = 0.0
_tradier_disabled_until = 0.0
_tradier_auth_logged = False


# Per-ticker state. This is deliberately small: it is behaviour memory,
# not a second indicator engine.
behavior_memory: Dict[str, Dict] = {}
active_monitors: Dict[str, Dict] = {}
alerted = {}

# Search scheduler state: keeps the full universe but avoids hammering every
# ticker with deep requests on every cycle.
search_state: Dict[str, Dict] = {}

LOG_PATH = Path(os.getenv("LEGENDARY_LOG_PATH", "legendary_alerts.csv"))
LOG_FIELDS = [
    "timestamp","stock","mode","direction","trigger",
    "stock_price","zone_low","zone_high","zone_distance_pct",
    "zone_score","rejection_score","absorption_score",
    "continuation_score","exhaustion_score","effort_result",
    "trend_score","fib_confluence","profile_confluence",
    "expected_move_pct","eta_minutes","time_fit",
    "strike","expiry","dte","contract_price",
    "potential_pct","estimated_target_price","reachability","score",
    "volume","open_interest","volume_oi","spread_pct",
    "exceptional","contract_ticker","timing_class","move_consumed_pct"
]


def cache_get(key, ttl):
    now = time.time()
    with _cache_lock:
        item = _cache.get(key)
        if item and now - item[0] <= ttl:
            return item[1]
    return None


def cache_set(key, value):
    with _cache_lock:
        _cache[key] = (time.time(), value)


# --- api_get notes ---------------------------------------------------------
# * Retries (up to POLYGON_MAX_ATTEMPTS, exponential backoff + jitter) happen
#   only for transient network errors: SSLError, ConnectionError, Timeout and
#   HTTP 500/502/503/504. 400/401/403/404 are never retried.
# * HTTP 403 means the Polygon plan is not entitled to that data. For the
#   options snapshot endpoint this triggers a 1-hour options cool-down so the
#   request budget is not wasted; bar requests are unaffected.
# * HTTP 429 keeps the adaptive spacing/backoff behaviour and is not retried.
def _get_session():
    """Shared session; Connection: close avoids reusing stale keep-alive sockets."""
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update({"Connection": "close"})
    return _session


def _reset_session():
    global _session
    old, _session = _session, None
    if old is not None:
        try:
            old.close()
        except Exception:
            pass


def _safe_url(url):
    """Host + path only; never includes the query string (API key)."""
    base = str(url).split("?", 1)[0]
    return base.split("://", 1)[-1]


def api_get(url, cache_key=None, cache_ttl=0, allow_stale_on_429=False):
    """Single controlled gateway for Polygon requests.

    Adaptive behavior: normal traffic stays fast; repeated 429 responses
    increase spacing and backoff temporarily, then recover gradually.
    The market-hunt logic and its thresholds are not changed here.
    """
    global _last_request_time, _backoff_until, _adaptive_interval, _last_429_time
    global _options_forbidden_until

    if cache_key and cache_ttl:
        cached = cache_get(cache_key, cache_ttl)
        if cached is not None:
            return cached

    is_options = "/v3/snapshot/options/" in str(url)
    if is_options and time.time() < _options_forbidden_until:
        return None

    safe = _safe_url(url)
    failure = None

    for attempt in range(POLYGON_MAX_ATTEMPTS):
        with _request_lock:
            now = time.time()
            if now < _backoff_until:
                # Do not freeze the whole scanner after a 429; keep the pause short
                # and let stale caches + smart rotation protect the request budget.
                time.sleep(min(2.0, _backoff_until - now))

            wait = _adaptive_interval - (time.time() - _last_request_time)
            if wait > 0:
                time.sleep(wait)

            try:
                res = _get_session().get(
                    url, timeout=(POLYGON_CONNECT_TIMEOUT, POLYGON_READ_TIMEOUT)
                )
                _last_request_time = time.time()
            except (requests.exceptions.SSLError, requests.exceptions.ConnectionError) as exc:
                _last_request_time = time.time()
                _reset_session()
                failure = type(exc).__name__
                res = None
            except requests.exceptions.Timeout as exc:
                _last_request_time = time.time()
                failure = type(exc).__name__
                res = None
            except requests.RequestException as exc:
                _last_request_time = time.time()
                logging.warning("API request failed for %s: %s", safe, type(exc).__name__)
                return None

            if res is not None:
                if res.status_code == 429:
                    now = time.time()
                    # Exponentially increase the spacing, but cap it so recovery
                    # remains quick after the API cools down.
                    _adaptive_interval = min(
                        ADAPTIVE_MAX_INTERVAL,
                        max(ADAPTIVE_MIN_INTERVAL, _adaptive_interval * 1.5)
                    )

                    retry_after = res.headers.get("Retry-After")
                    try:
                        server_delay = float(retry_after) if retry_after else 0.0
                    except (TypeError, ValueError):
                        server_delay = 0.0

                    previous = max(0, int(_backoff_until - now))
                    delay = max(2, server_delay, min(previous * 2, RATE_LIMIT_BACKOFF_BASE))
                    delay = min(15, MAX_BACKOFF_SECONDS, delay)
                    _backoff_until = now + delay
                    _last_429_time = now
                    logging.warning(
                        "429 rate limit. Adaptive interval=%.2fs; pausing Polygon traffic for %ss.",
                        _adaptive_interval, int(delay)
                    )

                    # Bars can safely use a very short stale fallback during a rate
                    # limit event, preventing one 429 from erasing a qualified
                    # structural candidate. Options are deliberately not given this
                    # fallback because contract quotes are more sensitive to staleness.
                    if allow_stale_on_429 and cache_key:
                        stale = _stale_cache.get(cache_key)
                        if stale and now - stale[0] <= STALE_BAR_FALLBACK_SECONDS:
                            return stale[1]
                    return None

                if res.status_code == 403:
                    family = "options_snapshot" if is_options else "other:" + safe.split("/", 2)[-1].split("/")[0]
                    if family not in _forbidden_logged:
                        _forbidden_logged.add(family)
                        if is_options:
                            logging.warning(
                                "Polygon returned 403 (not entitled) for the options snapshot "
                                "(%s). Check that the Polygon plan includes options data; "
                                "pausing options requests for 1 hour.", safe
                            )
                        else:
                            logging.warning("Polygon returned 403 (not entitled) for %s", safe)
                    if is_options:
                        _options_forbidden_until = time.time() + 3600
                    return None

                if res.status_code in _TRANSIENT_HTTP_STATUSES:
                    failure = "HTTP %s" % res.status_code
                elif res.status_code != 200:
                    logging.warning("API status %s for %s", res.status_code, safe)
                    return None
                else:
                    # Gradually recover toward the normal request interval after clean
                    # responses; never jump instantly back to the minimum.
                    if _adaptive_interval > ADAPTIVE_MIN_INTERVAL:
                        _adaptive_interval = max(
                            ADAPTIVE_MIN_INTERVAL,
                            _adaptive_interval - ADAPTIVE_RECOVERY_STEP
                        )

                    if cache_key and cache_ttl:
                        cache_set(cache_key, res)
                        _stale_cache[cache_key] = (time.time(), res)
                    return res

        # Transient failure: back off outside the request lock.
        if attempt < POLYGON_MAX_ATTEMPTS - 1:
            time.sleep(1.5 * 2 ** attempt + random.uniform(0, 1))

    logging.warning("API request failed after %d attempts for %s: %s",
                    POLYGON_MAX_ATTEMPTS, safe, failure)
    return None



def is_us_market_open():
    et = datetime.now(ZoneInfo("America/New_York"))
    if et.weekday() >= 5:
        return False
    open_time = et.replace(hour=9, minute=30, second=0, microsecond=0)
    close_time = et.replace(hour=16, minute=0, second=0, microsecond=0)
    return open_time <= et <= close_time


def get_market_phase():
    et = datetime.now(ZoneInfo("America/New_York"))
    open_dt = et.replace(hour=9, minute=30, second=0, microsecond=0)
    diff = (et - open_dt).total_seconds() / 60
    if diff < 60:
        return "OPENING"
    if diff > 330:
        return "POWER_HOUR"
    return "MIDDAY"


def send_telegram_alert(message, image_path=None):
    if EXTERNAL_SENDER is not None:
        try:
            EXTERNAL_SENDER(message, image_path)
        except Exception:
            logging.exception("External sender failed")
        return
    if not TELEGRAM_BOT_TOKEN or not LEGENDARY_TG_CHAT_ID:
        logging.warning("Telegram credentials are not configured.")
        return

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, data={
            "chat_id": LEGENDARY_TG_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }, timeout=15)

        if image_path and os.path.exists(image_path):
            photo_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
            with open(image_path, "rb") as photo:
                requests.post(photo_url,
                              data={"chat_id": LEGENDARY_TG_CHAT_ID},
                              files={"photo": photo},
                              timeout=15)
    except requests.RequestException as exc:
        logging.error("Telegram error: %s", exc)


def generate_card_image(ticker, option_type, strike, expiry_date,
                        output_path="signal_card.png", mode="PRE-HUNT"):
    if Image is None:          # pillow مو منزّل: التنبيه يروح بدون صورة
        return None
    width, height = 900, 340
    bg = (13, 27, 42)
    border = (212, 175, 55)
    text = (245, 245, 245)
    gold = (225, 198, 115)

    img = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(img)
    margin = 15
    draw.rounded_rectangle([margin, margin, width-margin, height-margin],
                           radius=25, outline=border, width=3)
    draw.line([(330,40),(330,height-40)], fill=(50,70,95), width=2)
    draw.line([(630,40),(630,height-40)], fill=(50,70,95), width=2)

    try:
        f_large = ImageFont.truetype("arial.ttf", 64)
        f_med = ImageFont.truetype("arial.ttf", 46)
        f_small = ImageFont.truetype("arial.ttf", 28)
    except Exception:
        f_large = f_med = f_small = ImageFont.load_default()

    draw.text((50,110), ticker, fill=gold, font=f_large)
    is_call = option_type.upper() == "CALL"
    dot = (34,139,34) if is_call else (178,34,34)
    badge = (20,80,40) if is_call else (140,30,30)
    draw.ellipse([215,135,255,175], fill=dot)
    draw.rounded_rectangle([370,55,565,115], radius=10, fill=badge)
    arrow = "↑" if is_call else "↓"
    draw.text((395,63), f"{arrow} {option_type.upper()}",
              fill=(255,255,255), font=f_small)
    draw.text((385,135), f"{float(strike):g}", fill=gold, font=f_med)
    draw.text((650,55), mode, fill=text, font=f_small)
    draw.text((650,145), str(expiry_date), fill=text, font=f_small)
    img.save(output_path)
    return output_path


def _bar_time(bar):
    ts = bar.get("t")
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(float(ts) / 1000, tz=timezone.utc)
    except Exception:
        return None


def _safe_float(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _clamp(v, lo=0.0, hi=100.0):
    return max(lo, min(hi, float(v)))


def _mean(values):
    vals = [x for x in values if x is not None and math.isfinite(x)]
    return sum(vals) / len(vals) if vals else 0.0


def _median(values):
    vals = sorted(x for x in values if x is not None and math.isfinite(x))
    if not vals:
        return 0.0
    n = len(vals)
    return vals[n // 2] if n % 2 else (vals[n//2-1] + vals[n//2]) / 2


def _pct(a, b):
    if not b:
        return 0.0
    return (a / b - 1.0) * 100.0


def fetch_bars(ticker):
    """
    Daily + 15m map. Five days of 15m bars lets the engine remember
    prior session structure without adding a second intraday request.
    """
    today = datetime.now(ZoneInfo("America/New_York")).date()
    daily_start = (today - timedelta(days=90)).isoformat()
    intraday_start = (today - timedelta(days=7)).isoformat()
    today_s = today.isoformat()

    daily_url = (
        f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/"
        f"{daily_start}/{today_s}?apiKey={POLYGON_API_KEY}"
    )
    m15_url = (
        f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/15/minute/"
        f"{intraday_start}/{today_s}?apiKey={POLYGON_API_KEY}"
    )

    rd = api_get(daily_url, f"daily:{ticker}", 600, allow_stale_on_429=True)
    rm = api_get(m15_url, f"m15:{ticker}", 50, allow_stale_on_429=True)

    daily = rd.json().get("results", []) if rd else []
    m15 = rm.json().get("results", []) if rm else []
    return daily, m15


def fetch_lower_timeframes(ticker, include_m1=False):
    """Fetch 5m for approach; fetch 1m only when the candidate is near trigger.

    This is an API-efficiency layer only. It does not change the 15m/5m/1m
    decision rules; it simply avoids paying for 1m data before it is needed.
    """
    today = datetime.now(ZoneInfo("America/New_York")).date()
    start = (today - timedelta(days=2)).isoformat()
    end = today.isoformat()

    m5_url = (
        f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/5/minute/"
        f"{start}/{end}?apiKey={POLYGON_API_KEY}"
    )
    r5 = api_get(m5_url, f"m5:{ticker}", 35, allow_stale_on_429=True)
    m5 = r5.json().get("results", []) if r5 else []

    m1 = []
    if include_m1:
        m1_url = (
            f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/minute/"
            f"{start}/{end}?apiKey={POLYGON_API_KEY}"
        )
        r1 = api_get(m1_url, f"m1:{ticker}", 25, allow_stale_on_429=True)
        m1 = r1.json().get("results", []) if r1 else []

    return m5, m1


def _session_levels(m15):
    """Prior RTH / premarket / current RTH levels from available bars."""
    sessions = {}
    for b in m15:
        dt = _bar_time(b)
        if not dt:
            continue
        et = dt.astimezone(ZoneInfo("America/New_York"))
        d = et.date()
        hm = et.hour * 60 + et.minute

        if 4 * 60 <= hm < 9 * 60 + 30:
            key = (d, "PRE")
        elif 9 * 60 + 30 <= hm <= 16 * 60:
            key = (d, "RTH")
        else:
            continue

        bucket = sessions.setdefault(key, {"high": -float("inf"), "low": float("inf")})
        bucket["high"] = max(bucket["high"], _safe_float(b.get("h")))
        bucket["low"] = min(bucket["low"], _safe_float(b.get("l")))

    out = []
    for (d, name), v in sorted(sessions.items()):
        if math.isfinite(v["high"]) and math.isfinite(v["low"]):
            out.append({"date": d, "name": name,
                        "high": v["high"], "low": v["low"]})
    return out


def _volume_profile(m15, bins=28):
    """
    Approximate volume profile from bar typical prices.
    It is deliberately a local structural estimate, not tick-level order flow.
    """
    bars = m15[-160:] if len(m15) > 160 else m15
    if len(bars) < 20:
        return {}

    lo = min(_safe_float(b.get("l")) for b in bars)
    hi = max(_safe_float(b.get("h")) for b in bars)
    if hi <= lo:
        return {}

    step = (hi - lo) / bins
    weights = [0.0] * bins

    for b in bars:
        tp = (_safe_float(b.get("h")) + _safe_float(b.get("l")) +
              _safe_float(b.get("c"))) / 3
        vol = max(0.0, _safe_float(b.get("v")))
        idx = int((tp - lo) / step)
        idx = min(bins - 1, max(0, idx))
        weights[idx] += vol

    total = sum(weights)
    if total <= 0:
        return {}

    poc_idx = max(range(bins), key=lambda i: weights[i])
    target = total * 0.70
    selected = {poc_idx}
    acc = weights[poc_idx]
    left = poc_idx - 1
    right = poc_idx + 1

    while acc < target and (left >= 0 or right < bins):
        lv = weights[left] if left >= 0 else -1
        rv = weights[right] if right < bins else -1
        if rv >= lv:
            if right < bins:
                selected.add(right)
                acc += weights[right]
                right += 1
            else:
                left -= 1
        else:
            if left >= 0:
                selected.add(left)
                acc += weights[left]
                left -= 1

    vah = lo + (max(selected) + 1) * step
    val = lo + min(selected) * step
    poc = lo + (poc_idx + 0.5) * step

    return {"poc": poc, "vah": vah, "val": val, "step": step}


def _fib_levels(m15):
    """
    Dynamic swing Fibonacci map. Recent structure is preferred; levels are
    treated as zones/confluence, never as automatic buy/sell signals.
    """
    bars = m15[-96:] if len(m15) > 96 else m15
    if len(bars) < 20:
        return {}

    highs = [_safe_float(b.get("h")) for b in bars]
    lows = [_safe_float(b.get("l")) for b in bars]
    hi = max(highs)
    lo = min(lows)
    rng = hi - lo
    if rng <= 0:
        return {}

    ratios = [0.382, 0.5, 0.618, 0.707, 0.786, 1.0, 1.13, 1.272, 1.618]
    return {r: lo + rng * r for r in ratios}


def _atr_pct(m15, n=20):
    bars = m15[-n:] if len(m15) >= n else m15
    if not bars:
        return 0.0
    ranges = [abs(_safe_float(b.get("h")) - _safe_float(b.get("l"))) for b in bars]
    closes = [_safe_float(b.get("c")) for b in bars]
    atr = _mean(ranges)
    price = closes[-1] if closes else 0
    return (atr / price * 100) if price else 0.0


def _atr_price(m15, n=20):
    bars = m15[-n:] if len(m15) >= n else m15
    return _mean([abs(_safe_float(b.get("h")) - _safe_float(b.get("l")))
                  for b in bars])


def _trend_state(m15):
    if len(m15) < 12:
        return {"direction": "FLAT", "score": 0.0}

    closes = [_safe_float(x.get("c")) for x in m15]
    recent = closes[-8:]
    older = closes[-20:-8] if len(closes) >= 20 else closes[:-8]
    recent_slope = _pct(recent[-1], recent[0]) if len(recent) > 1 else 0
    older_slope = _pct(older[-1], older[0]) if len(older) > 1 else 0

    up_steps = sum(1 for a, b in zip(recent, recent[1:]) if b > a)
    down_steps = sum(1 for a, b in zip(recent, recent[1:]) if b < a)

    score_up = max(0, recent_slope) + max(0, recent_slope - older_slope) * 0.5
    score_dn = max(0, -recent_slope) + max(0, -recent_slope + older_slope) * 0.5

    if up_steps >= 5 and score_up > 0.15:
        return {"direction": "UP", "score": _clamp(50 + score_up * 20)}
    if down_steps >= 5 and score_dn > 0.15:
        return {"direction": "DOWN", "score": _clamp(50 + score_dn * 20)}
    return {"direction": "FLAT", "score": 25.0}


def _effort_result(m15):
    """
    Measures effort vs result:
    high volume + weak price progress => absorption-like behaviour;
    high volume + strong progress => continuation fuel.
    """
    if len(m15) < 12:
        return {"absorption": 0, "continuation": 0, "ratio": 0}

    bars = m15[-12:]
    vols = [_safe_float(b.get("v")) for b in bars[:-1]]
    avg_vol = _mean(vols)
    avg_range = _mean([abs(_safe_float(b.get("h")) - _safe_float(b.get("l")))
                       for b in bars[:-1]])
    cur = bars[-1]
    vol_ratio = _safe_float(cur.get("v")) / avg_vol if avg_vol else 0
    cur_range = abs(_safe_float(cur.get("h")) - _safe_float(cur.get("l")))
    close = _safe_float(cur.get("c"))
    body = abs(close - _safe_float(cur.get("o")))
    progress = body / avg_range if avg_range else 0

    absorption = 0.0
    continuation = 0.0
    if vol_ratio >= 1.4 and progress <= 0.65:
        absorption = _clamp((vol_ratio - 1.0) * 35 + (0.65 - progress) * 55)
    if vol_ratio >= 1.25 and progress >= 0.75:
        continuation = _clamp((vol_ratio - 1.0) * 30 + progress * 45)

    return {"absorption": absorption,
            "continuation": continuation,
            "ratio": vol_ratio,
            "progress": progress}


def _level_interaction(m15, level, direction, atr):
    """
    Historical evidence that the level previously rejected/absorbed price.
    The current approach is not counted as historical proof.
    """
    if level <= 0 or atr <= 0:
        return {"rejection": 0.0, "absorption": 0.0, "touches": 0}

    bars = m15[-80:-3] if len(m15) > 10 else m15[:-2]
    tol = max(atr * 0.45, level * 0.0015)
    rejection = 0.0
    absorption = 0.0
    touches = 0

    ranges = [abs(_safe_float(b.get("h")) - _safe_float(b.get("l"))) for b in bars]
    volumes = [_safe_float(b.get("v")) for b in bars]
    avg_range = _mean(ranges)
    avg_vol = _mean(volumes)

    for b in bars:
        h = _safe_float(b.get("h"))
        l = _safe_float(b.get("l"))
        o = _safe_float(b.get("o"))
        c = _safe_float(b.get("c"))
        v = _safe_float(b.get("v"))
        rng = max(h - l, 1e-9)

        near = min(abs(h - level), abs(l - level), abs(c - level)) <= tol
        if not near:
            continue

        touches += 1
        vol_ratio = v / avg_vol if avg_vol else 1
        close_location = (c - l) / rng

        if direction == "PUT":
            # Future upper zone: upper wick / failure back below level.
            wick = h - max(o, c)
            if h >= level - tol and c < level:
                rejection += 8 + min(10, vol_ratio * 3) + min(8, wick / rng * 8)
            if vol_ratio >= 1.35 and abs(c - o) / rng <= 0.45:
                absorption += 7
        else:
            # Future lower zone: lower wick / failure below level.
            wick = min(o, c) - l
            if l <= level + tol and c > level:
                rejection += 8 + min(10, vol_ratio * 3) + min(8, wick / rng * 8)
            if vol_ratio >= 1.35 and abs(c - o) / rng <= 0.45:
                absorption += 7

    return {"rejection": _clamp(rejection),
            "absorption": _clamp(absorption),
            "touches": touches}


def _fib_confluence(price, level, fibs, atr):
    if not fibs or atr <= 0:
        return 0.0
    near = [abs(v - level) / atr for v in fibs.values()]
    best = min(near) if near else 99
    return 30.0 if best <= 0.25 else 22.0 if best <= 0.5 else 12.0 if best <= 0.9 else 0.0


def _profile_confluence(level, profile, atr):
    if not profile or atr <= 0:
        return 0.0
    vals = [profile.get("poc"), profile.get("vah"), profile.get("val")]
    d = min(abs(level - x) for x in vals if x)
    return 25.0 if d <= 0.30 * atr else 17.0 if d <= 0.60 * atr else 8.0 if d <= atr else 0.0


def _future_levels(stock_price, direction, m15):
    """
    Creates future candidate zones from multiple independent structures.
    The zone is ahead of price, not at current price.
    """
    atr = _atr_price(m15)
    fibs = _fib_levels(m15)
    profile = _volume_profile(m15)
    sessions = _session_levels(m15)

    levels = []

    def add(level, label, base=0):
        if level > 0:
            levels.append({"level": float(level), "label": label, "base": base})

    if direction == "PUT":
        for r, v in fibs.items():
            if v > stock_price + ZONE_MIN_DISTANCE_ATR * atr:
                add(v, f"FIB_{r:g}", 18)
        if profile:
            for k in ("vah", "poc"):
                v = profile.get(k)
                if v and v > stock_price + ZONE_MIN_DISTANCE_ATR * atr:
                    add(v, k.upper(), 22)
        for s in sessions:
            if s["high"] > stock_price + ZONE_MIN_DISTANCE_ATR * atr:
                add(s["high"], f"{s['name']}_HIGH", 24)

        recent_high = max(_safe_float(x.get("h")) for x in m15[-48:])
        if recent_high > stock_price + ZONE_MIN_DISTANCE_ATR * atr:
            add(recent_high, "RECENT_HIGH", 22)

    else:
        for r, v in fibs.items():
            if v < stock_price - ZONE_MIN_DISTANCE_ATR * atr:
                add(v, f"FIB_{r:g}", 18)
        if profile:
            for k in ("val", "poc"):
                v = profile.get(k)
                if v and v < stock_price - ZONE_MIN_DISTANCE_ATR * atr:
                    add(v, k.upper(), 22)
        for s in sessions:
            if s["low"] < stock_price - ZONE_MIN_DISTANCE_ATR * atr:
                add(s["low"], f"{s['name']}_LOW", 24)

        recent_low = min(_safe_float(x.get("l")) for x in m15[-48:])
        if recent_low < stock_price - ZONE_MIN_DISTANCE_ATR * atr:
            add(recent_low, "RECENT_LOW", 22)

    # Cluster nearby levels into zones.
    levels.sort(key=lambda x: x["level"])
    clusters = []
    for item in levels:
        if not clusters:
            clusters.append([item])
            continue
        center = _mean([x["level"] for x in clusters[-1]])
        if abs(item["level"] - center) <= max(0.55 * atr, stock_price * 0.0015):
            clusters[-1].append(item)
        else:
            clusters.append([item])

    zones = []
    for cluster in clusters:
        vals = [x["level"] for x in cluster]
        center = _mean(vals)
        labels = list(dict.fromkeys(x["label"] for x in cluster))
        base = min(35, sum(x["base"] for x in cluster))
        zones.append({
            "low": min(vals) - 0.18 * atr,
            "high": max(vals) + 0.18 * atr,
            "center": center,
            "labels": labels,
            "base": base
        })

    return zones, fibs, profile


def _zone_analysis(stock_price, direction, zone, daily, m15):
    atr = _atr_price(m15)
    if atr <= 0:
        return None

    distance = abs(zone["center"] - stock_price)
    distance_atr = distance / atr

    if distance_atr < ZONE_MIN_DISTANCE_ATR or distance_atr > ZONE_MAX_DISTANCE_ATR:
        return None

    fibs = _fib_levels(m15)
    profile = _volume_profile(m15)
    interaction = _level_interaction(m15, zone["center"], direction, atr)

    fib_score = _fib_confluence(stock_price, zone["center"], fibs, atr)
    profile_score = _profile_confluence(zone["center"], profile, atr)

    trend = _trend_state(m15)
    effort = _effort_result(m15)

    # For a contrarian hunt, the current trend should point INTO the future zone.
    trend_aligned = (direction == "PUT" and trend["direction"] == "UP") or \
                    (direction == "CALL" and trend["direction"] == "DOWN")
    trend_score = trend["score"] if trend_aligned else 0.0

    # Historical rejection/absorption are stronger than a bare level.
    rejection = interaction["rejection"]
    absorption = interaction["absorption"]

    # Exhaustion rises when current trend is strong but effort/result degrades.
    exhaustion = 0.0
    if trend_aligned:
        exhaustion += min(35, trend["score"] * 0.35)
        exhaustion += min(35, effort["absorption"] * 0.65)
        exhaustion += min(30, max(0, 55 - effort["continuation"]))

    # Distance: early enough to act, but not so early that the zone is meaningless.
    if distance_atr <= 0.75:
        distance_score = 10
    elif distance_atr <= 1.5:
        distance_score = 18
    elif distance_atr <= 2.5:
        distance_score = 15
    elif distance_atr <= 3.5:
        distance_score = 10
    else:
        distance_score = 5

    confluence = min(30, zone["base"] + fib_score * 0.45 + profile_score * 0.45)
    score = (
        confluence +
        rejection * 0.95 +
        absorption * 0.75 +
        exhaustion * 0.55 +
        trend_score * 0.22 +
        distance_score
    )
    score = _clamp(score, 0, 100)

    # Estimate expected move using recent ATR, daily ATR and structure distance.
    daily_ranges = [
        abs(_safe_float(x.get("h")) - _safe_float(x.get("l")))
        for x in daily[-14:]
    ]
    daily_atr = _mean(daily_ranges)
    expected_4h = max(atr * math.sqrt(16), daily_atr * 0.65 if daily_atr else 0)
    expected_move_pct = (expected_4h / stock_price * 100) if stock_price else 0

    bar_move = _median([
        abs(_safe_float(b.get("c")) - _safe_float(b.get("o")))
        for b in m15[-20:]
    ])
    bar_move = max(bar_move, atr * 0.25, stock_price * 0.0003)
    eta_bars = distance / bar_move
    eta_minutes = eta_bars * 15
    time_fit = _clamp(100 - max(0, eta_minutes - 240) / 3.0)

    return {
        "direction": direction,
        "zone_low": round(zone["low"], 2),
        "zone_high": round(zone["high"], 2),
        "zone_center": round(zone["center"], 2),
        "distance_atr": distance_atr,
        "distance_pct": distance / stock_price * 100,
        "zone_score": score,
        "rejection_score": rejection,
        "absorption_score": absorption,
        "continuation_score": effort["continuation"],
        "exhaustion_score": exhaustion,
        "effort_result": effort["ratio"],
        "trend_score": trend_score,
        "fib_confluence": fib_score,
        "profile_confluence": profile_score,
        "labels": zone["labels"],
        "expected_move_pct": expected_move_pct,
        "eta_minutes": eta_minutes,
        "time_fit": time_fit,
        "atr": atr
    }


def _approach_behavior(m5, m1, direction, zone_center):
    """
    Lower-timeframe confirmation:
    5m reads approach quality; 1m is only used near the zone.
    """
    if not m5:
        return {"approach": 0, "trigger": False, "rejection": 0, "absorption": 0}

    bars = m5[-12:]
    closes = [_safe_float(x.get("c")) for x in bars]
    volumes = [_safe_float(x.get("v")) for x in bars[:-1]]
    avg_vol = _mean(volumes)
    last = bars[-1]
    vol_ratio = _safe_float(last.get("v")) / avg_vol if avg_vol else 1

    if direction == "PUT":
        approaching = closes[-1] <= zone_center
        near = abs(closes[-1] - zone_center)
        body = abs(_safe_float(last.get("c")) - _safe_float(last.get("o")))
        rng = max(_safe_float(last.get("h")) - _safe_float(last.get("l")), 1e-9)
        wick = _safe_float(last.get("h")) - max(_safe_float(last.get("o")), _safe_float(last.get("c")))
        rejection = 0
        if approaching and wick / rng > 0.30 and _safe_float(last.get("c")) < zone_center:
            rejection = _clamp(25 + vol_ratio * 12)
    else:
        approaching = closes[-1] >= zone_center
        near = abs(closes[-1] - zone_center)
        body = abs(_safe_float(last.get("c")) - _safe_float(last.get("o")))
        rng = max(_safe_float(last.get("h")) - _safe_float(last.get("l")), 1e-9)
        wick = min(_safe_float(last.get("o")), _safe_float(last.get("c"))) - _safe_float(last.get("l"))
        rejection = 0
        if approaching and wick / rng > 0.30 and _safe_float(last.get("c")) > zone_center:
            rejection = _clamp(25 + vol_ratio * 12)

    approach = 35.0 if approaching else 15.0
    if vol_ratio >= 1.25:
        approach += 20
    if body / rng <= 0.5:
        approach += 15

    trigger = False
    one_min_rejection = 0
    one_min_absorption = 0
    if m1:
        recent = m1[-6:]
        if direction == "PUT":
            highs = [_safe_float(x.get("h")) for x in recent]
            closes1 = [_safe_float(x.get("c")) for x in recent]
            near1 = max(abs(h - zone_center) for h in highs) <= max(zone_center * 0.003, 0.75)
            if near1 and closes1[-1] < zone_center:
                one_min_rejection = 35
                trigger = True
        else:
            lows = [_safe_float(x.get("l")) for x in recent]
            closes1 = [_safe_float(x.get("c")) for x in recent]
            near1 = max(abs(l - zone_center) for l in lows) <= max(zone_center * 0.003, 0.75)
            if near1 and closes1[-1] > zone_center:
                one_min_rejection = 35
                trigger = True

    return {
        "approach": _clamp(approach),
        "trigger": trigger,
        "rejection": _clamp(rejection + one_min_rejection),
        "absorption": one_min_absorption,
        "distance": near
    }



def _tradier_cache_get(key, ttl):
    if not ttl:
        return None
    return cache_get(key, ttl)


def _tradier_cache_set(key, value):
    cache_set(key, value)


def _tradier_get(path, params=None, cache_key=None, cache_ttl=0):
    """Small isolated Tradier gateway for options only.

    Polygon remains the structural data source. Tradier is queried only after
    the stock passes the hunt engine, so this adds options access without
    multiplying the structural scan traffic.
    """
    global _tradier_last_request_time, _tradier_disabled_until, _tradier_auth_logged

    if not TRADIER_API_TOKEN:
        return None

    if cache_key and cache_ttl:
        cached = _tradier_cache_get(cache_key, cache_ttl)
        if cached is not None:
            return cached

    now = time.time()
    if now < _tradier_disabled_until:
        return None

    headers = {
        "Authorization": f"Bearer {TRADIER_API_TOKEN}",
        "Accept": "application/json",
    }

    with _tradier_request_lock:
        wait = TRADIER_MIN_INTERVAL - (time.time() - _tradier_last_request_time)
        if wait > 0:
            time.sleep(wait)

        try:
            res = requests.get(
                f"{TRADIER_BASE_URL}{path}",
                params=params or {},
                headers=headers,
                timeout=10,
            )
            _tradier_last_request_time = time.time()
        except requests.RequestException as exc:
            logging.warning("Tradier connection error: %s", exc)
            return None

        if res.status_code in (401, 403):
            # Do not hammer an invalid/unavailable token on every scan.
            _tradier_disabled_until = time.time() + 300
            if not _tradier_auth_logged:
                logging.warning(
                    "Tradier options access unavailable (HTTP %s); "
                    "keeping Polygon as fallback.",
                    res.status_code,
                )
                _tradier_auth_logged = True
            return None

        if res.status_code != 200:
            logging.warning(
                "Tradier API status %s for %s",
                res.status_code,
                path,
            )
            return None

        try:
            payload = res.json()
        except ValueError:
            logging.warning("Tradier returned non-JSON data for %s", path)
            return None

        if cache_key and cache_ttl:
            _tradier_cache_set(cache_key, payload)

        return payload


def _tradier_future_expirations(ticker):
    """Return a small, useful expiry window instead of downloading every chain."""
    payload = _tradier_get(
        "/markets/options/expirations",
        params={
            "symbol": ticker,
            "includeAllRoots": "false",
            "strikes": "false",
            "contractSize": "false",
            "expirationType": "true",
        },
        cache_key=f"tradier:expirations:{ticker}",
        cache_ttl=TRADIER_EXPIRATIONS_CACHE_SECONDS,
    )
    if not payload:
        return []

    node = payload.get("expirations", {})
    dates = node.get("date", []) if isinstance(node, dict) else []
    if isinstance(dates, str):
        dates = [dates]

    today = datetime.now(ZoneInfo("America/New_York")).date()
    out = []
    for value in dates or []:
        try:
            d = datetime.strptime(str(value), "%Y-%m-%d").date()
        except ValueError:
            continue
        dte = (d - today).days
        if dte < 0 or dte > TRADIER_MAX_DTE:
            continue
        out.append(d)

    out = sorted(set(out))
    return [d.isoformat() for d in out[:max(1, TRADIER_MAX_EXPIRIES)]]


def _normalize_tradier_chain(ticker, payload):
    """Map Tradier option-chain fields into the existing Polygon-shaped model."""
    if not payload:
        return []

    node = payload.get("options", {})
    rows = node.get("option", []) if isinstance(node, dict) else []
    if isinstance(rows, dict):
        rows = [rows]

    normalized = []
    for opt in rows or []:
        option_type = str(opt.get("option_type") or opt.get("type") or "").lower()
        ctype = "C" if option_type == "call" else "P" if option_type == "put" else ""
        if not ctype:
            continue

        symbol = opt.get("symbol") or opt.get("contract_symbol")
        expiry = opt.get("expiration_date")
        strike = opt.get("strike")
        if not symbol or not expiry or strike is None:
            continue

        greeks = opt.get("greeks") or {}
        normalized.append({
            "details": {
                "contract_type": ctype,
                "expiration_date": str(expiry),
                "strike_price": strike,
                "ticker": symbol,
            },
            "greeks": {
                "delta": greeks.get("delta", 0),
                "gamma": greeks.get("gamma", 0),
                "implied_volatility": (
                    greeks.get("mid_iv")
                    or greeks.get("smv_vol")
                    or greeks.get("ask_iv")
                    or greeks.get("bid_iv")
                    or 0
                ),
            },
            "day": {
                "volume": opt.get("volume", 0),
                "open_interest": opt.get("open_interest", 0),
            },
            "last_quote": {
                "bid": opt.get("bid", 0),
                "ask": opt.get("ask", 0),
                "last": opt.get("last", 0),
            },
        })
    return normalized


def fetch_option_snapshot_tradier(ticker):
    """Fetch only the nearest useful chains from Tradier, with short caching."""
    expirations = _tradier_future_expirations(ticker)
    if not expirations:
        return []

    all_options = []
    for expiry in expirations:
        payload = _tradier_get(
            "/markets/options/chains",
            params={
                "symbol": ticker,
                "expiration": expiry,
                "greeks": "true",
            },
            cache_key=f"tradier:chain:{ticker}:{expiry}",
            cache_ttl=TRADIER_CHAIN_CACHE_SECONDS,
        )
        if not payload:
            continue
        all_options.extend(_normalize_tradier_chain(ticker, payload))

    return all_options


def _fetch_options_best_source(ticker):
    """Tradier-first options discovery with Polygon fallback."""
    if TRADIER_API_TOKEN:
        tradier_options = fetch_option_snapshot_tradier(ticker)
        if tradier_options:
            return tradier_options, "TRADIER"

    polygon_options = fetch_option_snapshot(ticker)
    if polygon_options:
        return polygon_options, "POLYGON"

    return [], "NONE"


def fetch_option_snapshot(ticker):
    url = f"https://api.polygon.io/v3/snapshot/options/{ticker}?apiKey={POLYGON_API_KEY}"
    res = api_get(url, f"options:{ticker}", OPTIONS_CACHE_SECONDS)
    return res.json().get("results", []) if res else []


def estimate_contract_potential(stock_price, strike, premium, option_type,
                                delta, gamma, iv, days_to_expiry,
                                last_target_stock):
    """
    Scenario estimate using delta/gamma. IV/time are deliberately used as
    context and not converted into fake precision.
    """
    if premium <= 0 or stock_price <= 0:
        return None

    move = last_target_stock - stock_price
    if option_type == "PUT":
        move = stock_price - last_target_stock

    if move <= 0:
        return None

    theoretical_change = delta * move + 0.5 * max(gamma, 0) * (move ** 2)
    estimated_price = max(0.01, premium + theoretical_change)
    potential = (estimated_price / premium - 1) * 100
    return max(0.0, potential), estimated_price


def target_reachability(stock_price, last_target_stock, daily, m15, eta_minutes=None):
    """Separate last-target reachability score, with time fit included."""
    if stock_price <= 0 or last_target_stock <= 0:
        return 0

    distance_pct = abs(last_target_stock / stock_price - 1) * 100
    recent = m15[-20:] if len(m15) >= 5 else m15
    ranges = [abs(_safe_float(x.get("h")) - _safe_float(x.get("l"))) /
              max(_safe_float(x.get("c")), 0.01) * 100 for x in recent]
    avg_range = _mean(ranges)

    daily_ranges = [
        abs(_safe_float(x.get("h")) - _safe_float(x.get("l"))) /
        max(_safe_float(x.get("c")), 0.01) * 100 for x in daily[-14:]
    ]
    daily_range = _mean(daily_ranges)
    volatility = max(avg_range, daily_range, 0.01)
    ratio = distance_pct / volatility

    if ratio <= 1.5:
        score = 95
    elif ratio <= 2.5:
        score = 85
    elif ratio <= 4:
        score = 70
    elif ratio <= 6:
        score = 50
    elif ratio <= 9:
        score = 30
    else:
        score = 10

    if eta_minutes is not None:
        if eta_minutes <= 120:
            time_bonus = 5
        elif eta_minutes <= 240:
            time_bonus = 0
        elif eta_minutes <= 480:
            time_bonus = -10
        else:
            time_bonus = -20
        score = _clamp(score + time_bonus)

    return int(score)


def _reversal_target(stock_price, direction, m15, zone_center):
    """
    Target after the future zone is reached and reverses.
    Prefer meaningful structure behind the zone/current price.
    """
    fibs = _fib_levels(m15)
    profile = _volume_profile(m15)
    candidates = []

    if direction == "PUT":
        for r in (0.786, 0.707, 0.618, 0.5, 0.382):
            v = fibs.get(r)
            if v and v < zone_center:
                candidates.append(v)
        if profile:
            for k in ("poc", "val"):
                if profile.get(k) and profile[k] < zone_center:
                    candidates.append(profile[k])
        recent_low = min(_safe_float(x.get("l")) for x in m15[-48:])
        candidates.append(recent_low)
        below = [v for v in candidates if v < zone_center - max(0.35 * _atr_price(m15), 0.01)]
        if below:
            return max(below)
    else:
        for r in (1.0, 1.13, 1.272, 1.618):
            v = fibs.get(r)
            if v and v > zone_center:
                candidates.append(v)
        if profile and profile.get("poc") and profile["poc"] > zone_center:
            candidates.append(profile["poc"])
        recent_high = max(_safe_float(x.get("h")) for x in m15[-48:])
        candidates.append(recent_high)
        above = [v for v in candidates if v > zone_center + max(0.35 * _atr_price(m15), 0.01)]
        if above:
            return min(above)

    return zone_center


def choose_best_contract(ticker, direction, daily, m15,
                         stock_target=None, zone_analysis=None):
    options, options_provider = _fetch_options_best_source(ticker)
    if not options:
        return None

    stock_price = _safe_float(m15[-1].get("c"))
    phase = get_market_phase()
    zone_center = stock_target if stock_target else stock_price
    last_target_stock = _reversal_target(stock_price, direction, m15, zone_center)
    eta = zone_analysis.get("eta_minutes") if zone_analysis else None
    reach = target_reachability(stock_price, last_target_stock, daily, m15, eta)

    candidates = []

    for opt in options:
        details = opt.get("details", {})
        greeks = opt.get("greeks", {})
        day = opt.get("day", {})
        quote = opt.get("last_quote", {})

        ctype = details.get("contract_type", "").upper()
        if (direction == "CALL" and ctype != "C") or (direction == "PUT" and ctype != "P"):
            continue

        premium = _safe_float(quote.get("ask") or quote.get("last"))
        bid = _safe_float(quote.get("bid"))
        volume = _safe_float(day.get("volume"))
        oi = _safe_float(day.get("open_interest"))
        delta = abs(_safe_float(greeks.get("delta")))
        gamma = abs(_safe_float(greeks.get("gamma")))
        iv = _safe_float(greeks.get("implied_volatility"))
        expiry = details.get("expiration_date")
        strike = details.get("strike_price")

        if not expiry or not strike or premium <= 0:
            continue

        try:
            exp_dt = datetime.strptime(expiry, "%Y-%m-%d").date()
            dte = max(0, (exp_dt - datetime.now(ZoneInfo("America/New_York")).date()).days)
        except ValueError:
            continue

        spread_pct = ((premium - bid) / premium * 100) if bid > 0 else 100
        # Liquidity filters are kept, but not used to force a cheap-premium bias.
        if spread_pct > 35 or volume < 20:
            continue

        result = estimate_contract_potential(
            stock_price, float(strike), float(premium), direction,
            delta, gamma, iv, dte, float(last_target_stock)
        )
        if not result:
            continue

        potential, target_premium = result
        if potential < MIN_POTENTIAL_RETURN:
            continue

        volume_oi = volume / oi if oi else 0
        price_preference = 12 if premium <= PREFERRED_MAX_CONTRACT_PRICE else 0
        liquidity_score = min(15, volume / 100 * 15)
        delta_score = max(0, 15 - abs(delta - 0.30) * 40)
        dte_score = min(15, 5 + min(dte, 20) / 20 * 10)
        reach_score = reach
        potential_score = min(35, potential / 30)
        time_fit = zone_analysis.get("time_fit", 50) if zone_analysis else 50

        total = _clamp(
            price_preference + liquidity_score + delta_score +
            dte_score + (reach_score * 0.25) +
            potential_score + time_fit * 0.10
        )

        exceptional = potential >= EXCEPTIONAL_RETURN

        candidates.append({
            "contract_ticker": details.get("ticker"),
            "stock": ticker,
            "type": direction,
            "strike": strike,
            "expiry": expiry,
            "price": round(float(premium), 2),
            "potential": round(potential, 1),
            "estimated_target_price": round(target_premium, 2),
            "reachability": int(reach),
            "score": int(total),
            "exceptional": exceptional,
            "volume": int(volume),
            "open_interest": int(oi),
            "volume_oi": round(volume_oi, 2),
            "dte": dte,
            "spread_pct": round(spread_pct, 1),
            "phase": phase,
            "options_provider": options_provider,
            "last_target_stock": round(float(last_target_stock), 2),
            "zone_center": round(float(zone_center), 2)
        })

    if not candidates:
        return None

    candidates.sort(key=lambda x: (
        x["reachability"] >= 70,
        x["potential"] >= EXCEPTIONAL_RETURN,
        x["potential"],
        x["reachability"],
        x["price"] <= PREFERRED_MAX_CONTRACT_PRICE,
        x["score"]
    ), reverse=True)

    return candidates[0]


def _state_snapshot(ticker, m15, zone):
    price = _safe_float(m15[-1].get("c"))
    last = m15[-1]
    return {
        "timestamp": time.time(),
        "price": price,
        "volume": _safe_float(last.get("v")),
        "close": price,
        "zone": zone["center"],
    }


def _update_behavior_memory(ticker, m15, zone):
    """
    Lightweight temporal memory: compares the current approach with the
    previous observation without storing a large history.
    """
    state = _state_snapshot(ticker, m15, zone)
    previous = behavior_memory.get(ticker)
    behavior_memory[ticker] = state

    if not previous:
        return {"price_accel": 0, "distance_change": 0, "volume_accel": 0}

    price_change = _pct(state["price"], previous["price"])
    old_dist = abs(previous["price"] - previous["zone"])
    new_dist = abs(state["price"] - state["zone"])
    distance_change = old_dist - new_dist
    volume_change = _pct(state["volume"] + 1, previous["volume"] + 1)

    return {
        "price_accel": price_change,
        "distance_change": distance_change,
        "volume_accel": volume_change
    }


def _init_log():
    if LOG_PATH.exists():
        return
    with LOG_PATH.open("w", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=LOG_FIELDS).writeheader()


def _log_alert(opp):
    _init_log()
    row = {k: opp.get(k, "") for k in LOG_FIELDS}
    with LOG_PATH.open("a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=LOG_FIELDS).writerow(row)


def scan_market_opportunity(ticker):
    daily, m15 = fetch_bars(ticker)
    if len(daily) < 20 or len(m15) < 30:
        return None

    trend = _trend_state(m15)
    if trend["direction"] == "FLAT":
        return None

    # Contrarian hunt direction:
    # up into future upper zone -> PUT; down into future lower zone -> CALL.
    direction = "PUT" if trend["direction"] == "UP" else "CALL"

    zones, fibs, profile = _future_levels(_safe_float(m15[-1].get("c")),
                                           direction, m15)
    if not zones:
        return None

    analyses = []
    for zone in zones:
        a = _zone_analysis(_safe_float(m15[-1].get("c")), direction,
                           zone, daily, m15)
        if a and a["zone_score"] >= EARLY_ZONE_MIN_SCORE:
            analyses.append(a)

    if not analyses:
        return None

    analyses.sort(key=lambda x: (
        x["zone_score"],
        x["rejection_score"] + x["absorption_score"],
        -x["distance_atr"]
    ), reverse=True)
    za = analyses[0]

    # We want the signal BEFORE arrival. If price is already in the zone,
    # this function refuses to call it PRE-HUNT.
    price = _safe_float(m15[-1].get("c"))
    in_zone = za["zone_low"] <= price <= za["zone_high"]
    if in_zone:
        return None

    memory_delta = _update_behavior_memory(ticker, m15,
                                            {"center": za["zone_center"]})

    # Very early warning can be generated from 15m structure alone.
    # Lower timeframes are only requested for stronger/closer candidates.
    mode = "PRE-HUNT"
    trigger = "FUTURE_REJECTION_ZONE"

    if za["distance_atr"] <= APPROACH_DISTANCE_ATR or za["zone_score"] >= EARLY_ZONE_NEAR_SCORE:
        # Stage lower-timeframe requests: 5m confirms approach first; 1m is
        # requested only when the candidate is genuinely near the trigger.
        m5, _ = fetch_lower_timeframes(ticker, include_m1=False)
        approach = _approach_behavior(m5, [], direction, za["zone_center"])

        near_trigger = za["distance_atr"] <= TRIGGER_DISTANCE_ATR
        if near_trigger:
            # Preserve the original trigger behavior: every near-zone
            # candidate still gets 1m confirmation. The saving comes from
            # avoiding 1m requests for candidates that are not near trigger.
            _, m1 = fetch_lower_timeframes(ticker, include_m1=True)
            approach = _approach_behavior(m5, m1, direction, za["zone_center"])
        za["approach_score"] = approach["approach"]
        za["trigger_ready"] = approach["trigger"]
        za["rejection_score"] = max(za["rejection_score"], approach["rejection"])
        za["absorption_score"] = max(za["absorption_score"], approach["absorption"])

        if approach["trigger"] and za["distance_atr"] <= TRIGGER_DISTANCE_ATR:
            mode = "TRIGGER"
            trigger = "EARLY_ZONE_CONFIRMED"
        else:
            mode = "PRE-HUNT"
            trigger = "APPROACHING_FUTURE_ZONE"
    else:
        za["approach_score"] = 0
        za["trigger_ready"] = False

    # Prevent late/chasing alerts: current move must not have consumed the zone.
    # If price has already travelled unusually far in the trend, suppress.
    recent_start = _safe_float(m15[-8].get("c"))
    move_from_recent = abs(_pct(price, recent_start))
    atr_pct = _atr_pct(m15)
    consumed = move_from_recent / max(atr_pct * 2.5, 0.10)
    move_consumed_pct = _clamp(consumed * 100.0, 0, 200)

    # A late signal is a CHASE and is rejected. The experiment is intended
    # to measure genuine early hunting, not post-move option chasing.
    if consumed > 1.15:
        return None

    # Options are queried only after the stock itself qualifies.
    opp = choose_best_contract(
        ticker, direction, daily, m15,
        stock_target=za["zone_center"],
        zone_analysis=za
    )
    if not opp:
        return None

    # Add stock-behaviour fields.
    opp.update({
        "alert_mode": mode,
        "trigger": trigger,
        "zone_low": za["zone_low"],
        "zone_high": za["zone_high"],
        "zone_distance_pct": round(za["distance_pct"], 2),
        "zone_score": round(za["zone_score"], 1),
        "rejection_score": round(za["rejection_score"], 1),
        "absorption_score": round(za["absorption_score"], 1),
        "continuation_score": round(za["continuation_score"], 1),
        "exhaustion_score": round(za["exhaustion_score"], 1),
        "effort_result": round(za["effort_result"], 2),
        "trend_score": round(za["trend_score"], 1),
        "fib_confluence": round(za["fib_confluence"], 1),
        "profile_confluence": round(za["profile_confluence"], 1),
        "expected_move_pct": round(za["expected_move_pct"], 2),
        "eta_minutes": round(za["eta_minutes"], 1),
        "time_fit": round(za["time_fit"], 1),
        "labels": ",".join(za["labels"]),
        "memory_price_accel": round(memory_delta["price_accel"], 3),
        "memory_distance_change": round(memory_delta["distance_change"], 3),
        "memory_volume_accel": round(memory_delta["volume_accel"], 2),
        "timing_class": "HUNT" if mode == "PRE-HUNT" else "HUNT_CONFIRMED",
        "move_consumed_pct": round(move_consumed_pct, 1)
    })

    # Signal score is distinct from reachability.
    opp["score"] = int(_clamp(
        opp["score"] * 0.55 +
        za["zone_score"] * 0.30 +
        za["time_fit"] * 0.15
    ))
    return opp


def format_alert(opp):
    if opp["alert_mode"] == "TRIGGER":
        title = "⚡️ *TRIGGER*"
    else:
        title = "🏌🏼‍♂️ *PRE-HUNT*"

    tag = "🏌🏼‍♂️ *استثنائية*" if opp["exceptional"] else "🔥 *انفجارية*"
    direction = "🟢 CALL ↑" if opp["type"] == "CALL" else "🔴 PUT ↓"

    return f"""
🗽 *THE LEGENDARY*

{title}
📌 `{opp['stock']}` — {direction}
🧭 Timing: `{opp['timing_class']}` | المستهلك من الحركة: `{opp['move_consumed_pct']:.0f}%`

🏹 منطقة الصيد: `{opp['zone_low']}–{opp['zone_high']}`
📍 السعر: `{opp['zone_center']}`
📏 بُعد المنطقة: `{opp['zone_distance_pct']}%`
⏱️ وصول تقديري: `{opp['eta_minutes']:.0f} دقيقة`

{tag}
🎯 Strike: `{opp['strike']}`
📅 Expiry: `{opp['expiry']}` ({opp['dte']} DTE)
💵 Contract: `${opp['price']:.2f}`
📈 السيناريو: `+{opp['potential']:.0f}%`
🎯 هدف العقد: `${opp['estimated_target_price']:.2f}`
🎯 قابلية آخر هدف: `{opp['reachability']}/100`

🧠 Zone: `{opp['zone_score']:.0f}/100`
↩️ رفض: `{opp['rejection_score']:.0f}`
🧱 امتصاص: `{opp['absorption_score']:.0f}`
➡️ مواصلة: `{opp['continuation_score']:.0f}`
🧭 اتجاه: `{opp['trend_score']:.0f}`
📐 Fib: `{opp['fib_confluence']:.0f}`
📊 Profile: `{opp['profile_confluence']:.0f}`
⏳ عامل الوقت: `{opp['time_fit']:.0f}/100`

📊 Vol: `{opp['volume']}`
📊 OI: `{opp['open_interest']}`
📊 Vol/OI: `{opp['volume_oi']}`
📏 Spread: `{opp['spread_pct']}%`

⚡ Trigger: `{opp['trigger']}`
🎯 هدف السهم النهائي: `{opp['last_target_stock']}`
"""


def _monitor_one(opp):
    contract = opp.get("contract_ticker")
    if not contract:
        return None

    # Prefer the same live options source used for discovery.
    if TRADIER_API_TOKEN:
        payload = _tradier_get(
            "/markets/quotes",
            params={"symbols": contract, "greeks": "false"},
            cache_key=f"tradier:quote:{contract}",
            cache_ttl=OPTIONS_CACHE_SECONDS,
        )
        if payload:
            quote_node = payload.get("quotes", {})
            quote = quote_node.get("quote", {}) if isinstance(quote_node, dict) else {}
            if isinstance(quote, list):
                quote = quote[0] if quote else {}
            price = _safe_float(
                quote.get("bid") or quote.get("ask") or quote.get("last")
            )
            if price > 0:
                gain = (price / opp["price"] - 1) * 100
                return price, gain

    # Keep the existing Polygon monitor as a fallback.
    url = (
        f"https://api.polygon.io/v3/snapshot/options/"
        f"{opp['stock']}/{contract}?apiKey={POLYGON_API_KEY}"
    )
    res = api_get(url, f"monitor:{contract}", OPTIONS_CACHE_SECONDS)
    if not res:
        return None

    result = res.json().get("results", {})
    quote = result.get("last_quote", {})
    price = _safe_float(quote.get("bid") or quote.get("ask") or
                        result.get("last_trade", {}).get("price"))
    if price <= 0:
        return None

    gain = (price / opp["price"] - 1) * 100
    return price, gain


def monitor_active_contracts():
    """Centralized monitor: no one thread per alert."""
    now = time.time()
    finished = []

    for key, opp in list(active_monitors.items()):
        try:
            exp = datetime.strptime(
                opp["expiry"], "%Y-%m-%d"
            ).replace(tzinfo=ZoneInfo("America/New_York"))
            expiry_cutoff = exp.timestamp() + 16 * 3600
            if now > expiry_cutoff:
                finished.append(key)
                continue

            result = _monitor_one(opp)
            if not result:
                continue

            price, gain = result
            opp["peak_gain"] = max(opp.get("peak_gain", gain), gain)

            # Alert once when the contract reaches its predefined target.
            target_price = _safe_float(opp.get("estimated_target_price"))
            if target_price > 0 and price >= target_price and not opp.get("target_hit"):
                opp["target_hit"] = True
                send_telegram_alert(
                    f"""
🎯 *TARGET ACHIEVED* ✅

🗽 `{opp['stock']} {opp['type']} {opp['strike']}`
📅 Expiry: `{opp['expiry']}`

💵 العقد: `${price:.2f}`
💵 الدخول: `${opp['price']:.2f}`
📈 العائد: `+{gain:.0f}%`

🎯 الهدف المحدد: `${target_price:.2f}`
🏆 أعلى عائد مسجل: `+{opp['peak_gain']:.0f}%`
"""
                )

        except Exception:
            logging.exception("Monitor error for %s", key)

    for key in finished:
        active_monitors.pop(key, None)


def _register_monitor(opp):
    key = (opp["stock"], opp["contract_ticker"], opp["expiry"])
    if len(active_monitors) >= MAX_ACTIVE_MONITORS:
        # Keep the strongest candidates only.
        weakest_key = min(
            active_monitors,
            key=lambda k: active_monitors[k].get("score", 0)
        )
        if active_monitors[weakest_key].get("score", 0) >= opp.get("score", 0):
            return
        active_monitors.pop(weakest_key, None)
    active_monitors[key] = opp


def _ordered_assets_for_cycle():
    """Prioritize active/accelerating candidates without removing any asset."""
    if not behavior_memory:
        return list(TARGET_ASSETS)

    def priority(ticker):
        state = behavior_memory.get(ticker, {})
        accel = abs(_safe_float(state.get("volume", 0)))
        return accel

    known = [a for a in TARGET_ASSETS if a in behavior_memory]
    unknown = [a for a in TARGET_ASSETS if a not in behavior_memory]
    known.sort(key=priority, reverse=True)
    return known + unknown


def _smart_assets_for_cycle(now):
    """Select only the most useful due tickers for this cycle.

    The complete universe remains eligible. Strong/active candidates are
    revisited quickly; quiet candidates are rotated more slowly. This is a
    request-scheduling layer only and does not alter the hunt engine.
    """
    ordered = _ordered_assets_for_cycle()
    due = [a for a in ordered if now >= _safe_float(search_state.get(a, {}).get("next_scan", 0))]

    # First give already-known active candidates priority, then rotate through
    # untouched/quiet names. This prevents a burst of 20x structural requests.
    due.sort(key=lambda a: (
        _safe_float(search_state.get(a, {}).get("priority", 0)),
        1 if a in behavior_memory else 0,
        _safe_float(search_state.get(a, {}).get("last_scan", 0))
    ), reverse=True)
    return due[:max(1, MAX_STRUCTURAL_SCANS_PER_CYCLE)]


def _schedule_next_scan(ticker, opp=None):
    """Adapt the next structural scan interval from observed opportunity strength."""
    now = time.time()
    state = search_state.setdefault(ticker, {})

    if opp:
        zone_score = _safe_float(opp.get("zone_score"))
        distance = _safe_float(opp.get("zone_distance_pct"))
        trigger = opp.get("alert_mode") == "TRIGGER"
        if trigger:
            cooldown = HOT_SCAN_COOLDOWN_SECONDS
            priority = 3
        elif zone_score >= EARLY_ZONE_NEAR_SCORE:
            cooldown = ACTIVE_SCAN_COOLDOWN_SECONDS
            priority = 2
        elif zone_score >= EARLY_ZONE_MIN_SCORE:
            cooldown = ACTIVE_SCAN_COOLDOWN_SECONDS
            priority = 1
        else:
            cooldown = NORMAL_SCAN_COOLDOWN_SECONDS
            priority = 0
        state["priority"] = priority
        state["zone_score"] = zone_score
        state["distance_pct"] = distance
    else:
        # No qualifying opportunity: slow this ticker down, but keep rotating
        # it through the universe so a later setup is still discovered.
        cooldown = NORMAL_SCAN_COOLDOWN_SECONDS
        state["priority"] = max(0, _safe_float(state.get("priority", 0)) - 1)

    state["last_scan"] = now
    state["next_scan"] = now + max(30, cooldown)


def main_engine():
    if not POLYGON_API_KEY:
        raise RuntimeError("POLYGON_API_KEY is not configured.")

    _init_log()

    send_telegram_alert(
        "🗽⚡️ *THE LEGENDARY V2 بدأ العمل — PRE-HUNT engine*"
        "\nلا يوجد حد لعدد التنبيهات."
    )

    last_monitor = 0.0

    while True:
        if not is_us_market_open():
            time.sleep(180)
            continue

        cycle_start = time.time()

        assets_this_cycle = _smart_assets_for_cycle(time.time())
        for asset in assets_this_cycle:
            try:
                opp = scan_market_opportunity(asset)
                _schedule_next_scan(asset, opp)
                if not opp:
                    continue

                key = (opp["stock"], opp["contract_ticker"], opp["expiry"])
                now = time.time()

                # Same contract cannot re-alert inside 45 minutes.
                if now - alerted.get(key, 0) < 2700:
                    continue
                alerted[key] = now

                _log_alert(opp)

                image = generate_card_image(
                    opp["stock"], opp["type"],
                    opp["strike"], opp["expiry"],
                    mode=opp["alert_mode"]
                )
                send_telegram_alert(format_alert(opp), image)
                _register_monitor(opp)

                logging.info(
                    "ALERT %s %s zone=%.1f potential=%.1f reach=%s",
                    opp["stock"], opp["type"], opp["zone_score"],
                    opp["potential"], opp["reachability"]
                )

            except Exception:
                logging.exception("Scan error for %s", asset)

        if time.time() - last_monitor >= MONITOR_INTERVAL_SECONDS:
            monitor_active_contracts()
            last_monitor = time.time()

        elapsed = time.time() - cycle_start
        time.sleep(max(5, SCAN_INTERVAL_SECONDS - elapsed))


def run_forever(send=None, restart_delay=60):
    """يشغّل صياد العقود للأبد (يستخدمه السكانر في Thread).
    send = دالة إرسال (message, image_path). لو طاح المحرك يرجع يشتغل بعد دقيقة."""
    global EXTERNAL_SENDER
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO,
                            format="%(asctime)s - %(levelname)s - %(message)s")
    if send is not None:
        EXTERNAL_SENDER = send
    while True:
        try:
            main_engine()
        except Exception as exc:
            logging.exception("THE LEGENDARY crashed, restarting")
            send_telegram_alert(f"⚠️ *صياد العقود توقف وبيرجع يشتغل:* `{exc}`")
            time.sleep(restart_delay)


def main():
    if "--test" in sys.argv:
        self_test()
        return
    if "--algotest" in sys.argv:
        algo_self_test()
        return
    if "--newstest" in sys.argv:
        news_self_test()
        return
    if "--wsweeptest" in sys.argv:
        wsweep_self_test()
        return
    if "--sweeptest" in sys.argv:
        sweep_self_test()
        return
    if "--optionstest" in sys.argv:
        legendary_self_test()
        return
    once = "--once" in sys.argv
    _load_chats()
    discover_groups()
    log(f"التنبيهات بتروح لـ {len(CHATS)} محادثة: {', '.join(CHATS) or 'ولا وحدة'}")
    if not once:
        start_algo_thread()
        start_news_thread()
        start_legendary_thread()      # (8) صياد العقود THE LEGENDARY
        try:   # قائمة IFVG الأسبوعية (كل جمعة)
            import weekly_ifvg
            threading.Thread(target=weekly_ifvg.run_forever, kwargs={"send": send_telegram},
                             daemon=True, name="weekly_ifvg").start()
        except Exception as e:
            log(f"IFVG الأسبوعي: ما اشتغل: {e}")

    gap_tickers, gap_day, gap_last = [], None, None
    gap15_tickers = []
    gap1d_day = None
    sweep_day, sweep_tickers, sweep_tickers_day = None, [], None
    try:
        with open(WSWEEP_WEEK_FILE, encoding="utf-8") as f:
            wsweep_week = f.read().strip() or None
    except FileNotFoundError:
        wsweep_week = None
    log("الجاب: " + ("24 ساعة (مع الجلسة الليلية من Tiingo)" if GAP_OVERNIGHT else
                     "الجلسة الممتدة 4 الفجر - 8 بالليل نيويورك (ياهو مجاناً)" if GAP_EXTENDED else
                     "الجلسة الرسمية بس"))
    was_open = None
    gap_sent = _load_set(GAP_SENT_FILE)
    flow_tickers, flow_day, flow_last = [], None, 0.0
    flow_sent = _load_set(FLOW_SENT_FILE)
    daily_week = next(iter(_load_set(DAILY_WEEK_FILE)), None)
    short_day = None
    short_sent = _load_set(SHORT_SENT_FILE)
    rsplit_sent = _load_set(RSPLIT_SENT_FILE)
    rsplit_new_sent = _load_set(RSPLIT_NEW_FILE)
    rsplit_state = _rsplit_state()

    while True:
        discover_groups()
        # (1) الجاب - بعد إغلاق كل شمعة بدقيقة
        now_ny = pd.Timestamp.now(tz=NY)
        slot = gap_scan_due(now_ny, gap_last)
        if ENABLE_GAP and (once or (slot is not None and us_market_open(now_ny))):
            gap_last = slot or now_ny
            today = pd.Timestamp.now(tz=NY).date()
            if gap_day != today or not gap_tickers:
                gap_tickers = get_gap_universe()
                log(f"الجاب: {len(gap_tickers)} سهم ({' + '.join(e.upper() for e in GAP_EXCHANGES)}) "
                    f"قيمتها السوقية {MIN_MARKET_CAP/1e9:.0f} مليار وفوق")
                if ENABLE_GAP_15M:
                    gap15_tickers = build_universe("الجاب 15 دقيقة", GAP15_MIN_PRICE,
                                                   GAP15_MAX_PRICE, GAP15_MIN_AVG_VOLUME,
                                                   include_nyse=False)
                gap_day = today
            # (أ) فريم 4 ساعات والساعة - أسهم الملياري دولار وسعر 10$ وفوق
            # + صناديق SPY و QQQ (الساعة والأربع ساعات بس)
            watch = set(WATCH_SYMBOLS) if ENABLE_WATCH else set()
            normal = [t for t in gap_tickers if t not in watch]
            if ENABLE_GAP_4H or ENABLE_GAP_1H:
                scan_gap(normal + [e for e in GAP_ETFS if e not in normal], gap_sent)
            # (هـ) قائمة المراقبة - IFVG على 15 دقيقة وساعة و4 ساعات، الجاب أكثر من 15 سنت
            if ENABLE_WATCH and WATCH_SYMBOLS:
                scan_gap(WATCH_SYMBOLS, gap_sent,
                         frames=[(True, 15, "w15", "فريم 15 دقيقة"),
                                 (True, 60, "w1h", "فريم ساعة"),
                                 (True, 240, "w4h", "فريم 4 ساعات")],
                         min_price=0, min_size=WATCH_MIN_SIZE,
                         tag_label=" (قائمة المراقبة)", msg_fn=_watch_message)
            # (ج) فريم 15 دقيقة النظيف - نفس أسهم الساعة، الشموع الثلاث بدون فراغ، والجاب 2$ وفوق
            if ENABLE_GAP_15M_CLEAN:
                scan_gap(normal, gap_sent,
                         frames=[(True, 15, "15mc", "فريم 15 دقيقة (بدون فراغ)", check_pattern_clean)],
                         min_size=GAP15C_MIN_SIZE, tag_label=" (15 دقيقة بدون فراغ)")
            # (ب) فريم 15 دقيقة - أسهم من 1$ إلى 15$ بدون شرط القيمة السوقية
            if ENABLE_GAP_15M and gap15_tickers:
                scan_gap(gap15_tickers, gap_sent,
                         frames=[(True, 15, "15m", "فريم 15 دقيقة")],
                         min_price=GAP15_MIN_PRICE, max_price=GAP15_MAX_PRICE,
                         min_size=GAP15_MIN_SIZE, tag_label=" (15 دقيقة)")

        # (1ب) الجاب اليومي - مرة باليوم بعد إغلاق السوق
        now_ny = pd.Timestamp.now(tz=NY)
        if ENABLE_GAP and ENABLE_GAP_1D and gap1d_day != now_ny.date() and (
                once or (now_ny.weekday() < 5 and (now_ny.hour, now_ny.minute) >= GAP_1D_AFTER_NY)):
            if gap_day != now_ny.date() or not gap_tickers:
                gap_tickers = get_gap_universe()
                gap_day = now_ny.date()
            scan_gap_daily(gap_tickers, gap_sent)
            gap1d_day = now_ny.date()

        # (1د) سحب سيولة دعمين - يومي، مرة باليوم بعد الإغلاق
        now_ny = pd.Timestamp.now(tz=NY)
        if ENABLE_SWEEP and sweep_day != now_ny.date() and (
                once or (now_ny.weekday() < 5 and (now_ny.hour, now_ny.minute) >= SWEEP_AFTER_NY)):
            if not sweep_tickers or sweep_tickers_day != now_ny.date():
                sweep_tickers = sorted(nasdaq_nyse_above_cap(SWEEP_MIN_MARKET_CAP))
                sweep_tickers_day = now_ny.date()
                log(f"سحب السيولة: {len(sweep_tickers)} سهم قيمتها السوقية "
                    f"{SWEEP_MIN_MARKET_CAP / 1e9:.0f} مليار وفوق")
            scan_sweep_daily(sweep_tickers, gap_sent)
            sweep_day = now_ny.date()

        # (1و) سحب سيولة دعمين - أسبوعي، كل جمعة بعد الإغلاق
        now_ny = pd.Timestamp.now(tz=NY)
        iso = now_ny.isocalendar()
        wk = f"{iso[0]}-W{iso[1]:02d}"
        if ENABLE_WSWEEP and wsweep_week != wk and (
                once or (now_ny.weekday() == WSWEEP_WEEKDAY
                         and (now_ny.hour, now_ny.minute) >= WSWEEP_AFTER_NY)):
            wtick = sorted(nasdaq_nyse_above_cap(WSWEEP_MIN_MARKET_CAP))
            log(f"سحب السيولة الأسبوعي: {len(wtick)} سهم قيمتها السوقية "
                f"{WSWEEP_MIN_MARKET_CAP / 1e9:.0f} مليار وفوق")
            scan_sweep_weekly(wtick, gap_sent)
            wsweep_week = wk
            try:
                with open(WSWEEP_WEEK_FILE, "w", encoding="utf-8") as f:
                    f.write(wk + "\n")
            except Exception:
                pass

        # (2) ماسح السيولة - وقت السوق الرسمي، كل 5 دقايق
        if ENABLE_FLOW and (regular_session_open() or once) \
                and time.time() - flow_last >= FLOW_EVERY_MIN * 60:
            today = pd.Timestamp.now(tz=NY).date()
            if flow_day != today or not flow_tickers:
                flow_tickers = build_universe("ماسح السيولة", FLOW_MIN_PRICE, FLOW_MAX_PRICE,
                                              FLOW_MIN_AVG_VOLUME, include_nyse=False)
                flow_day = today
            scan_flow(flow_tickers, flow_sent)
            flow_last = time.time()

        # (3) القاع المزدوج W - قائمة وحدة كل جمعة بعد الإغلاق
        now_ny = pd.Timestamp.now(tz=NY)
        iso = now_ny.isocalendar()
        week = f"{iso[0]}-W{iso[1]:02d}"
        if ENABLE_DAILY and (once or (now_ny.weekday() == DAILY_WEEKDAY
                                      and (now_ny.hour, now_ny.minute) >= DAILY_AFTER_NY
                                      and daily_week != week)):
            daily_tickers = build_universe("اليومي", DAILY_MIN_PRICE, 100_000,
                                           DAILY_MIN_AVG_VOLUME, include_nyse=False)
            big = nasdaq_above_cap(DAILY_MIN_MARKET_CAP)
            daily_tickers = [t for t in daily_tickers if t in big]
            log(f"النماذج: {len(daily_tickers)} سهم قيمتها السوقية "
                f"{DAILY_MIN_MARKET_CAP / 1e9:.0f} مليار وفوق")
            scan_daily(daily_tickers)
            daily_week = week
            try:
                with open(DAILY_WEEK_FILE, "w", encoding="utf-8") as f:
                    f.write(week + "\n")
            except Exception:
                pass

        # (4ب) التجزئة العكسية - الجديد كل يوم، قائمة كل جمعة، وقائمة أول الشهر
        if ENABLE_RSPLIT_SHORT:
            rsplit_job(rsplit_state, rsplit_new_sent, rsplit_sent, force=once)

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
            log(f"[{datetime.now():%H:%M}] السوق مسكر، أنتظر...")
        was_open = is_open

        if once:
            break
        time.sleep(LOOP_SLEEP_SEC)


if __name__ == "__main__":
    main()
