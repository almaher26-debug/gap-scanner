# -*- coding: utf-8 -*-
"""
قائمة IFVG الأسبوعية — فريم ساعة — بوت سافونا
-------------------------------------------
النموذج: فجوة هابطة (FVG) تنقلب بشمعة خضراء تقفل فوقها كاملة (IFVG)، في واحدة من الحالتين:
  أ) منطقة سيولة:
     1) 🟢 شمعة خضراء فيها فير فاليو جاب: قاع الشمعة اللي بعدها فوق قمة الشمعة اللي قبلها
     2) سحب سيولة: السعر ينزل ويكسر قاع سابق
     3) IFVG مقابل الشمعة الخضراء (نفس منطقتها السعرية)
  ب) عند دعم: منطقة الـ IFVG على/فوق قاع سابق صامد (ما انكسر بإغلاق)

الفلاتر:
  - أسهم ناسداك + نيويورك + أمكس، قيمة سوقية 10 مليار دولار وفوق (من سكرينر ناسداك)
  - شمعة الانعكاس لازم تكون خضراء (الإغلاق أعلى من الافتتاح)
  - فريم ساعة للجلسة الرسمية (9:30، 10:30 ... مثل تريدنج فيو)

الجدول:
  - كل جمعة بعد إغلاق السوق يرسل قائمة وحدة بكل الأسهم اللي سوت النموذج خلال الأسبوع
  - أول ما يشتغل، لو قائمة الأسبوع اللي فات ما انرسلت، يرسلها على طول

يشتغل من داخل gap_scanner.py (Thread)، أو لحاله:
  python -u weekly_ifvg.py          يشتغل دايم
  python -u weekly_ifvg.py --now    يرسل قائمة الأسبوع اللي فات الحين ويطلع
"""
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests

# ------------------------------------------------------------------ الإعدادات
FEED = os.getenv("WEEKLY_IFVG_FEED", "sip")
MIN_MCAP = float(os.getenv("WEEKLY_IFVG_MIN_MCAP", "10000000000"))  # 10 مليار دولار
MIN_PRICE = 3.0                 # نتجاهل الأسهم تحت 3$
HISTORY_DAYS = 21               # كم يوم نسحب (عشان القيعان والـ ATR)
EXCHANGES = {"NASDAQ", "NYSE", "AMEX"}

ATR_LEN = 14
MIN_GAP_ATR = 0.10              # أقل حجم للفجوة = 0.10 × ATR
PIVOT_LEFT, PIVOT_RIGHT = 3, 2  # تأكيد القاع
FVG_TO_INV_MAX = 60             # أقصى عدد شموع بين الشمعة الخضراء والانعكاس
INV_MAX_AGE = 30                # أقصى عمر للفجوة الهابطة قبل ما تنقلب
SUPPORT_LOOKBACK = 60           # نبحث عن الدعم في آخر 60 شمعة قبل الانعكاس
SUPPORT_ATR = 0.5               # الدعم داخل المنطقة أو تحتها بمسافة ≤ 0.5 × ATR

STATE_FILE = os.getenv("WEEKLY_IFVG_STATE", "/data/weekly_ifvg_state.json" if os.path.isdir("/data")
                       else "weekly_ifvg_state.json")
NY = ZoneInfo("America/New_York")
RIYADH = ZoneInfo("Asia/Riyadh")
DATA = "https://data.alpaca.markets/v2/stocks/bars"
REQ_GAP_SEC = 1.0               # بين كل طلب وطلب (عشان ما نزاحم باقي السكانرات على حد ألباكا)


def log(msg):
    print(f"[{datetime.now(RIYADH):%H:%M}] IFVG الأسبوعي: {msg}", flush=True)


def _headers():
    return {
        "APCA-API-KEY-ID": os.getenv("ALPACAAPIKEY") or os.getenv("ALPACA_API_KEY", ""),
        "APCA-API-SECRET-KEY": os.getenv("ALPACASECRETKEY") or os.getenv("ALPACA_SECRET_KEY", ""),
    }


