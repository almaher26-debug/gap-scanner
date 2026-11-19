# ===== سكنر القاما (Gamma scanner) =====
# نفس قالب gap_scanner: يشتغل على Railway ويرسل على تيليجرام
# التشغيل: python gamma_scanner.py   (المتغيرات: TELEGRAM_TOKEN + TELEGRAM_CHAT_ID)
"""
سكنر تمركز الصانع (القاما) - AAPL TSLA META MSFT NVDA AMD
=========================================================

(1) تنبيه أول ما يشتغل البوت (أول تنبيه اليوم)
    - لو تقرير اليوم ما انرسل، يرسله فوراً ويسجل اليوم عشان ما يتكرر مع إعادة التشغيل
    - START_ID: غيّر الرقم لو تبي يعيد الإرسال بعد الرفع الجاي حتى لو انرسل اليوم

(2) التقرير اليومي - كل يوم سوق 8:30 الصبح نيويورك (4:30 العصر الرياض بالشتاء / 3:30 بالصيف)
    - رسالة ملخص: ترتيب الأسهم الست حسب سيولة الصانع (صافي القاما)
    - لكل سهم: صورة شارت السترايكات (قاما الكول والبوت لكل سترايك) + تحتها:
        سيولة الصانع: صافي القاما، قاما الكول، قاما البوت، العقود المفتوحة وقيمتها، نسبة البوت/الكول
        أقوى تمركز: السترايك اللي عليه أكبر قاما (والثاني والثالث)
        جدار الكول (مقاومة)، جدار البوت (دعم)، نقطة الانقلاب
        أكثر سترايك عقود مفتوحة، أكثر سترايك فوليوم

الحساب (نفس gap_scanner):
    قاما كل عقد (بلاك شولز) × العقود المفتوحة × 100 × السعر² × 1%  = دولار لكل 1% حركة
    الكول موجب والبوت سالب (افتراض: الصانع شاري كول وبايع بوت)
    أقرب 4 انتهاءات خلال 30 يوم، والسترايكات داخل ±20% من السعر - من سلسلة عقود ياهو

التشغيل:
  pip install yfinance pandas requests matplotlib
  python gamma_scanner.py                    # يشتغل باستمرار (تنبيه الحين + كل يوم)
  python gamma_scanner.py --now              # يطبع التقرير بالشاشة (بيانات حقيقية) ويحفظ الصور
  python gamma_scanner.py --now --send       # يرسله لتيليجرام الحين
  python gamma_scanner.py --now NVDA AMD     # أسهم معينة
  python gamma_scanner.py --test             # تجربة بدون نت (سلسلة وهمية)
"""

import gc
import io
import math
import os
import sys
import time
from datetime import datetime, timedelta

import pandas as pd
import requests

# ================== الإعدادات ==================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "ضع_توكن_البوت_هنا")      # من @BotFather
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "ضع_رقم_المحادثة_هنا")  # من @userinfobot (أكثر من رقم بينهم فاصلة)
AUTO_ADD_GROUPS = True           # أي قروب أو قناة تضيف لها البوت يلقط رقمها لحاله
DATA_DIR = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH", ".")
CHATS_FILE = os.path.join(DATA_DIR, "gamma_chats.txt")

NY = "America/New_York"
LOCAL_TZ = "Asia/Riyadh"
LOOP_SLEEP_SEC = 30

# الأسهم: أو متغير GAMMA_SYMBOLS في Railway (بينها فاصلة)
SYMBOLS = [s.strip().upper() for s in os.environ.get("GAMMA_SYMBOLS", "").split(",") if s.strip()] or [
    "AAPL", "TSLA", "META", "MSFT", "NVDA", "AMD",
]

SEND_ON_START = True             # True = يرسل التقرير أول ما يشتغل (لو ما انرسل اليوم)
START_ID = "1"                   # غيّر الرقم عشان يعيد الإرسال بعد الرفع حتى لو انرسل اليوم
DAILY_AT_NY = (8, 30)            # التقرير اليومي من 8:30 الصبح نيويورك
DAILY_UNTIL_NY = (16, 0)         # لو البوت اشتغل بعد كذا وما انرسل، ينتظر لليوم الجاي
STATE_FILE = os.path.join(DATA_DIR, "gamma_scanner_state.txt")

