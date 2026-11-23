# ===== سكنر البيني ستوكس 4 ساعات =====
# نفس قالب gamma_scanner: يشتغل على Railway ويرسل على تيليجرام
# التشغيل: python penny_scanner.py   (المتغيرات: TELEGRAM_TOKEN + TELEGRAM_CHAT_ID)
"""
ناسداك - بيني ستوكس - فريم 4 ساعات مع البري والأفتر (4:00 - 20:00 نيويورك)

الشروط:
  - السعر بين MIN_PRICE و MAX_PRICE
  - الفري فلوت بين 2 و 20 مليون
  - اليوم اللي قبل أول صعود سيولته ما تتعدى 2 مليون $
  - صعود: شموع 4 ساعات خضراء متتالية، أول شمعة سيولتها فوق 15 مليون $
  - بعدها شمعة بيعية (حمراء) = قاع الإعداد (قاعها)
  - شمعة تنزل تحت القاع وتغلق فوقه = تنبيه
  - الوقف: قاع شمعة السحب، وبحد أقصى 15% تحت الدخول
  - الأهداف: قمم شموع الصعود اللي فوق سعر الدخول

شموع 4 ساعات (نيويورك): 4-8 / 8-12 / 12-16 / 16-20
الفحص بعد إغلاق كل شمعة بـ SCAN_DELAY_MIN دقايق

التشغيل:
  pip install yfinance pandas requests matplotlib
  python penny_scanner.py                 # يشتغل باستمرار
  python penny_scanner.py --now           # يفحص الحين ويطبع بالشاشة
  python penny_scanner.py --now --send    # يفحص الحين ويرسل لتيليجرام
  python penny_scanner.py --now ABCD XYZ  # أسهم معينة
  python penny_scanner.py --test          # تجربة بدون نت
"""

import gc
import io
import json
import os
import sys
import time
from datetime import datetime

import pandas as pd
import requests

# ================== الإعدادات ==================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "ضع_توكن_البوت_هنا")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "ضع_رقم_المحادثة_هنا")
AUTO_ADD_GROUPS = True
DATA_DIR = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH", ".")
CHATS_FILE = os.path.join(DATA_DIR, "penny_chats.txt")
STATE_FILE = os.path.join(DATA_DIR, "penny_scanner_state.json")
FLOAT_CACHE_FILE = os.path.join(DATA_DIR, "penny_float_cache.json")

NY = "America/New_York"
LOCAL_TZ = "Asia/Riyadh"
LOOP_SLEEP_SEC = 30

MIN_PRICE = float(os.environ.get("PENNY_MIN_PRICE", 1.0))
MAX_PRICE = float(os.environ.get("PENNY_MAX_PRICE", 10.0))
MIN_FLOAT = 2_000_000
MAX_FLOAT = 20_000_000

LIQ_MIN = 15_000_000            # سيولة أول شمعة صعود
LIQ_AS_VALUE = True             # True = قيمة (سعر × فوليوم) | False = عدد أسهم
LIQ_ON_FIRST = True             # True = أول شمعة خضراء | False = أي شمعة بالصعود
PREV_DAY_MAX_LIQ = 2_000_000    # اليوم اللي قبل أول صعود: سيولته ما تتعدى كذا (السهم كان نايم)
MIN_GREEN = 2                   # أقل عدد شموع خضراء متتالية
SETUP_EXPIRY = 12               # الإعداد يلغى بعد كذا شمعة بدون إشارة
MAX_STOP_PCT = 15               # الوقف بحد أقصى كذا % تحت الدخول
N_TARGETS = 3
REQUIRE_FVG = True              # True = ما يرسل إلا إذا فيه فير قاب 15 دقيقة فوق الدعم

# الأسهم: من سكرينر ياهو (ناسداك) + أي أسهم تضيفها بـ PENNY_SYMBOLS
EXTRA_SYMBOLS = [s.strip().upper() for s in os.environ.get("PENNY_SYMBOLS", "").split(",") if s.strip()]
SCREEN_MIN_VOLUME = 300_000     # أقل فوليوم يومي لدخول السكرينر
SCREEN_MAX = 750                # أقصى عدد أسهم من السكرينر
NASDAQ_CODES = ["NMS", "NGM", "NCM"]

SCAN_DELAY_MIN = 3              # الفحص بعد إغلاق الشمعة بكذا دقيقة
CANDLE_EDGES_NY = [8, 12, 16, 20]
HISTORY_DAYS = "15d"
SEND_CHART = True
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
            _send_one(cid, "✅ سكنر البيني متصل")


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
                          files={"photo": ("penny.png", png, "image/png")}, timeout=40).json()
        return bool(r.get("ok"))
    except Exception as e:
        log(f"فشل إرسال الصورة لـ {chat_id}:", e)
        return False