def _get(url, params):
    for _ in range(5):
        r = requests.get(url, headers=_headers(), params=params, timeout=60)
        if r.status_code == 429:
            time.sleep(15)
            continue
        r.raise_for_status()
        time.sleep(REQ_GAP_SEC)
        return r.json()
    raise RuntimeError("ألباكا: طلبات كثيرة (429)")


# ------------------------------------------------------------------ البيانات
def universe():
    """{رمز: قيمة سوقية} من سكرينر ناسداك الرسمي (نفس مصدر باقي السكانرات) - مليار وفوق بس."""
    out = {}
    for ex in ("nasdaq", "nyse", "amex"):
        url = ("https://api.nasdaq.com/api/screener/stocks"
               f"?tableonly=true&limit=10000&exchange={ex}&download=true")
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"}, timeout=30)
            data = r.json().get("data") or {}
            rows = data.get("rows") or (data.get("table") or {}).get("rows") or []
            for row in rows:
                sym = str(row.get("symbol", "")).strip().upper()
                cap = _num(row.get("marketCap"))
                if sym.isalpha() and len(sym) <= 5 and cap >= MIN_MCAP:
                    out[sym] = cap
        except Exception as e:
            log(f"ما قدرت أجيب أسهم {ex.upper()}: {e}")
    return out


def _num(x):
    try:
        return float(str(x).replace("$", "").replace(",", "").strip())
    except Exception:
        return 0.0


def fetch_hourly(symbols, start, end):
    """شموع ساعة للجلسة الرسمية (9:30-16:00 نيويورك) مبنية من شموع نص ساعة."""
    raw = {}
    for i in range(0, len(symbols), 100):
        params = {"symbols": ",".join(symbols[i:i + 100]), "timeframe": "30Min",
                  "start": start.isoformat().replace("+00:00", "Z"),
                  "end": end.isoformat().replace("+00:00", "Z"),
                  "limit": 10000, "adjustment": "split", "feed": FEED, "sort": "asc"}
        while True:
            try:
                js = _get(DATA, params)
            except Exception as e:
                log(f"خطأ بدفعة {i}: {e}")
                break
            for s, b in (js.get("bars") or {}).items():
                raw.setdefault(s, []).extend(b)
            tok = js.get("next_page_token")
            if not tok:
                break
            params["page_token"] = tok
    return {s: to_session_hours(b) for s, b in raw.items()}


def to_session_hours(bars30):
    out, cur, key = [], None, None
    for b in bars30:
        t = datetime.fromisoformat(b["t"].replace("Z", "+00:00")).astimezone(NY)
        mins = t.hour * 60 + t.minute
        if not (570 <= mins < 960):          # برا الجلسة الرسمية
            continue
        k = (t.date(), (mins - 570) // 60)   # 9:30، 10:30، ... 15:30
        if k != key:
            if cur:
                out.append(cur)
            key = k
            cur = {"t": t, "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"]}
        else:
            cur["h"] = max(cur["h"], b["h"])
            cur["l"] = min(cur["l"], b["l"])
            cur["c"] = b["c"]
    if cur:
        out.append(cur)
    return out


# ------------------------------------------------------------------ النموذج
def _atr(bars):
    out, prev, val = [], None, None
    for b in bars:
        tr = b["h"] - b["l"] if prev is None else max(b["h"] - b["l"], abs(b["h"] - prev), abs(b["l"] - prev))
        val = tr if val is None else (val * (ATR_LEN - 1) + tr) / ATR_LEN
        out.append(val)
        prev = b["c"]
    return out


def _pivot_lows(bars):
    piv = []
    for i in range(PIVOT_LEFT, len(bars) - PIVOT_RIGHT):
        if bars[i]["l"] == min(b["l"] for b in bars[i - PIVOT_LEFT:i + PIVOT_RIGHT + 1]):
            piv.append((i, bars[i]["l"]))
    return piv