GAMMA_MAX_DTE = 30               # الانتهاءات من اليوم إلى كذا يوم
GAMMA_MAX_EXPS = 4               # أقصى عدد انتهاءات (أقربها)
GAMMA_RANGE_PCT = 20             # السترايكات داخل ±كذا % من السعر
GAMMA_TOP_N = 3                  # كم سترايك في "أقوى تمركز"
RATE = 0.04                      # الفائدة لحساب القاما

SEND_CHART = True                # صورة شارت السترايكات مع كل سهم (يحتاج matplotlib)
CHART_RANGE_PCT = 12             # الشارت يعرض السترايكات داخل ±كذا % من السعر (أوضح)
CHART_MAX_STRIKES = 40           # أقصى عدد سترايكات بالشارت (الأقرب للسعر)

ADD_DISCLAIMER = True
DISCLAIMER = "⚠️ محتوى تعليمي فقط، وليس توصية بيع أو شراء."
HEADERS = {"User-Agent": "Mozilla/5.0"}
# ===============================================


def log(*a):
    print(*a, flush=True)


# ================== تيليجرام ==================
TG_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
CHATS = set()
_last_update_id = 0


def _no_token():
    return "ضع_" in TELEGRAM_TOKEN


def _load_chats():
    for c in TELEGRAM_CHAT_ID.split(","):
        c = c.strip()
        if c and "ضع_" not in c:
            CHATS.add(c)
    try:
        with open(CHATS_FILE, encoding="utf-8") as f:
            CHATS.update(x.strip() for x in f if x.strip())
    except FileNotFoundError:
        pass


def _save_chat(cid):
    try:
        with open(CHATS_FILE, "a", encoding="utf-8") as f:
            f.write(cid + "\n")
    except Exception:
        pass


def discover_groups():
    """يلقط القروبات/القنوات اللي انضاف لها البوت."""
    global _last_update_id
    if not AUTO_ADD_GROUPS or _no_token():
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
        status = ((u.get("my_chat_member") or {}).get("new_chat_member") or {}).get("status")
        if status in ("left", "kicked"):
            CHATS.discard(cid)
            continue
        new_id = (u.get("message") or {}).get("migrate_to_chat_id")
        if new_id:
            CHATS.discard(cid)
            cid = str(new_id)
        if cid not in CHATS:
            CHATS.add(cid)
            _save_chat(cid)
            log(f"✅ انضاف قروب/قناة: {chat.get('title', '')}  الرقم: {cid}")
            _send_one(cid, "✅ سكنر القاما متصل هنا وبيرسل التنبيهات")


def _send_one(chat_id, text):
    try:
        r = requests.post(f"{TG_API}/sendMessage",
                          data={"chat_id": chat_id, "text": text, "disable_web_page_preview": True},
                          timeout=15).json()
        if not r.get("ok"):
            log(f"فشل الإرسال لـ {chat_id}: {r.get('description')}")
    except Exception as e:
        log(f"فشل الإرسال لـ {chat_id}:", e)


def _send_photo_one(chat_id, png, caption=None):
    try:
        data = {"chat_id": chat_id}
        if caption:
            data["caption"] = caption
        r = requests.post(f"{TG_API}/sendPhoto", data=data,
                          files={"photo": ("gamma.png", png, "image/png")}, timeout=40).json()
        if not r.get("ok"):
            log(f"فشل إرسال الصورة لـ {chat_id}: {r.get('description')}")
            return False
        return True
    except Exception as e:
        log(f"فشل إرسال الصورة لـ {chat_id}:", e)
        return False


def send_telegram(text, photo=None, disclaimer=True):
    if disclaimer and ADD_DISCLAIMER and "ليست توصية" not in text:
        text += "\n\n" + DISCLAIMER
    log(text)
    if _no_token():
        return                                   # بدون توكن: يطبع بالشاشة بس
    fits = len(text.encode("utf-16-le")) // 2 <= 1024   # حد النص تحت الصورة
    for cid in list(CHATS):
        if photo and fits and _send_photo_one(cid, photo, text):
            continue
        if photo:
            _send_photo_one(cid, photo)
        _send_one(cid, text)


# ================== القاما ==================
def _years(exp):
    end = pd.Timestamp(exp).tz_localize(NY) + pd.Timedelta(hours=16)
    return max((end - pd.Timestamp.now(tz=NY)).total_seconds(), 60) / (365 * 24 * 3600)