def send_telegram(text, photo=None):
    log(text)
    if _no_token():
        return
    for cid in list(CHATS):
        if photo and _send_photo_one(cid, photo, text):
            continue
        _send_one(cid, text)


# ================== الأسهم والفلوت ==================
def _json_load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _json_save(path, d):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(d, f)
    except Exception as e:
        log(f"ما قدرت أحفظ {path}: {e}")


def screen_universe():
    """أسهم ناسداك بيني من سكرينر ياهو."""
    import yfinance as yf
    syms = set()
    try:
        from yfinance import EquityQuery as Q
        q = Q("and", [
            Q("is-in", ["exchange"] + NASDAQ_CODES),
            Q("btwn", ["intradayprice", MIN_PRICE, MAX_PRICE]),
            Q("gt", ["dayvolume", SCREEN_MIN_VOLUME]),
        ])
        off = 0
        while off < SCREEN_MAX:
            r = yf.screen(q, size=250, offset=off, sortField="dayvolume", sortAsc=False)
            quotes = r.get("quotes", [])
            syms.update(x["symbol"] for x in quotes if x.get("symbol"))
            if len(quotes) < 250:
                break
            off += 250
    except Exception as e:
        log("السكرينر المخصص ما اشتغل:", e)
    for name in ("small_cap_gainers", "day_gainers", "most_actives"):
        try:
            r = yf.screen(name, count=250)
            for x in r.get("quotes", []):
                p = x.get("regularMarketPrice") or 0
                if x.get("symbol") and MIN_PRICE <= p <= MAX_PRICE and x.get("exchange") in NASDAQ_CODES:
                    syms.add(x["symbol"])
        except Exception:
            pass
    return sorted(syms)


def get_float(t, cache):
    today = str(pd.Timestamp.now(tz=NY).date())
    c = cache.get(t)
    if c and c.get("d") == today:
        return c.get("f")
    import yfinance as yf
    f = None
    try:
        info = yf.Ticker(t).info
        f = info.get("floatShares") or None
    except Exception:
        pass
    cache[t] = {"d": today, "f": f}
    return f


# ================== شموع 4 ساعات ==================
def norm15(df):
    """بيانات 15 دقيقة بتوقيت نيويورك، من 4:00 إلى 20:00 بس."""
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.dropna(subset=["Open", "High", "Low", "Close"])
    idx = df.index.tz_convert(NY) if df.index.tz is not None else df.index.tz_localize(NY)
    df = df.set_axis(idx)
    mins = idx.hour * 60 + idx.minute
    return df[(mins >= 240) & (mins < 1200)]


def to_4h(df, now=None):
    """15 دقيقة (مع البري والأفتر) -> شموع 4 ساعات 4-8/8-12/12-16/16-20 نيويورك، المغلقة بس."""
    df = norm15(df)
    if df.empty:
        return pd.DataFrame()
    mins = df.index.hour * 60 + df.index.minute
    bucket = (mins - 240) // 240
    day = df.index.normalize()
    start = day + pd.to_timedelta(240 + bucket * 240, unit="m")
    g = df.groupby(start)
    out = pd.DataFrame({"o": g["Open"].first(), "h": g["High"].max(), "l": g["Low"].min(),
                        "c": g["Close"].last(), "v": g["Volume"].sum()})
    now = now or pd.Timestamp.now(tz=NY)
    out = out[out.index + pd.Timedelta(hours=4) <= now]        # المغلقة بس
    return out