def _liquidity(bars, atr, piv, f, inv, z_lo, z_hi):
    """الحالة أ: شمعة خضراء فيها FVG قبل الفجوة الهابطة ومقابلها، وسحب سيولة بينها وبين الانعكاس.
       يرجع مستوى القاع المكسور أو None."""
    for k in range(f - 3, max(1, inv - FVG_TO_INV_MAX) - 1, -1):
        a, g, c = bars[k - 2], bars[k - 1], bars[k]
        if not (g["c"] > g["o"] and c["l"] > a["h"] and c["l"] - a["h"] >= MIN_GAP_ATR * atr[k]):
            continue
        if z_hi < g["l"] or z_lo > g["h"]:     # لازم تكون بنفس منطقة الشمعة الخضراء
            continue
        sweep = None
        for s in range(k + 1, inv + 1):
            cands = [p for p in piv if p[0] >= k - 10 and p[0] + PIVOT_RIGHT < s]
            if cands and bars[s]["l"] < cands[-1][1]:
                sweep = cands[-1][1]
        if sweep is not None:
            return sweep
    return None


def _support(bars, atr, piv, inv, z_lo, z_hi):
    """الحالة ب: قاع سابق مؤكد قبل الانعكاس، داخل المنطقة أو تحتها بشوي، وما انكسر بإغلاق.
       يرجع مستوى الدعم (الأقرب للمنطقة) أو None."""
    best = None
    for pi, pp in piv:
        if pi + PIVOT_RIGHT >= inv or inv - pi > SUPPORT_LOOKBACK:
            continue
        if not (z_lo - SUPPORT_ATR * atr[inv] <= pp <= z_hi):
            continue
        if any(bars[j]["c"] < pp for j in range(pi + 1, inv + 1)):
            continue
        if best is None or pp > best:
            best = pp
    return best


def detect(bars, win_start, win_end):
    """يرجع آخر حدث بالأسبوع أو None:
       {inv_idx, zone, reason ('sweep'|'support'), level, close, t}"""
    n = len(bars)
    if n < 30:
        return None
    atr = _atr(bars)
    piv = _pivot_lows(bars)
    found = None

    for f in range(2, n):
        fa, fc = bars[f - 2], bars[f]
        # فجوة هابطة
        if not (fc["h"] < fa["l"] and fa["l"] - fc["h"] >= MIN_GAP_ATR * atr[f]):
            continue
        z_lo, z_hi = fc["h"], fa["l"]
        # الانعكاس: أول شمعة تقفل فوق الفجوة كاملة، ولازم تكون خضراء
        inv = next((j for j in range(f + 1, min(n, f + 1 + INV_MAX_AGE)) if bars[j]["c"] > z_hi), None)
        if inv is None or bars[inv]["c"] <= bars[inv]["o"]:
            continue
        t = bars[inv]["t"]
        if not (win_start <= t <= win_end):
            continue
        if found is not None and inv <= found["inv_idx"]:
            continue

        level = _liquidity(bars, atr, piv, f, inv, z_lo, z_hi)
        reason = "sweep"
        if level is None:
            level = _support(bars, atr, piv, inv, z_lo, z_hi)
            reason = "support"
        if level is None:
            continue

        found = {"inv_idx": inv, "zone": (round(z_lo, 2), round(z_hi, 2)), "reason": reason,
                 "level": round(level, 2), "close": round(bars[inv]["c"], 2), "t": t}
    return found


# ------------------------------------------------------------------ الأسبوع والرسالة
def week_window(friday):
    mon = friday - timedelta(days=4)
    start = datetime(mon.year, mon.month, mon.day, 0, 0, tzinfo=NY)
    end = datetime(friday.year, friday.month, friday.day, 20, 0, tzinfo=NY)
    return start, end


def last_finished_friday(now_ny=None):
    """آخر جمعة سكّر سوقها (بعد 4:30 العصر نيويورك)."""
    now = now_ny or datetime.now(NY)
    d = now.date()
    while d.weekday() != 4:
        d -= timedelta(days=1)
    if d == now.date() and now.hour * 60 + now.minute < 16 * 60 + 30:
        d -= timedelta(days=7)
    return d


