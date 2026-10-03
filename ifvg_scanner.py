# -*- coding: utf-8 -*-
"""
سكانر الIFVG في مناطق السيولة — فريم ساعة و 4 ساعات
-----------------------------------------------------------------
النموذج (شراء):
  1) السعر يكسر قاع سابق (Swing Low) ويرجع — سحب سيولة (Liquidity Sweep)
  2) فيه فجوة هابطة (Bearish FVG) تكونت قبل الكسر أو أثناء النزول
  3) شمعة تقفل فوق الفجوة كاملة  => الفجوة انعكست وصارت دعم (IFVG)
  4) تنبيه أول عند الانعكاس، وتنبيه ثاني لما السعر يرجع يختبر المنطقة ويثبت فوقها
النموذج (بيع) نفس الشي بالعكس.

يشتغل لحاله:   python -u ifvg_scanner.py
أو من داخل البوت:
    import ifvg_scanner
    threading.Thread(target=ifvg_scanner.run_forever, kwargs={"send": send_telegram}, daemon=True).start()

المتغيرات (Railway Variables):
  ALPACAAPIKEY, ALPACASECRETKEY       مفاتيح ألباكا (موجودة عندك)
  TELEGRAM_TOKEN, TELEGRAM_CHAT_ID    تليجرام (TELEGRAM_CHAT_ID يقبل أكثر من رقم بينها فاصلة)
  IFVG_SYMBOLS        قائمة الأسهم مفصولة بفاصلة (اختياري)
  IFVG_TIMEFRAMES     الافتراضي: 1Hour,4Hour
  IFVG_FEED           الافتراضي: sip
"""
import json
import os
import time
from datetime import datetime, timedelta, timezone

import requests

# ------------------------------------------------------------------ الإعدادات
DEFAULT_SYMBOLS = (
    "LITE,MU,NVDA,AMD,AVGO,TSLA,AAPL,MSFT,META,AMZN,GOOGL,NFLX,PLTR,SMCI,"
    "COIN,MSTR,ARM,TSM,ANET,CRWD,SHOP,UBER,QQQ,SPY"
)
SYMBOLS = [s.strip().upper() for s in os.getenv("IFVG_SYMBOLS", DEFAULT_SYMBOLS).split(",") if s.strip()]
TIMEFRAMES = [t.strip() for t in os.getenv("IFVG_TIMEFRAMES", "1Hour,4Hour").split(",") if t.strip()]
FEED = os.getenv("IFVG_FEED", "sip")
DATA_DELAY_MIN = 16 if FEED == "sip" else 0       # بيانات SIP المجانية متأخرة 15 دقيقة
STATE_FILE = os.getenv("IFVG_STATE_FILE", "/data/ifvg_state.json" if os.path.isdir("/data") else "ifvg_state.json")

TF_MINUTES = {"1Hour": 60, "4Hour": 240}
TF_AR = {"1Hour": "ساعة", "4Hour": "4 ساعات"}
HISTORY_DAYS = {"1Hour": 25, "4Hour": 90}

PIVOT_LEFT = 3          # شموع يسار القاع/القمة
PIVOT_RIGHT = 2         # شموع يمين القاع/القمة
ATR_LEN = 14
MIN_GAP_ATR = 0.15      # أقل حجم للفجوة = 0.15 × ATR (يفلتر الفجوات التافهة)
FVG_MAX_AGE = 30        # أقدم فجوة نحسبها (بالشموع) قبل الانعكاس
SWEEP_WINDOW = 15       # السحب لازم يكون خلال آخر 15 شمعة قبل الانعكاس
RETEST_MAX_BARS = 20    # بعد الانعكاس، نراقب إعادة الاختبار لمدة 20 شمعة
ALERT_LOOKBACK = 3      # نرسل فقط لو الحدث صار بآخر 3 شموع مقفلة (ما نرسل قديم)
SCAN_EVERY_SEC = 300

