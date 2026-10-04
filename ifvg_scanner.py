# -*- coding: utf-8 -*-
"""
سكانر الIFVG في مناطق السيولة / الدعم — فريم ساعة و 4 ساعات
-----------------------------------------------------------------
الشروط (شراء فقط):
  1) القيمة السوقية للسهم 10 مليار دولار أو أكثر
  2) فيه فجوة هابطة (Bearish FVG)
  3) شمعة خضراء (الإغلاق أعلى من الافتتاح) تقفل فوق الفجوة كاملة => الفجوة انعكست وصارت دعم (IFVG)
  4) ويكون الانعكاس في واحدة من الحالتين:
       أ) منطقة سيولة: السعر كسر قاع سابق (Swing Low) ورجع — سحب سيولة
       ب) عند دعم: منطقة الـ IFVG فوق/على قاع سابق صامد (ما انكسر بإغلاق)
  5) تنبيه أول عند الانعكاس، وتنبيه ثاني لما السعر يرجع يختبر المنطقة ويقفل بشمعة خضراء فوقها

يشتغل لحاله:   python -u ifvg_scanner.py
أو من داخل البوت:
    import ifvg_scanner
    threading.Thread(target=ifvg_scanner.run_forever, kwargs={"send": send_telegram}, daemon=True).start()

المتغيرات (Railway Variables):
  ALPACAAPIKEY, ALPACASECRETKEY       مفاتيح ألباكا (موجودة عندك)
  TELEGRAM_TOKEN, TELEGRAM_CHAT_ID    تليجرام (TELEGRAM_CHAT_ID يقبل أكثر من رقم بينها فاصلة)
  IFVG_MIN_MCAP       أقل قيمة سوقية بالدولار — الافتراضي 10000000000 (10 مليار)
  IFVG_SYMBOLS        قائمة أسهم ثابتة (اختياري). لو حطيتها يتجاهل فلتر القيمة السوقية التلقائي
  IFVG_TIMEFRAMES     الافتراضي: 1Hour,4Hour
  IFVG_FEED           الافتراضي: sip
"""
import json
import os
import time
from datetime import datetime, timedelta, timezone

import requests

# ------------------------------------------------------------------ الإعدادات
FALLBACK_SYMBOLS = (
    "LITE,MU,NVDA,AMD,AVGO,TSLA,AAPL,MSFT,META,AMZN,GOOGL,NFLX,PLTR,SMCI,"
    "COIN,MSTR,ARM,TSM,ANET,CRWD,SHOP,UBER"
)
FIXED_SYMBOLS = [s.strip().upper() for s in os.getenv("IFVG_SYMBOLS", "").split(",") if s.strip()]
MIN_MCAP = float(os.getenv("IFVG_MIN_MCAP", "10000000000"))
TIMEFRAMES = [t.strip() for t in os.getenv("IFVG_TIMEFRAMES", "1Hour,4Hour").split(",") if t.strip()]
FEED = os.getenv("IFVG_FEED", "sip")
DATA_DELAY_MIN = 16 if FEED == "sip" else 0       # بيانات SIP المجانية متأخرة 15 دقيقة
DATA_DIR = "/data" if os.path.isdir("/data") else "."
STATE_FILE = os.getenv("IFVG_STATE_FILE", os.path.join(DATA_DIR, "ifvg_state.json"))
UNIVERSE_FILE = os.path.join(DATA_DIR, "ifvg_universe.json")
UNIVERSE_REFRESH_SEC = 24 * 3600                  # نحدّث قائمة الأسهم مرة باليوم

TF_MINUTES = {"1Hour": 60, "4Hour": 240}
TF_AR = {"1Hour": "ساعة", "4Hour": "4 ساعات"}
HISTORY_DAYS = {"1Hour": 25, "4Hour": 90}