# ================== الإعداد والإشارة ==================
def find_signals(c4):
    """يمشي على شموع 4 ساعات ويرجع كل الإشارات (كسر القاع وإغلاق فوقه)."""
    sigs = []
    run_len, run_first_liq, run_max_liq, run_highs = 0, 0.0, 0.0, []
    active, pb_low, pb_i, pool, setup_liq = False, None, None, [], 0.0
    rows = list(c4.itertuples())
    day_liq = (c4["c"] * c4["v"] if LIQ_AS_VALUE else c4["v"]).groupby(c4.index.date).sum()
    days = list(day_liq.index)
    run_quiet = False
    for i, r in enumerate(rows):
        green, red = r.c > r.o, r.c < r.o
        liq = r.c * r.v if LIQ_AS_VALUE else r.v
        signal = False

        if active and i > pb_i:
            if r.l < pb_low and r.c > pb_low:
                signal, active = True, False
                sigs.append({"i": i, "t": r.Index, "close": r.c, "low": pb_low,
                             "sweep_low": r.l, "pool": list(pool), "liq": setup_liq})
            elif r.c < pb_low or i - pb_i >= SETUP_EXPIRY:
                active = False

        if green:
            if run_len == 0:
                run_highs, run_first_liq, run_max_liq = [], liq, 0.0
                k = days.index(r.Index.date())
                run_quiet = k > 0 and day_liq.iloc[k - 1] <= PREV_DAY_MAX_LIQ
            run_len += 1
            run_highs.append(r.h)
            run_max_liq = max(run_max_liq, liq)
        else:
            if red and run_len >= MIN_GREEN and not signal:
                setup = run_first_liq if LIQ_ON_FIRST else run_max_liq
                if setup >= LIQ_MIN and run_quiet:
                    active, pb_low, pb_i, pool, setup_liq = True, r.l, i, list(run_highs), setup
            run_len = 0
    return sigs


def find_fvg(m15, s):
    """أقرب فير فاليو قاب صاعد (15 دقيقة) فوق الدعم (قاع الشمعة البيعية اللي انسحبت سيولتها)، تكوّن بعد قاع شمعة السحب وما تعبّى."""
    t0, t1 = s["t"], s["t"] + pd.Timedelta(hours=4)
    d = m15[(m15.index >= t0) & (m15.index < t1)]
    if len(d) < 3:
        return None
    lows, highs = d["Low"].to_numpy(), d["High"].to_numpy()
    k0 = int(lows.argmin())                       # بار قاع السحب
    best = None
    for k in range(max(k0, 0) + 2, len(d)):
        bot, top = highs[k - 2], lows[k]
        if k - 2 < k0 or top <= bot or bot <= s["low"]:
            continue
        if k + 1 < len(d) and lows[k + 1:].min() <= bot:   # تعبّى
            continue
        if best is None or bot < best[0]:
            best = (float(bot), float(top), d.index[k])
    return best


def build_trade(s, fvg):
    """الدخول من الفير قاب، الوقف قاع السحب بحد أقصى 15%، الأهداف قمم الصعود."""
    if fvg:
        entry = fvg[1]                            # أعلى الفير قاب
    elif REQUIRE_FVG:
        return None
    else:
        entry = s["close"]
    stop = max(s["sweep_low"], entry * (1 - MAX_STOP_PCT / 100))
    tg, last = [], None
    for h in sorted(s["pool"]):
        if h > entry and (last is None or h > last) and len(tg) < N_TARGETS:
            tg.append(h)
            last = h
    return dict(s, entry=entry, stop=stop, targets=tg, fvg=fvg)


# ================== الرسالة والشارت ==================
def _p(v):
    return f"{v:.4f}" if v < 1 else f"{v:.2f}"


def _pct(a, b):
    return f"{(a / b - 1) * 100:+.1f}%"


def _m(v):
    return f"{v / 1e6:.1f}M"


def signal_message(t, s, flt):
    e = s["entry"]
    t_local = s["t"].tz_convert(LOCAL_TZ)
    f = s.get("fvg")
    L = [f"🚨 ${t}",
         f"دخول: {_p(e)}" + (f" (FVG {_p(f[0])} - {_p(f[1])})" if f else ""),
         f"الدعم: {_p(s['low'])}",
         f"وقف: {_p(s['stop'])} | خسارة {(1 - s['stop'] / e) * 100:.1f}%"]
    for i, h in enumerate(s["targets"], 1):
        L.append(f"هدف {i}: {_p(h)} ({_pct(h, e)})")
    L.append(f"فلوت: {_m(flt)} | سيولة: {_m(s['liq'])}")
    L.append(f"{t_local:%m-%d %H:%M} 4H")
    return "\n".join(L)