def _bs_gamma(spot, strike, years, iv):
    if not (spot and strike and years > 0 and iv and iv > 0.01):
        return 0.0
    sq = iv * math.sqrt(years)
    d1 = (math.log(spot / strike) + (RATE + iv * iv / 2) * years) / sq
    return math.exp(-d1 * d1 / 2) / math.sqrt(2 * math.pi) / (spot * sq)


def get_spot(t):
    import yfinance as yf
    tk = yf.Ticker(t)
    try:
        p = tk.fast_info.get("last_price") or tk.fast_info.get("lastPrice")
        if p:
            return float(p)
    except Exception:
        pass
    h = tk.history(period="5d", interval="1d")
    return float(h["Close"].dropna().iloc[-1])


def get_chain(t):
    """[(سترايك، انتهاء، IV، مفتوحة، كول؟، فوليوم)] لأقرب الانتهاءات، والانتهاءات."""
    import yfinance as yf
    tk = yf.Ticker(t)
    today = pd.Timestamp.now(tz=NY).date()
    last = today + timedelta(days=GAMMA_MAX_DTE)
    exps = sorted(e for e in (tk.options or []) if today <= pd.Timestamp(e).date() <= last)[:GAMMA_MAX_EXPS]
    raw = []
    for e in exps:
        ch = tk.option_chain(e)
        exp = pd.Timestamp(e).date()
        for df, is_call in ((ch.calls, True), (ch.puts, False)):
            for x in df.itertuples():
                oi = 0 if pd.isna(x.openInterest) else int(x.openInterest)
                if oi <= 0:
                    continue
                iv = 0 if pd.isna(x.impliedVolatility) else float(x.impliedVolatility)
                vol = 0 if pd.isna(x.volume) else int(x.volume)
                raw.append((float(x.strike), exp, iv, oi, is_call, vol))
    # قبل الافتتاح ياهو يرجع IV قريب من الصفر: نعوضها بوسيط IV لنفس الانتهاء، وإلا وسيط الكل
    good = [r for r in raw if r[2] > 0.01]
    all_ivs = sorted(r[2] for r in good)
    med_all = all_ivs[len(all_ivs) // 2] if all_ivs else 0.4
    med = {}
    for e in {r[1] for r in raw}:
        ivs = sorted(r[2] for r in good if r[1] == e)
        med[e] = ivs[len(ivs) // 2] if ivs else med_all
    chain = [(k, e, iv if iv > 0.01 else med[e], oi, c, v) for k, e, iv, oi, c, v in raw]
    return chain, exps


def _gex_at(rows, s):
    tot = 0.0
    for k, yrs, iv, oi, is_call, _ in rows:
        g = _bs_gamma(s, k, yrs, iv) * oi * 100 * s * s * 0.01
        tot += g if is_call else -g
    return tot


def gamma_levels(chain, exps, spot):
    """كل أرقام السهم من سلسلة العقود، أو None."""
    lo, hi = spot * (1 - GAMMA_RANGE_PCT / 100), spot * (1 + GAMMA_RANGE_PCT / 100)
    yrs = {e: _years(e) for e in {x[1] for x in chain}}
    rows = [(k, yrs[e], iv, oi, c, v) for k, e, iv, oi, c, v in chain if lo <= k <= hi]
    if not rows:
        return None
    calls, puts, oi_k, vol_k = {}, {}, {}, {}
    call_oi = put_oi = 0
    for k, y, iv, oi, is_call, vol in rows:
        g = _bs_gamma(spot, k, y, iv) * oi * 100 * spot * spot * 0.01
        d = calls if is_call else puts
        d[k] = d.get(k, 0.0) + g
        o = oi_k.setdefault(k, [0, 0])
        o[0 if is_call else 1] += oi
        vol_k[k] = vol_k.get(k, 0) + (vol or 0)
        if is_call:
            call_oi += oi
        else:
            put_oi += oi
    strikes = sorted(set(calls) | set(puts))
    net = {k: calls.get(k, 0.0) - puts.get(k, 0.0) for k in strikes}      # صافي كل سترايك
    gross = {k: calls.get(k, 0.0) + puts.get(k, 0.0) for k in strikes}    # التمركز الكلي
    grid = [spot * (1 + i / 200) for i in range(-30, 31)]                  # ±15% بخطوة 0.5%
    vals = [_gex_at(rows, s) for s in grid]
    flips = [(grid[i] + grid[i + 1]) / 2 for i in range(len(grid) - 1) if (vals[i] < 0) != (vals[i + 1] < 0)]
    ko = max(oi_k, key=lambda k: sum(oi_k[k]))
    kv = max(vol_k, key=vol_k.get) if max(vol_k.values()) > 0 else None
    return {
        "spot": spot, "exps": exps, "calls": calls, "puts": puts, "net_k": net, "gross": gross,
        "call_wall": max(calls, key=calls.get) if calls else None,
        "put_wall": max(puts, key=puts.get) if puts else None,
        "top": sorted(gross, key=gross.get, reverse=True)[:GAMMA_TOP_N],
        "net": _gex_at(rows, spot),
        "call_gex": sum(calls.values()), "put_gex": sum(puts.values()),
        "call_oi": call_oi, "put_oi": put_oi,
        "oi_value": (call_oi + put_oi) * 100 * spot,
        "flip": min(flips, key=lambda x: abs(x - spot)) if flips else None,
        "oi_top": (ko, oi_k[ko][0], oi_k[ko][1]),
        "vol_top": (kv, vol_k[kv]) if kv is not None else None,
    }


# ================== الرسائل ==================
def _usd(v):
    a, s = abs(v), "-" if v < 0 else ""
    if a >= 1e9:
        return f"{s}{a / 1e9:.2f}B$"
    if a >= 1e6:
        return f"{s}{a / 1e6:.1f}M$"
    if a >= 1e3:
        return f"{s}{a / 1e3:.0f}K$"
    return f"{s}{a:.0f}$"


def _n(v):
    return f"{v / 1e6:.2f}M" if v >= 1e6 else f"{v / 1e3:.1f}K" if v >= 1e3 else f"{v:.0f}"


def stock_message(t, lv):
    spot = lv["spot"]
    pct = lambda k: f"{(k / spot - 1) * 100:+.1f}%"
    net = lv["net"]
    pcr = lv["put_oi"] / lv["call_oi"] if lv["call_oi"] else 0
    L = [f"🧲 ${t} — {spot:.2f}",
         f"الانتهاءات: {', '.join(pd.Timestamp(e).strftime('%m-%d') for e in lv['exps'])}",
         "",
         "💰 سيولة الصانع:",
         f"صافي القاما: {_usd(net)} لكل 1% {'🟢' if net >= 0 else '🔴'}",
         f"قاما الكول: {_usd(lv['call_gex'])} | قاما البوت: {_usd(-lv['put_gex'])}",
         f"العقود المفتوحة: {_n(lv['call_oi'] + lv['put_oi'])} (قيمتها {_usd(lv['oi_value'])})",
         f"بوت/كول: {pcr:.2f}",
         "",
         "🎯 أقوى تمركز:"]
    for i, k in enumerate(lv["top"], 1):
        side = "كول" if lv["calls"].get(k, 0) >= lv["puts"].get(k, 0) else "بوت"
        L.append(f"{i}) {k:g} ({pct(k)}) — {_usd(lv['gross'][k])} غالبه {side}")
    L.append("")
    if lv["call_wall"] is not None:
        k = lv["call_wall"]
        L.append(f"🟩 جدار الكول (مقاومة): {k:g} ({pct(k)})")
    if lv["put_wall"] is not None:
        k = lv["put_wall"]
        L.append(f"🟥 جدار البوت (دعم): {k:g} ({pct(k)})")
    if lv["flip"] is not None:
        f = lv["flip"]
        L.append(f"🔁 الانقلاب: {f:.2f} ({pct(f)}) — السعر {'فوقه' if spot > f else 'تحته'}")
    k, c, p = lv["oi_top"]
    L.append(f"📌 أكثر عقود مفتوحة: {k:g} ({_n(c)} كول / {_n(p)} بوت)")
    if lv["vol_top"]:
        k, v = lv["vol_top"]
        L.append(f"🔥 أكثر فوليوم: {k:g} ({_n(v)})")
    L.append("")
    L.append("موجب = حركة أهدى والسعر ينشد للسترايكات الكبيرة" if net >= 0
             else "سالب = الصانع يطارد السعر، الحركة أقوى وأسرع")
    return "\n".join(L)


def summary_message(results, miss, prefix=""):
    now = pd.Timestamp.now(tz=LOCAL_TZ)
    L = [f"{prefix}🧲 سكنر تمركز الصانع — {now:%Y-%m-%d %H:%M} (توقيتك)",
         f"أقرب {GAMMA_MAX_EXPS} انتهاءات، السترايكات ±{GAMMA_RANGE_PCT}% من السعر",
         "",
         "ترتيب سيولة الصانع (صافي القاما لكل 1%):"]
    for i, (t, lv) in enumerate(sorted(results, key=lambda x: -x[1]["net"]), 1):
        k = lv["top"][0]
        L.append(f"{i}) ${t} {lv['spot']:.2f} | {_usd(lv['net'])} {'🟢' if lv['net'] >= 0 else '🔴'}"
                 f" | أقوى تمركز {k:g}")
    if miss:
        L.append("")
        L.append("ما فيه بيانات عقود: " + " ".join(miss))
    L.append("")
    L.append("🟢 موجب = حركة أهدى | 🔴 سالب = حركة أقوى وأسرع")
    return "\n".join(L)


# ================== الشارت ==================
def strike_chart(t, lv):
    """شارت السترايكات: قاما الكول (أخضر يمين) والبوت (أحمر يسار) لكل سترايك + الصافي + السعر والمستويات."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    spot = lv["spot"]
    ks = [k for k in sorted(lv["gross"]) if abs(k / spot - 1) * 100 <= CHART_RANGE_PCT]
    if len(ks) > CHART_MAX_STRIKES:
        ks = sorted(sorted(ks, key=lambda k: abs(k - spot))[:CHART_MAX_STRIKES])
    if not ks:
        return None
    c = [lv["calls"].get(k, 0) / 1e6 for k in ks]
    p = [-lv["puts"].get(k, 0) / 1e6 for k in ks]
    n = [lv["net_k"].get(k, 0) / 1e6 for k in ks]
    y = list(range(len(ks)))

    def ypos(price):                                   # مكان سعر بين السترايكات
        if price <= ks[0]:
            return 0
        if price >= ks[-1]:
            return len(ks) - 1
        for i in range(len(ks) - 1):
            if ks[i] <= price <= ks[i + 1]:
                return i + (price - ks[i]) / (ks[i + 1] - ks[i])
        return 0

    bg, fg, grid = "#0f1419", "#d7dde3", "#26313b"
    fig, ax = plt.subplots(figsize=(8, max(6, len(ks) * 0.28)), dpi=130)
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    ax.barh(y, c, color="#22c55e", height=0.75, label="Call GEX")
    ax.barh(y, p, color="#ef4444", height=0.75, label="Put GEX")
    ax.scatter(n, y, color="#facc15", s=14, zorder=3, label="Net GEX")
    ax.axvline(0, color="#5b6670", lw=0.8)

    def hline(price, color, text, style="-"):
        yy = ypos(price)
        ax.axhline(yy, color=color, ls=style, lw=1.3)
        ax.text(ax.get_xlim()[1], yy, f" {text} {price:.2f}", color=color, va="center", ha="left", fontsize=8)

    ax.set_yticks(y)
    ax.set_yticklabels([f"{k:g}" for k in ks], fontsize=7, color=fg)
    ax.tick_params(axis="x", colors=fg, labelsize=8)
    for s in ax.spines.values():
        s.set_color(grid)
    ax.set_axisbelow(True)
    ax.grid(axis="x", color=grid, lw=0.6)
    ax.set_xlabel("Gamma exposure ($M per 1% move)", color=fg, fontsize=9)
    hline(spot, "#38bdf8", "Spot")
    if lv["flip"] is not None and ks[0] <= lv["flip"] <= ks[-1]:
        hline(lv["flip"], "#f59e0b", "Flip", "--")
    if lv["call_wall"] in ks:
        hline(lv["call_wall"], "#22c55e", "Call wall", ":")
    if lv["put_wall"] in ks:
        hline(lv["put_wall"], "#ef4444", "Put wall", ":")
    top = lv["top"][0]
    if top in ks:
        ax.annotate("Strongest", xy=(max(c[ks.index(top)], 0), ks.index(top)), xytext=(6, 0),
                    textcoords="offset points", color="#facc15", fontsize=8, va="center")
    exps = ", ".join(pd.Timestamp(e).strftime("%m-%d") for e in lv["exps"])
    title = f"${t}  {spot:.2f}  |  Net GEX {_usd(lv['net'])}  |  exp {exps}"
    ax.set_title(title.replace("$", r"\$"), color=fg, fontsize=10, loc="left")
    leg = ax.legend(loc="lower right", fontsize=7, facecolor=bg, edgecolor=grid)
    for tx in leg.get_texts():
        tx.set_color(fg)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=bg, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


# ================== التقرير ==================
def scan(symbols):
    results, miss = [], []
    for t in symbols:
        try:
            spot = get_spot(t)
            chain, exps = get_chain(t)
            lv = gamma_levels(chain, exps, spot) if chain else None
        except Exception as e:
            log(f"{t}: {e}")
            lv = None
        if lv:
            results.append((t, lv))
        else:
            miss.append(t)
        time.sleep(1)
    gc.collect()
    return results, miss


def send_report(symbols, prefix="", send=True, save_dir=None):
    t0 = time.time()
    results, miss = scan(symbols)
    out = send_telegram if send else (lambda txt, photo=None, disclaimer=True: log(txt))
    out(summary_message(results, miss, prefix), disclaimer=False)
    for t, lv in results:
        png = None
        if SEND_CHART:
            try:
                png = strike_chart(t, lv)
            except Exception as e:
                log(f"شارت {t}: {e}")
        if png and save_dir:
            with open(os.path.join(save_dir, f"gamma_{t}.png"), "wb") as f:
                f.write(png)
        out(stock_message(t, lv), photo=png)
        time.sleep(1)
    log(f"[{datetime.now():%H:%M}] التقرير: {len(results)} سهم، {len(miss)} بدون بيانات — {time.time() - t0:.0f} ثانية")


# ================== الجدولة ==================
def _state():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            d = dict(x.strip().split("=", 1) for x in f if "=" in x)
            return d
    except FileNotFoundError:
        return {}


def _save_state(st):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            f.writelines(f"{k}={v}\n" for k, v in st.items())
    except Exception as e:
        log(f"ما قدرت أحفظ الحالة: {e}")


def maybe_send(first=False):
    st = _state()
    now = pd.Timestamp.now(tz=NY)
    day = str(now.date())
    if first and SEND_ON_START and (st.get("day") != day or st.get("start_id") != START_ID):
        st.update(day=day, start_id=START_ID)
        _save_state(st)                                  # يتسجل قبل الإرسال عشان ما يتكرر
        send_report(SYMBOLS, prefix="🚀 أول تنبيه اليوم\n")
        return
    if now.weekday() >= 5 or not (DAILY_AT_NY <= (now.hour, now.minute) < DAILY_UNTIL_NY):
        return
    if st.get("day") == day:
        return
    st["day"] = day
    _save_state(st)
    send_report(SYMBOLS)


# ================== تجربة بدون نت ==================
def self_test():
    exp = (pd.Timestamp.now(tz=NY) + pd.Timedelta(days=7)).date()
    fake = [(95, exp, 0.4, 9000, False, 1200), (100, exp, 0.4, 20000, False, 3000),
            (100, exp, 0.4, 15000, True, 8000), (105, exp, 0.4, 25000, True, 4000),
            (110, exp, 0.4, 6000, True, 900), (90, exp, 0.4, 3000, False, 100),
            (97.5, exp, 0.4, 4000, False, 500), (102.5, exp, 0.4, 7000, True, 2500)]
    lv = gamma_levels(fake, [exp.isoformat()], 101.0)
    assert lv["call_wall"] == 105 and lv["put_wall"] == 100, lv
    assert lv["oi_top"] == (100, 15000, 20000), lv
    print(summary_message([("TEST", lv)], []))
    print("\n" + stock_message("TEST", lv))
    png = strike_chart("TEST", lv)
    with open("gamma_TEST.png", "wb") as f:
        f.write(png)
    print(f"\nالشارت: gamma_TEST.png ({len(png) // 1024} KB)")
    print("GAMMA TEST OK")


def main():
    if "--test" in sys.argv:
        self_test()
        return
    if "--now" in sys.argv:
        _load_chats()
        syms = [a.upper() for a in sys.argv[1:] if not a.startswith("--")] or SYMBOLS
        send_report(syms, prefix="🧪 تجربة\n", send="--send" in sys.argv, save_dir=".")
        return
    _load_chats()
    discover_groups()
    log(f"سكنر القاما: {', '.join(SYMBOLS)} | التنبيهات لـ {len(CHATS)} محادثة")
    maybe_send(first=True)
    while True:
        try:
            discover_groups()
            maybe_send()
        except Exception as e:
            log(f"خطأ: {e}")
        time.sleep(LOOP_SLEEP_SEC)


if __name__ == "__main__":
    main()