PIVOT_LEFT = 3          # شموع يسار القاع/القمة
PIVOT_RIGHT = 2         # شموع يمين القاع/القمة
ATR_LEN = 14
MIN_GAP_ATR = 0.15      # أقل حجم للفجوة = 0.15 × ATR (يفلتر الفجوات التافهة)
FVG_MAX_AGE = 30        # أقدم فجوة نحسبها (بالشموع) قبل الانعكاس
SWEEP_WINDOW = 15       # السحب لازم يكون خلال آخر 15 شمعة قبل الانعكاس
SUPPORT_LOOKBACK = 60   # نبحث عن الدعم في آخر 60 شمعة
SUPPORT_ATR = 0.5       # الدعم لازم يكون قريب من المنطقة (خلال 0.5 × ATR تحتها أو داخلها)
RETEST_MAX_BARS = 20    # بعد الانعكاس، نراقب إعادة الاختبار لمدة 20 شمعة
ALERT_LOOKBACK = 3      # نرسل فقط لو الحدث صار بآخر 3 شموع مقفلة (ما نرسل قديم)
SCAN_EVERY_SEC = 300

ALPACA_URL = "https://data.alpaca.markets/v2/stocks/bars"
NASDAQ_URL = "https://api.nasdaq.com/api/screener/stocks"


# ------------------------------------------------------------------ قائمة الأسهم (قيمة سوقية ≥ 10 مليار)
def _parse_mcap(v):
    try:
        return float(str(v).replace(",", "").replace("$", "").strip() or 0)
    except ValueError:
        return 0.0


def _fetch_universe():
    """كل الأسهم الأمريكية من سكرينر ناسداك (مجاني) — يرجع {symbol: market_cap} للي ≥ MIN_MCAP."""
    r = requests.get(
        NASDAQ_URL,
        params={"tableonly": "true", "limit": "10000", "download": "true"},
        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
        timeout=60,
    )
    r.raise_for_status()
    rows = ((r.json().get("data") or {}).get("rows")) or []
    out = {}
    for row in rows:
        sym = (row.get("symbol") or "").strip().upper().replace("/", ".")
        if not sym or "^" in sym or " " in sym:
            continue
        mcap = _parse_mcap(row.get("marketCap"))
        if mcap >= MIN_MCAP:
            out[sym] = mcap
    return out


def get_universe():
    """يرجع {symbol: market_cap}. يستخدم الكاش لو عمره أقل من يوم."""
    if FIXED_SYMBOLS:
        return {s: 0.0 for s in FIXED_SYMBOLS}
    cache = {}
    try:
        with open(UNIVERSE_FILE, encoding="utf-8") as f:
            cache = json.load(f)
    except Exception:
        pass
    fresh = (cache.get("min_mcap") == MIN_MCAP
             and time.time() - cache.get("ts", 0) < UNIVERSE_REFRESH_SEC
             and cache.get("symbols"))
    if fresh:
        return cache["symbols"]
    try:
        syms = _fetch_universe()
        if len(syms) < 50:
            raise ValueError(f"القائمة قصيرة بشكل غريب ({len(syms)})")
        try:
            with open(UNIVERSE_FILE, "w", encoding="utf-8") as f:
                json.dump({"ts": time.time(), "min_mcap": MIN_MCAP, "symbols": syms}, f)
        except Exception as e:
            print(f"IFVG: ما قدرت أحفظ قائمة الأسهم: {e}")
        print(f"IFVG: تحدثت القائمة — {len(syms)} سهم قيمتها السوقية ≥ {_fmt_mcap(MIN_MCAP)}")
        return syms
    except Exception as e:
        print(f"IFVG: ما قدرت أجيب القيم السوقية ({e})")
        if cache.get("symbols"):
            return cache["symbols"]           # نكمل على القائمة القديمة
        return {s: 0.0 for s in FALLBACK_SYMBOLS.split(",")}


def _fmt_mcap(v):
    if not v:
        return "—"
    if v >= 1e12:
        return f"{v / 1e12:.2f}T"
    return f"{v / 1e9:.1f}B"