def signal_chart(t, c4, s, bars=40):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    d = c4.iloc[max(0, s["i"] - bars + 6): s["i"] + 1]
    bg, fg, grid = "#0f1419", "#d7dde3", "#26313b"
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=130)
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    for x, r in enumerate(d.itertuples()):
        col = "#22c55e" if r.c >= r.o else "#ef4444"
        ax.vlines(x, r.l, r.h, color=col, lw=1)
        ax.bar(x, max(abs(r.c - r.o), r.h * 0.001), bottom=min(r.o, r.c), color=col, width=0.7)
    n = len(d)

    def hl(y, col, txt, ls="-"):
        ax.axhline(y, color=col, ls=ls, lw=1.1)
        ax.text(n + 0.2, y, f"{txt} {_p(y)}", color=col, va="center", ha="left", fontsize=8,
                bbox=dict(facecolor=bg, edgecolor="none", pad=1))

    if s.get("fvg"):
        ax.axhspan(s["fvg"][0], s["fvg"][1], color="#38bdf8", alpha=0.18, lw=0)
    hl(s["entry"], "#38bdf8", "Entry")
    hl(s["low"], "#f59e0b", "Low", "--")
    hl(s["stop"], "#ef4444", "Stop")
    for i, h in enumerate(s["targets"], 1):
        hl(h, "#22c55e", f"T{i}", ":")
    ax.set_xlim(-1, n + 4)
    step = max(1, n // 8)
    ax.set_xticks(range(0, n, step))
    ax.set_xticklabels([d.index[i].tz_convert(LOCAL_TZ).strftime("%m-%d %H") for i in range(0, n, step)],
                       fontsize=7, color=fg, rotation=30)
    ax.tick_params(axis="y", colors=fg, labelsize=8)
    for sp in ax.spines.values():
        sp.set_color(grid)
    ax.grid(color=grid, lw=0.5)
    ax.set_title(f"\\${t}  4H", color=fg, fontsize=10, loc="left")
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=bg, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


# ================== الفحص ==================
def download(symbols):
    import yfinance as yf
    out = {}
    for i in range(0, len(symbols), 100):
        part = symbols[i:i + 100]
        try:
            df = yf.download(part, period=HISTORY_DAYS, interval="15m", prepost=True,
                             group_by="ticker", threads=True, progress=False, auto_adjust=False)
        except Exception as e:
            log("فشل التحميل:", e)
            continue
        for t in part:
            try:
                sub = df[t] if isinstance(df.columns, pd.MultiIndex) else df
                out[t] = sub.dropna(how="all")
            except KeyError:
                pass
        time.sleep(1)
    return out


def scan(symbols=None, send=True, only_last=True):
    t0 = time.time()
    st = _json_load(STATE_FILE)
    sent = st.setdefault("sent", {})
    cache = _json_load(FLOAT_CACHE_FILE)
    syms = symbols or sorted(set(screen_universe()) | set(EXTRA_SYMBOLS))
    log(f"[{datetime.now():%H:%M}] فحص {len(syms)} سهم")
    data = download(syms)
    hits = 0
    for t, raw in data.items():
        m15 = norm15(raw)
        c4 = to_4h(m15)
        if len(c4) < MIN_GREEN + 2:
            continue
        sigs = find_signals(c4)
        if not sigs:
            continue
        s = sigs[-1]
        if only_last and s["i"] != len(c4) - 1:
            continue
        s = build_trade(s, find_fvg(m15, s))
        if not s or not (MIN_PRICE <= s["entry"] <= MAX_PRICE):
            continue
        key = f"{t}|{s['t'].isoformat()}"
        if key in sent:
            continue
        flt = get_float(t, cache)
        if not flt or not (MIN_FLOAT <= flt <= MAX_FLOAT):
            continue
        png = None
        if SEND_CHART:
            try:
                png = signal_chart(t, c4, s)
            except Exception as e:
                log(f"شارت {t}: {e}")
        (send_telegram if send else (lambda txt, photo=None: log(txt)))(signal_message(t, s, flt), photo=png)
        sent[key] = 1
        hits += 1
    cutoff = (pd.Timestamp.now(tz=NY) - pd.Timedelta(days=5)).isoformat()
    st["sent"] = {k: v for k, v in sent.items() if k.split("|", 1)[1] >= cutoff}
    _json_save(STATE_FILE, st)
    _json_save(FLOAT_CACHE_FILE, cache)
    gc.collect()
    log(f"خلص: {hits} إشارة — {time.time() - t0:.0f} ثانية")


# ================== الجدولة ==================
def maybe_scan():
    now = pd.Timestamp.now(tz=NY)
    if now.weekday() >= 5:
        return
    st = _json_load(STATE_FILE)
    for h in CANDLE_EDGES_NY:
        edge = now.normalize() + pd.Timedelta(hours=h, minutes=SCAN_DELAY_MIN)
        key = edge.strftime("%Y-%m-%d %H")
        if edge <= now < edge + pd.Timedelta(minutes=60) and st.get("last_edge") != key:
            st["last_edge"] = key
            _json_save(STATE_FILE, st)
            scan()
            return


# ================== تجربة بدون نت ==================
def self_test():
    # 16 بار (15 دقيقة) لكل شمعة 4 ساعات، 4 شموع باليوم
    plan = [(1.02, 1.03, 1.00, 1.01, 20_000)] * 4 + [  # يوم هادي قبل الصعود (~1.3M$)
        (1.02, 1.05, 0.98, 1.00, 25_000),
        (1.01, 1.60, 1.00, 1.55, 750_000),     # أول خضراء سيولة كبيرة
        (1.55, 2.10, 1.50, 2.00, 450_000),
        (2.00, 2.40, 1.90, 2.30, 350_000),
        (2.30, 2.35, 1.80, 1.90, 300_000),     # بيعية -> الدعم 1.80
        (1.90, 2.00, 1.85, 1.95, 150_000),
        None,                                  # كسر 1.80 وإغلاق فوقه + فير قاب
        (1.92, 1.95, 1.88, 1.90, 50_000),
    ]
    sweep = [(1.95, 1.96, 1.90, 1.91), (1.91, 1.92, 1.80, 1.82), (1.82, 1.83, 1.70, 1.72),  # قاع 1.70
             (1.72, 1.82, 1.71, 1.81), (1.81, 1.84, 1.80, 1.83),                         # high 1.82
             (1.86, 1.93, 1.85, 1.92)]                                                   # low 1.85 > 1.82 = FVG
    sweep += [(1.92, 1.94, 1.88, 1.92)] * 10
    days = pd.bdate_range("2026-11-13", periods=3)
    idx, rows = [], []
    for n, p in enumerate(plan):
        day, slot = days[n // 4], n % 4
        start = day.tz_localize(NY) + pd.Timedelta(hours=4 + slot * 4)
        bars = sweep if p is None else [
            (p[0] if j == 0 else (p[0] + p[3]) / 2, p[1] if j == 5 else (p[0] + p[3]) / 2 + 0.001,
             p[2] if j == 9 else (p[0] + p[3]) / 2 - 0.001, p[3] if j == 15 else (p[0] + p[3]) / 2)
            for j in range(16)]
        for j, b in enumerate(bars):
            idx.append(start + pd.Timedelta(minutes=15 * j))
            rows.append(b + ((p[4] if p else 120_000),))
    df = pd.DataFrame(rows, index=pd.DatetimeIndex(idx), columns=["Open", "High", "Low", "Close", "Volume"])
    m15 = norm15(df)
    c4 = to_4h(m15, now=pd.Timestamp("2026-11-30", tz=NY))
    print(c4.round(3))
    sigs = find_signals(c4)
    assert len(sigs) == 1, sigs
    busy = c4.copy()
    busy.iloc[:4, busy.columns.get_loc("v")] *= 2        # اليوم اللي قبل فوق 2M -> ما فيه إشارة
    assert find_signals(busy) == [], "شرط اليوم الهادي ما اشتغل"
    fvg = find_fvg(m15, sigs[0])
    assert fvg and abs(fvg[0] - 1.82) < 1e-9 and abs(fvg[1] - 1.85) < 1e-9, fvg
    s = build_trade(sigs[0], fvg)
    assert s["low"] == 1.80 and s["entry"] == 1.85, s
    assert abs(s["stop"] - max(1.70, 1.85 * 0.85)) < 1e-9, s
    assert s["targets"] == [2.10, 2.40], s
    print("\n" + signal_message("TEST", s, 8_500_000))
    png = signal_chart("TEST", c4, s)
    with open("penny_TEST.png", "wb") as f:
        f.write(png)
    # الوقف بحد أقصى 15%
    s2 = build_trade(dict(sigs[0], sweep_low=1.0), (1.9, 2.0, None))
    assert abs(s2["stop"] - 1.7) < 1e-9, s2
    print(f"\nالشارت: penny_TEST.png ({len(png) // 1024} KB)\nPENNY TEST OK")


def main():
    if "--test" in sys.argv:
        self_test()
        return
    if "--now" in sys.argv:
        _load_chats()
        syms = [a.upper() for a in sys.argv[1:] if not a.startswith("--")] or None
        scan(syms, send="--send" in sys.argv, only_last="--all" not in sys.argv)
        return
    _load_chats()
    discover_groups()
    log(f"سكنر البيني 4H | التنبيهات لـ {len(CHATS)} محادثة")
    while True:
        try:
            discover_groups()
            maybe_scan()
        except Exception as e:
            log(f"خطأ: {e}")
        time.sleep(LOOP_SLEEP_SEC)


if __name__ == "__main__":
    main()