def _fmt_cap(v):
    return f"{v / 1e12:.2f}T" if v >= 1e12 else f"{v / 1e9:.1f}B"


def build_messages(friday, rows):
    start, _ = week_window(friday)
    head = (f"📋 قائمة IFVG الأسبوعية — فريم ساعة\n"
            f"الأسبوع: {start:%m-%d} ← {friday:%m-%d}\n"
            f"النموذج: IFVG بشمعة خضراء — في منطقة سيولة أو عند دعم\n"
            f"الأسهم (قيمة سوقية {_fmt_cap(MIN_MCAP)} وفوق): {len(rows)}\n")
    if not rows:
        return [head + "\nما فيه أسهم سوت النموذج هالأسبوع."]
    lines = []
    for i, (sym, cap, ev) in enumerate(rows, 1):
        where = (f"سحب السيولة: {ev['level']}" if ev["reason"] == "sweep"
                 else f"عند دعم: {ev['level']}")
        lines.append(f"{i}) 🟢 ${sym} ({_fmt_cap(cap)})\n"
                     f"   IFVG: {ev['zone'][0]} - {ev['zone'][1]} | {where}\n"
                     f"   الإغلاق: {ev['close']} | {ev['t'].astimezone(RIYADH):%m-%d %H:%M} (توقيتك)")
    msgs, cur = [], head + "\n"
    for ln in lines:
        if len(cur) + len(ln) > 3500:
            msgs.append(cur)
            cur = "(تكملة القائمة)\n\n"
        cur += ln + "\n"
    msgs.append(cur)
    return msgs


def weekly_report(friday, send):
    win_start, win_end = week_window(friday)
    log(f"أفحص أسبوع {win_start:%m-%d} ← {friday:%m-%d}")
    caps = universe()
    if len(caps) < 50:
        raise RuntimeError(f"قائمة الأسهم من ناسداك رجعت {len(caps)} بس - بعيد المحاولة بعد شوي")
    syms = sorted(caps)
    log(f"{len(syms)} سهم ({_fmt_cap(MIN_MCAP)} وفوق)، أسحب الشموع...")
    data = fetch_hourly(syms, win_start - timedelta(days=HISTORY_DAYS - 5),
                        min(win_end, datetime.now(timezone.utc) - timedelta(minutes=16)))
    hits = {}
    for s, bars in data.items():
        if not bars or bars[-1]["c"] < MIN_PRICE:
            continue
        ev = detect(bars, win_start, win_end)
        if ev:
            hits[s] = ev
    rows = sorted(((s, caps[s], ev) for s, ev in hits.items()), key=lambda r: -r[1])
    log(f"{len(rows)} سهم سوى النموذج")
    for m in build_messages(friday, rows):
        send(m)
    return len(rows)


# ------------------------------------------------------------------ التشغيل
def _default_send(text):
    token = os.getenv("TELEGRAM_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN", "")
    text += "\n\n⚠️ محتوى تعليمي فقط، وليس توصية بيع أو شراء. القرار مسؤوليتك."
    for chat in [c.strip() for c in os.getenv("TELEGRAM_CHAT_ID", "").split(",") if c.strip()]:
        try:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          data={"chat_id": chat, "text": text}, timeout=15)
        except Exception as e:
            log(f"ما قدرت أرسل لـ {chat}: {e}")


def _load_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_state(st):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(st, f)
    except Exception as e:
        log(f"ما قدرت أحفظ الحالة: {e}")


def run_forever(send=None):
    send = send or _default_send
    log("بدأ — يرسل القائمة كل جمعة بعد الإغلاق")
    while True:
        try:
            fri = last_finished_friday().isoformat()
            st = _load_state()
            if st.get("last_week") != fri:
                weekly_report(datetime.fromisoformat(fri).date(), send)
                st["last_week"] = fri
                _save_state(st)
        except Exception as e:
            log(f"خطأ: {e}")
        time.sleep(600)


if __name__ == "__main__":
    if "--now" in sys.argv:
        weekly_report(last_finished_friday(), _default_send)
    else:
        run_forever()