# ------------------------------------------------------------------ البيانات
def fetch_bars(symbols, timeframe):
    """يرجع {symbol: [bar,...]} كل bar = dict(t,o,h,l,c,v) — شموع مقفلة فقط."""
    headers = {
        "APCA-API-KEY-ID": os.getenv("ALPACAAPIKEY", ""),
        "APCA-API-SECRET-KEY": os.getenv("ALPACASECRETKEY", ""),
    }
    now = datetime.now(timezone.utc)
    end = now - timedelta(minutes=DATA_DELAY_MIN)
    start = now - timedelta(days=HISTORY_DAYS[timeframe])
    out = {}
    for i in range(0, len(symbols), 50):
        params = {
            "symbols": ",".join(symbols[i:i + 50]),
            "timeframe": timeframe,
            "start": start.isoformat().replace("+00:00", "Z"),
            "end": end.isoformat().replace("+00:00", "Z"),
            "limit": 10000,
            "adjustment": "split",
            "feed": FEED,
        }
        while True:
            try:
                r = requests.get(ALPACA_URL, headers=headers, params=params, timeout=30)
                r.raise_for_status()
            except Exception as e:
                print(f"IFVG {timeframe}: دفعة {i // 50 + 1} فشلت: {e}")
                break
            js = r.json()
            for sym, bars in (js.get("bars") or {}).items():
                out.setdefault(sym, []).extend(bars)
            tok = js.get("next_page_token")
            if not tok:
                break
            params["page_token"] = tok
    # شيل الشمعة اللي ما قفلت
    tf_min = TF_MINUTES[timeframe]
    for sym, bars in out.items():
        if bars:
            t_last = datetime.fromisoformat(bars[-1]["t"].replace("Z", "+00:00"))
            if t_last + timedelta(minutes=tf_min) > end:
                bars.pop()
    return out


# ------------------------------------------------------------------ المنطق
def _atr(bars, n=ATR_LEN):
    out, prev_c, val = [], None, None
    for b in bars:
        tr = b["h"] - b["l"] if prev_c is None else max(b["h"] - b["l"], abs(b["h"] - prev_c), abs(b["l"] - prev_c))
        val = tr if val is None else (val * (n - 1) + tr) / n
        out.append(val)
        prev_c = b["c"]
    return out


def _pivots(bars):
    """قيعان مؤكدة: (index, price)"""
    lows = []
    for i in range(PIVOT_LEFT, len(bars) - PIVOT_RIGHT):
        win = bars[i - PIVOT_LEFT:i + PIVOT_RIGHT + 1]
        if bars[i]["l"] == min(b["l"] for b in win):
            lows.append((i, bars[i]["l"]))
    return lows


def _bear_fvgs(bars, atr):
    """الفجوات الهابطة: dict(idx, bottom, top)"""
    fvgs = []
    for i in range(2, len(bars)):
        a, c = bars[i - 2], bars[i]
        if c["h"] < a["l"] and (a["l"] - c["h"]) >= MIN_GAP_ATR * atr[i]:
            fvgs.append({"idx": i, "bottom": c["h"], "top": a["l"]})
    return fvgs


def _green(b):
    return b["c"] > b["o"]


def _sweep(bars, lows, j):
    """هل صار سحب سيولة (كسر قاع سابق) خلال SWEEP_WINDOW قبل الشمعة j؟ يرجع (sweep_idx, level) أو None"""
    lo = max(0, j - SWEEP_WINDOW)
    for k in range(j, lo - 1, -1):
        cands = [(pi, pp) for pi, pp in lows if pi + PIVOT_RIGHT < k and k - pi <= 60]
        if cands and bars[k]["l"] < cands[-1][1]:
            return k, cands[-1][1]
    return None