ALPACA_URL = "https://data.alpaca.markets/v2/stocks/bars"


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
            r = requests.get(ALPACA_URL, headers=headers, params=params, timeout=30)
            r.raise_for_status()
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
    """قيعان وقمم مؤكدة: (index, price)"""
    lows, highs = [], []
    for i in range(PIVOT_LEFT, len(bars) - PIVOT_RIGHT):
        win = bars[i - PIVOT_LEFT:i + PIVOT_RIGHT + 1]
        if bars[i]["l"] == min(b["l"] for b in win):
            lows.append((i, bars[i]["l"]))
        if bars[i]["h"] == max(b["h"] for b in win):
            highs.append((i, bars[i]["h"]))
    return lows, highs


def _find_fvgs(bars, atr):
    """الفجوات: dict(kind, idx, bottom, top)   kind = 'bear' أو 'bull' (قبل الانعكاس)"""
    fvgs = []
    for i in range(2, len(bars)):
        a, c = bars[i - 2], bars[i]
        min_gap = MIN_GAP_ATR * atr[i]
        if c["h"] < a["l"] and (a["l"] - c["h"]) >= min_gap:
            fvgs.append({"kind": "bear", "idx": i, "bottom": c["h"], "top": a["l"]})
        if c["l"] > a["h"] and (c["l"] - a["h"]) >= min_gap:
            fvgs.append({"kind": "bull", "idx": i, "bottom": a["h"], "top": c["l"]})
    return fvgs


def _sweep(bars, piv, j, side):
    """هل صار سحب سيولة خلال SWEEP_WINDOW قبل الشمعة j؟ يرجع (sweep_idx, level) أو None"""
    lo = max(0, j - SWEEP_WINDOW)
    for k in range(j, lo - 1, -1):
        # القاع/القمة لازم يكون مؤكد قبل شمعة السحب
        cands = [(pi, pp) for pi, pp in piv if pi + PIVOT_RIGHT < k and k - pi <= 60]
        if not cands:
            continue
        if side == "long":
            level = cands[-1][1]
            if bars[k]["l"] < level:
                return k, level
        else:
            level = cands[-1][1]
            if bars[k]["h"] > level:
                return k, level
    return None


def detect(bars):
    """
    يرجع قائمة أحداث:
      {type: 'inversion'|'retest', side: 'long'|'short', zone:(bottom,top), fvg_idx, inv_idx, idx, sweep_level}
    """
    if len(bars) < 40:
        return []
    atr = _atr(bars)
    lows, highs = _pivots(bars)
    events = []
    n = len(bars)

    for f in _find_fvgs(bars, atr):
        side = "long" if f["kind"] == "bear" else "short"
        # أول شمعة تقفل خلف الفجوة كاملة = الانعكاس
        inv = None
        for j in range(f["idx"] + 1, min(n, f["idx"] + 1 + FVG_MAX_AGE)):
            c = bars[j]["c"]
            if side == "long" and c > f["top"]:
                inv = j
                break
            if side == "short" and c < f["bottom"]:
                inv = j
                break
            # لو الفجوة انعكست من الجهة الثانية (اتملت وكمل) نلغيها
        if inv is None:
            continue

        sw = _sweep(bars, lows if side == "long" else highs, inv, side)
        if not sw or sw[0] < f["idx"] - 5:
            continue  # لازم السحب يكون حول/بعد تكوين الفجوة

        zone = (round(f["bottom"], 2), round(f["top"], 2))
        base = {"side": side, "zone": zone, "fvg_idx": f["idx"], "inv_idx": inv, "sweep_level": round(sw[1], 2)}
        events.append({**base, "type": "inversion", "idx": inv})

        # إعادة الاختبار: يلمس المنطقة ويقفل لصالح الاتجاه
        for k in range(inv + 1, min(n, inv + 1 + RETEST_MAX_BARS)):
            b = bars[k]
            if side == "long":
                if b["c"] < f["bottom"]:
                    break  # فشل — قفل تحت المنطقة
                if b["l"] <= f["top"] and b["c"] >= f["top"]:
                    events.append({**base, "type": "retest", "idx": k})
                    break
            else:
                if b["c"] > f["top"]:
                    break
                if b["h"] >= f["bottom"] and b["c"] <= f["bottom"]:
                    events.append({**base, "type": "retest", "idx": k})
                    break
    return _merge(events)