def _support(bars, lows, f, inv, atr_v):
    """
    دعم: قاع سابق مؤكد قبل الانعكاس، مستواه داخل المنطقة أو تحتها بمسافة ≤ SUPPORT_ATR × ATR،
    وما انكسر بإغلاق من وقت تكوينه لين الانعكاس. يرجع المستوى أو None (يختار الأقرب للمنطقة).
    """
    best = None
    for pi, pp in lows:
        if pi + PIVOT_RIGHT >= inv or inv - pi > SUPPORT_LOOKBACK:
            continue
        if not (f["bottom"] - SUPPORT_ATR * atr_v <= pp <= f["top"]):
            continue
        if any(bars[k]["c"] < pp for k in range(pi + 1, inv + 1)):
            continue  # الدعم انكسر بإغلاق
        if best is None or pp > best:
            best = pp
    return best


def detect(bars):
    """
    يرجع قائمة أحداث (شراء فقط):
      {type: 'inversion'|'retest', side: 'long', zone:(bottom,top), fvg_idx, inv_idx, idx,
       reason: 'sweep'|'support', level}
    """
    if len(bars) < 40:
        return []
    atr = _atr(bars)
    lows = _pivots(bars)
    events = []
    n = len(bars)

    for f in _bear_fvgs(bars, atr):
        # أول شمعة تقفل فوق الفجوة كاملة = الانعكاس، ولازم تكون خضراء
        inv = None
        for j in range(f["idx"] + 1, min(n, f["idx"] + 1 + FVG_MAX_AGE)):
            if bars[j]["c"] > f["top"]:
                inv = j
                break
        if inv is None or not _green(bars[inv]):
            continue

        # الحالة أ: منطقة سيولة
        sw = _sweep(bars, lows, inv)
        if sw and sw[0] >= f["idx"] - 5:
            reason, level = "sweep", sw[1]
        else:
            # الحالة ب: عند دعم
            sup = _support(bars, lows, f, inv, atr[inv])
            if sup is None:
                continue
            reason, level = "support", sup

        zone = (round(f["bottom"], 2), round(f["top"], 2))
        base = {"side": "long", "zone": zone, "fvg_idx": f["idx"], "inv_idx": inv,
                "reason": reason, "level": round(level, 2)}
        events.append({**base, "type": "inversion", "idx": inv})

        # إعادة الاختبار: يلمس المنطقة ويقفل بشمعة خضراء فوقها
        for k in range(inv + 1, min(n, inv + 1 + RETEST_MAX_BARS)):
            b = bars[k]
            if b["c"] < f["bottom"]:
                break  # فشل — قفل تحت المنطقة
            if b["l"] <= f["top"] and b["c"] >= f["top"] and _green(b):
                events.append({**base, "type": "retest", "idx": k})
                break
    return _merge(events)


def _merge(events):
    """يدمج الفجوات المتداخلة بنفس الحدث في منطقة وحدة (عشان ما يتكرر التنبيه)."""
    out = []
    for ev in sorted(events, key=lambda e: (e["type"], e["zone"][0])):
        last = out[-1] if out else None
        if (last and last["type"] == ev["type"]
                and abs(last["idx"] - ev["idx"]) <= 2 and ev["zone"][0] <= last["zone"][1]):
            last["zone"] = (min(last["zone"][0], ev["zone"][0]), max(last["zone"][1], ev["zone"][1]))
            last["idx"] = max(last["idx"], ev["idx"])
            last["fvg_idx"] = min(last["fvg_idx"], ev["fvg_idx"])
            if ev["reason"] == "sweep":       # السحب أقوى، نقدمه
                last["reason"], last["level"] = "sweep", ev["level"]
            continue
        out.append(dict(ev))
    return sorted(out, key=lambda e: e["idx"])


# ------------------------------------------------------------------ الرسالة
def _riyadh(ts):
    t = datetime.fromisoformat(ts.replace("Z", "+00:00")) + timedelta(hours=3)
    return t.strftime("%m-%d %H:%M")