def _merge(events):
    """يدمج الفجوات المتداخلة بنفس الاتجاه ونفس الحدث في منطقة وحدة (عشان ما يتكرر التنبيه)."""
    out = []
    for ev in sorted(events, key=lambda e: (e["type"], e["side"], e["zone"][0])):
        last = out[-1] if out else None
        if (last and last["type"] == ev["type"] and last["side"] == ev["side"]
                and abs(last["idx"] - ev["idx"]) <= 2 and ev["zone"][0] <= last["zone"][1]):
            last["zone"] = (min(last["zone"][0], ev["zone"][0]), max(last["zone"][1], ev["zone"][1]))
            last["idx"] = max(last["idx"], ev["idx"])
            last["fvg_idx"] = min(last["fvg_idx"], ev["fvg_idx"])
            continue
        out.append(dict(ev))
    return sorted(out, key=lambda e: e["idx"])


# ------------------------------------------------------------------ الرسالة
def _riyadh(ts):
    t = datetime.fromisoformat(ts.replace("Z", "+00:00")) + timedelta(hours=3)
    return t.strftime("%m-%d %H:%M")


def format_msg(sym, tf, ev, bars):
    b = bars[ev["idx"]]
    bot, top = ev["zone"]
    long_ = ev["side"] == "long"
    if ev["type"] == "inversion":
        head = "🟢 IFVG" if long_ else "🔴 IFVG"
        what = ("السعر قفل فوق فجوة هابطة بعد ما سحب السيولة تحت القاع — الفجوة انقلبت دعم"
                if long_ else
                "السعر قفل تحت فجوة صاعدة بعد ما سحب السيولة فوق القمة — الفجوة انقلبت مقاومة")
    else:
        head = "🟢 إعادة اختبار IFVG" if long_ else "🔴 إعادة اختبار IFVG"
        what = ("السعر رجع للمنطقة وثبت فوقها — المنطقة صمدت كدعم"
                if long_ else
                "السعر رجع للمنطقة وارتد تحتها — المنطقة صمدت كمقاومة")
    sweep_txt = f"كسر القاع {ev['sweep_level']}" if long_ else f"كسر القمة {ev['sweep_level']}"
    invalid = f"إغلاق تحت {bot}" if long_ else f"إغلاق فوق {top}"
    return (
        f"🤖 بوت سافونا — {head}\n"
        f"⚠️ محتوى تعليمي فقط، وليس توصية بيع أو شراء. القرار مسؤوليتك.\n\n"
        f"السهم: ${sym}\n"
        f"الفريم: {TF_AR.get(tf, tf)}\n"
        f"السعر: ${b['c']:.2f}\n"
        f"منطقة الـ IFVG: {bot} - {top}\n"
        f"سحب السيولة: {sweep_txt}\n"
        f"تلغى الفكرة عند: {invalid}\n"
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
    new = 0
    for tf in TIMEFRAMES:
        try:
            data = fetch_bars(SYMBOLS, tf)
        except Exception as e:
            print(f"IFVG {tf}: خطأ بالبيانات: {e}")
            continue
        for sym, bars in data.items():
            for ev in detect(bars):
                if ev["idx"] < len(bars) - ALERT_LOOKBACK:
                    continue
                key = f"{sym}|{tf}|{bars[ev['fvg_idx']]['t']}|{ev['side']}|{ev['type']}"
                if key in state:
                    continue
                send(format_msg(sym, tf, ev, bars))
                state[key] = int(time.time())
                new += 1
    _save_state(state)
    print(f"[{datetime.now(timezone.utc) + timedelta(hours=3):%H:%M}] الإنفيرجن جاب: خلص الفحص - {new} تنبيه جديد")
    return new


def run_forever(send=None):
    print(f"الإنفيرجن جاب: بدأ المراقبة — {len(SYMBOLS)} سهم على فريم {', '.join(TF_AR.get(t, t) for t in TIMEFRAMES)}")
    while True:
        try:
            scan_once(send)
        except Exception as e:
            print(f"IFVG: خطأ: {e}")
        time.sleep(SCAN_EVERY_SEC)


if __name__ == "__main__":
    run_forever()