def format_msg(sym, tf, ev, bars, mcap=0.0):
    b = bars[ev["idx"]]
    bot, top = ev["zone"]
    if ev["type"] == "inversion":
        head = "🟢 IFVG"
        what = "شمعة خضراء قفلت فوق فجوة هابطة — الفجوة انقلبت دعم"
    else:
        head = "🟢 إعادة اختبار IFVG"
        what = "السعر رجع للمنطقة وقفل بشمعة خضراء فوقها — المنطقة صمدت كدعم"
    if ev["reason"] == "sweep":
        where = f"منطقة سيولة (كسر القاع {ev['level']} ورجع)"
    else:
        where = f"عند دعم {ev['level']}"
    mcap_line = f"القيمة السوقية: {_fmt_mcap(mcap)}\n" if mcap else ""
    return (
        f"🤖 بوت سافونا — {head}\n"
        f"⚠️ محتوى تعليمي فقط، وليس توصية بيع أو شراء. القرار مسؤوليتك.\n\n"
        f"السهم: ${sym}\n"
        f"{mcap_line}"
        f"الفريم: {TF_AR.get(tf, tf)}\n"
        f"السعر: ${b['c']:.2f}\n"
        f"منطقة الـ IFVG: {bot} - {top}\n"
        f"المكان: {where}\n"
        f"تلغى الفكرة عند: إغلاق تحت {bot}\n"
        f"وقت الشمعة: {_riyadh(b['t'])} (توقيتك)\n"
        f"المصدر: Alpaca ({FEED.upper()})\n\n"
        f"📚 {what}."
    )


# ------------------------------------------------------------------ التليجرام والحالة
def _default_send(text):
    token = os.getenv("TELEGRAM_TOKEN", "")
    for chat in [c.strip() for c in os.getenv("TELEGRAM_CHAT_ID", "").split(",") if c.strip()]:
        try:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          data={"chat_id": chat, "text": text}, timeout=15)
        except Exception as e:
            print(f"IFVG: ما قدرت أرسل لـ {chat}: {e}")


def _load_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_state(st):
    # نخلي آخر 5000 مفتاح بس
    if len(st) > 5000:
        st = dict(sorted(st.items(), key=lambda kv: kv[1])[-5000:])
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(st, f)
    except Exception as e:
        print(f"IFVG: ما قدرت أحفظ الحالة: {e}")
    return st


def scan_once(send=None):
    send = send or _default_send
    state = _load_state()
    universe = get_universe()
    symbols = sorted(universe)
    new = 0
    for tf in TIMEFRAMES:
        try:
            data = fetch_bars(symbols, tf)
        except Exception as e:
            print(f"IFVG {tf}: خطأ بالبيانات: {e}")
            continue
        for sym, bars in data.items():
            for ev in detect(bars):
                if ev["idx"] < len(bars) - ALERT_LOOKBACK:
                    continue
                key = f"{sym}|{tf}|{bars[ev['fvg_idx']]['t']}|long|{ev['type']}"
                if key in state:
                    continue
                send(format_msg(sym, tf, ev, bars, universe.get(sym, 0.0)))
                state[key] = int(time.time())
                new += 1
    _save_state(state)
    print(f"[{datetime.now(timezone.utc) + timedelta(hours=3):%H:%M}] الإنفيرجن جاب: خلص الفحص "
          f"({len(symbols)} سهم) - {new} تنبيه جديد")
    return new


def run_forever(send=None):
    print(f"الإنفيرجن جاب: بدأ المراقبة — أسهم قيمتها السوقية ≥ {_fmt_mcap(MIN_MCAP)} "
          f"على فريم {', '.join(TF_AR.get(t, t) for t in TIMEFRAMES)}")
    while True:
        try:
            scan_once(send)
        except Exception as e:
            print(f"IFVG: خطأ: {e}")
        time.sleep(SCAN_EVERY_SEC)


if __name__ == "__main__":
    run_forever()
