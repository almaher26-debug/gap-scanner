#!/usr/bin/env python3
"""
ماسح شراكات الشركات الكبرى  —  Big-Cap Partnership Scanner
============================================================
يراقب الأخبار كل بضع دقائق. أول ما يطلع خبر شراكة / صفقة / اتفاقية / استثمار
فيه:
  • شركة كبرى: أي سهم أمريكي قيمته السوقية فوق BIG_CAP_MIN (افتراضي 50 مليار $)
    — بدون قائمة ثابتة، السكنر يكتشفها بنفسه من الخبر
  • وشريك: سهم مدرج في ناسداك (PARTNER_EXCHANGES) قيمته فوق MIN_MARKET_CAP (افتراضي 1 مليار $)
يرسل لك تنبيه تيليجرام فيه رموز كل الأطراف.

التشغيل:
    python scanner.py            # يشتغل على طول ويمسح كل SCAN_MINUTES دقيقة
    python scanner.py --once     # مسح واحد فقط
    python scanner.py --test     # رسالة تجربة لتيليجرام
    python scanner.py --dry-run  # يطبع التنبيهات بدل ما يرسلها
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote_plus

import feedparser
import requests

BASE_DIR = Path(__file__).resolve().parent
RIYADH = timezone(timedelta(hours=3))


# ─────────────────────────── الإعدادات ───────────────────────────
def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_dotenv(BASE_DIR / ".env")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
SCAN_MINUTES = float(os.getenv("SCAN_MINUTES", "10"))
BIG_CAP_MIN = float(os.getenv("BIG_CAP_MIN", "50000000000"))        # الشركة الكبرى: فوق 50 مليار $
MIN_MARKET_CAP = float(os.getenv("MIN_MARKET_CAP", "1000000000"))   # الشريك: فوق 1 مليار $
# بورصة الشريك: NASDAQ فقط افتراضياً. تبي NYSE بعد؟ اكتب NASDAQ,NYSE
PARTNER_EXCHANGES = {x.strip().upper() for x in os.getenv("PARTNER_EXCHANGES", "NASDAQ").split(",") if x.strip()}
MAX_AGE_HOURS = float(os.getenv("MAX_AGE_HOURS", "24"))
# SEC تطلب User-Agent فيه إيميل حقيقي
SEC_USER_AGENT = os.getenv("SEC_USER_AGENT", "PartnershipScanner your-email@example.com")

# شركات خاصة كبرى نعاملها كـ "شركة كبرى" لو سوّت شراكة مع سهم ناسداك
BIG_PRIVATE = {"spacex": "SpaceX", "openai": "OpenAI", "anthropic": "Anthropic", "xai": "xAI"}

# عمليات البحث العامة — تغطي كل الشركات، مو أسماء محددة
SEARCH_QUERIES = [
    '"strategic partnership" Nasdaq',
    '"announce partnership" OR "announces partnership"',
    '"multiyear agreement" OR "multi-year agreement"',
    '"teams up with" OR "partners with" stock',
    '"collaboration agreement" OR "strategic collaboration"',
    '"supply agreement" OR "signs deal" OR "inks deal"',
    '"to invest" stake partnership billion',
    'site:prnewswire.com partnership',
    'site:businesswire.com partnership',
    'site:globenewswire.com partnership',
    'Nvidia OR Microsoft OR Apple OR Amazon OR Google OR Tesla OR Meta partnership',
    'Broadcom OR Oracle OR AMD OR Palantir OR Netflix OR Salesforce deal agreement',
]

# كلمات تدل إن الخبر فعلاً شراكة/صفقة
DEAL_WORDS = [
    "partner", "partnership", "partners with", "teams up", "team up", "joins forces",
    "collaborat", "alliance", "deal", "agreement", "agrees", "signs", "signed",
    "contract", "supply", "invest", "investment", "stake", "acquire", "acquisition",
    "buys", "to buy", "merger", "joint venture", "pact", "selects", "chooses",
    "expands relationship", "multiyear", "multi-year", "warrant", "backs",
    "commit", "orders", "order for", "teaming", "integrat", "license", "licensing",
]

# شركات خاصة معروفة (ما لها رمز)
KNOWN_PRIVATE = {
    **BIG_PRIVATE,
    "databricks": "Databricks", "mistral": "Mistral AI", "perplexity": "Perplexity",
    "scale ai": "Scale AI", "stripe": "Stripe", "figure ai": "Figure AI", "nscale": "Nscale",
    "crusoe": "Crusoe", "cerebras": "Cerebras", "waymo": "Waymo", "neuralink": "Neuralink",
}

# أسماء دارجة → رمز (الأخبار ما تكتب الاسم الرسمي دايماً)
ALIASES = {
    "nvidia": "NVDA", "apple": "AAPL", "tesla": "TSLA", "microsoft": "MSFT", "azure": "MSFT",
    "amazon": "AMZN", "aws": "AMZN", "amazon web services": "AMZN",
    "google": "GOOGL", "alphabet": "GOOGL", "google cloud": "GOOGL", "deepmind": "GOOGL",
    "youtube": "GOOGL", "meta": "META", "meta platforms": "META", "facebook": "META",
    "instagram": "META", "whatsapp": "META", "tsmc": "TSM", "taiwan semiconductor": "TSM",
    "broadcom": "AVGO", "amd": "AMD", "intel": "INTC", "oracle": "ORCL", "ibm": "IBM",
    "qualcomm": "QCOM", "micron": "MU", "arm": "ARM", "arm holdings": "ARM", "asml": "ASML",
    "salesforce": "CRM", "adobe": "ADBE", "palantir": "PLTR", "coreweave": "CRWV",
    "dell": "DELL", "hpe": "HPE", "hewlett packard enterprise": "HPE", "supermicro": "SMCI",
    "super micro": "SMCI", "cisco": "CSCO", "uber": "UBER", "lyft": "LYFT", "netflix": "NFLX",
    "spotify": "SPOT", "shopify": "SHOP", "snowflake": "SNOW", "servicenow": "NOW",
    "crowdstrike": "CRWD", "palo alto networks": "PANW", "synopsys": "SNPS", "cadence": "CDNS",
    "marvell": "MRVL", "texas instruments": "TXN", "eaton": "ETN", "vertiv": "VRT",
    "corning": "GLW", "lumentum": "LITE", "coherent": "COHR", "softbank": "SFTBY",
    "sony": "SONY", "toyota": "TM", "general motors": "GM", "ford": "F", "stellantis": "STLA",
    "honda": "HMC", "chevron": "CVX", "exxon": "XOM", "exxonmobil": "XOM",
    "constellation energy": "CEG", "vistra": "VST", "nextera": "NEE", "oklo": "OKLO",
    "nuscale": "SMR", "generac": "GNRC", "adp": "ADP", "braze": "BRZE", "evgo": "EVGO",
    "walmart": "WMT", "costco": "COST", "jpmorgan": "JPM", "goldman sachs": "GS",
    "morgan stanley": "MS", "blackrock": "BLK", "visa": "V", "mastercard": "MA",
    "paypal": "PYPL", "verizon": "VZ", "at&t": "T", "t-mobile": "TMUS", "comcast": "CMCSA",
    "disney": "DIS", "nike": "NKE", "starbucks": "SBUX", "ups": "UPS", "fedex": "FDX",
    "boeing": "BA", "lockheed martin": "LMT", "rocket lab": "RKLB", "ast spacemobile": "ASTS",
    "nebius": "NBIS", "iren": "IREN", "applied digital": "APLD", "digital realty": "DLR",
    "equinix": "EQIX", "ionq": "IONQ", "rigetti": "RGTI", "d-wave": "QBTS",
    "soundhound": "SOUN", "c3.ai": "AI", "pinterest": "PINS", "reddit": "RDDT",
    "roblox": "RBLX", "zoom": "ZM", "workday": "WDAY", "intuit": "INTU", "accenture": "ACN",
    "rivian": "RIVN", "lucid": "LCID", "mobileye": "MBLY", "nokia": "NOK", "ericsson": "ERIC",
    "applovin": "APP", "robinhood": "HOOD", "coinbase": "COIN", "strategy": "MSTR",
    "microstrategy": "MSTR", "airbnb": "ABNB", "doordash": "DASH", "booking": "BKNG",
    "eli lilly": "LLY", "lilly": "LLY", "novo nordisk": "NVO", "pfizer": "PFE",
    "johnson & johnson": "JNJ", "unitedhealth": "UNH", "berkshire hathaway": "BRK-B",
    "lam research": "LRCX", "applied materials": "AMAT", "kla": "KLAC", "analog devices": "ADI",
    "nxp": "NXPI", "on semiconductor": "ON", "onsemi": "ON", "arista": "ANET",
    "fortinet": "FTNT", "zscaler": "ZS", "datadog": "DDOG", "mongodb": "MDB",
    "cloudflare": "NET", "atlassian": "TEAM", "astera labs": "ALAB", "credo": "CRDO",
}

# كلمات إنجليزية عامة تطابق أسماء شركات بقائمة SEC — نتجاهلها
COMMON_WORDS = set("""
target block gap visa match ally chewy snap unity zoom box gold global first general united
american national energy power data cloud digital capital financial bank group trust health
care life new one best smart open core edge peak alpha beta delta sigma apex summit
vision future frontier pioneer liberty freedom eagle star sun moon sky river ocean lake
rock stone iron steel wave light bright clear true real live link net web point center
focus key prime plus pro max ultra mega super hyper deal strategy booking lilly kla
""".split())

SUFFIX_TOKENS = {
    "inc", "incorporated", "corp", "corporation", "co", "company", "companies", "ltd",
    "limited", "plc", "llc", "lp", "holdings", "holding", "group", "sa", "nv", "ag", "se",
    "the", "class", "a", "b", "c", "de", "com", "adr", "ads", "trust", "international",
}


# ─────────────────────────── أدوات ───────────────────────────
def log(msg: str) -> None:
    print(f"[{datetime.now(RIYADH):%Y-%m-%d %H:%M:%S}] {msg}", flush=True)


def normalize_name(name: str) -> str:
    s = name.lower().replace("&", " and ")
    s = re.sub(r"/[a-z]{2}/", " ", s)
    s = re.sub(r"[^a-z0-9\- ]+", " ", s)
    toks = s.split()
    while toks and toks[-1] in SUFFIX_TOKENS:
        toks.pop()
    while toks and toks[0] == "the":
        toks.pop(0)
    return " ".join(toks)


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9][a-z0-9&\-\.]*[a-z0-9]|[a-z0-9]", text.lower())


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, data) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


# ─────────────────────────── قاعدة الأسهم (SEC) ───────────────────────────
class TickerDB:
    """كل الأسهم المدرجة في أمريكا مع البورصة (من SEC) + الأسماء الدارجة."""

    URL = "https://www.sec.gov/files/company_tickers_exchange.json"

    def __init__(self) -> None:
        self.name_to_ticker: dict[str, str] = {}
        self.ticker_name: dict[str, str] = {}
        self.ticker_exchange: dict[str, str] = {}
        self.cache_path = BASE_DIR / "sec_tickers_cache.json"
        self._load()

    def _load(self) -> None:
        data = None
        if self.cache_path.exists() and time.time() - self.cache_path.stat().st_mtime < 7 * 86400:
            data = load_json(self.cache_path, None)
        if data is None:
            try:
                r = requests.get(self.URL, headers={"User-Agent": SEC_USER_AGENT}, timeout=30)
                r.raise_for_status()
                data = r.json()
                save_json(self.cache_path, data)
                log(f"حمّلت قائمة SEC: {len(data.get('data', []))} سهم")
            except Exception as e:
                log(f"تعذّر تحميل قائمة SEC ({e}) — أكمل بالأسماء الدارجة")
                data = load_json(self.cache_path, {}) or {}

        fields = data.get("fields", ["cik", "name", "ticker", "exchange"])
        idx = {f: i for i, f in enumerate(fields)}
        seen_cik = set()
        for row in data.get("data", []):
            cik, name, ticker = row[idx["cik"]], row[idx["name"]], (row[idx["ticker"]] or "").upper()
            exch = (row[idx["exchange"]] or "").upper()
            if not ticker:
                continue
            self.ticker_exchange.setdefault(ticker, exch)
            self.ticker_name.setdefault(ticker, name)
            if cik in seen_cik:          # أول رمز للشركة هو الأساسي
                continue
            seen_cik.add(cik)
            norm = normalize_name(name)
            if len(norm) < 4 or norm in COMMON_WORDS or (" " not in norm and len(norm) < 5):
                continue
            self.name_to_ticker.setdefault(norm, ticker)

        for alias, tk in ALIASES.items():
            self.name_to_ticker[alias] = tk

    def name(self, tk: str) -> str:
        return self.ticker_name.get(tk, tk)

    def exchange(self, tk: str) -> str:
        return self.ticker_exchange.get(tk, "")


# ─────────────────────────── القيمة السوقية ───────────────────────────
class MarketCaps:
    def __init__(self) -> None:
        self.path = BASE_DIR / "market_cap_cache.json"
        self.cache: dict[str, list] = load_json(self.path, {})

    def get(self, ticker: str) -> float | None:
        hit = self.cache.get(ticker)
        if hit and time.time() - hit[1] < 86400:
            return hit[0]
        cap = None
        try:
            import yfinance as yf
            t = yf.Ticker(ticker)
            try:
                cap = t.fast_info["market_cap"]
            except Exception:
                cap = None
            if not cap:
                cap = (t.info or {}).get("marketCap")
        except Exception as e:
            log(f"تعذّر جلب القيمة السوقية لـ {ticker}: {e}")
        if cap:
            self.cache[ticker] = [float(cap), time.time()]
            save_json(self.path, self.cache)
            return float(cap)
        return None


def fmt_cap(cap: float | None) -> str:
    if not cap:
        return "؟"
    if cap >= 1e12:
        return f"${cap / 1e12:.2f} تريليون"
    return f"${cap / 1e9:.1f} مليار"


# ─────────────────────────── جلب الأخبار ───────────────────────────
@dataclass
class Article:
    title: str
    link: str
    summary: str
    published: datetime | None
    source: str = ""


def fetch_articles() -> list[Article]:
    out: list[Article] = []
    headers = {"User-Agent": "Mozilla/5.0 (PartnershipScanner)"}
    for q in SEARCH_QUERIES:
        url = ("https://news.google.com/rss/search?q=" + quote_plus(q + " when:1d")
               + "&hl=en-US&gl=US&ceid=US:en")
        try:
            r = requests.get(url, headers=headers, timeout=20)
            feed = feedparser.parse(r.content)
        except Exception as e:
            log(f"خطأ بجلب الأخبار ({q}): {e}")
            continue
        for e in feed.entries:
            pub = None
            if getattr(e, "published_parsed", None):
                pub = datetime(*e.published_parsed[:6], tzinfo=timezone.utc)
            summary = re.sub(r"<[^>]+>", " ", html.unescape(e.get("summary", "")))
            src = e.source.get("title", "") if isinstance(getattr(e, "source", None), dict) else ""
            out.append(Article(e.get("title", "").strip(), e.get("link", ""), summary, pub, src))
        time.sleep(0.5)
    return out


# ─────────────────────────── التحليل ───────────────────────────
EXPLICIT_TICKER_RE = re.compile(
    r"\(\s*(NASDAQ|Nasdaq|NYSE|NYSE American|AMEX|NYSEARCA|OTC|OTCQX)\s*[:：]\s*([A-Z][A-Z.\-]{0,5})\s*\)"
    r"|\b(NASDAQ|NYSE)\s*:\s*([A-Z][A-Z.\-]{0,5})\b"
)
CASHTAG_RE = re.compile(r"\$([A-Z]{1,5})\b")


def is_deal(text: str) -> bool:
    t = text.lower()
    return any(w in t for w in DEAL_WORDS)


def clean_title(title: str) -> str:
    return re.sub(r"\s+-\s+[^-]{2,60}$", "", title).strip()


def detect(text: str, db: TickerDB) -> tuple[dict[str, str], list[str], dict[str, str]]:
    """يرجع: الرموز المذكورة (رمز← الاسم بالخبر)، الشركات الخاصة، والبورصات المكتوبة صراحة."""
    tickers: dict[str, str] = {}
    explicit_exch: dict[str, str] = {}
    privates: list[str] = []

    for m in EXPLICIT_TICKER_RE.finditer(text):
        ex = (m.group(1) or m.group(3) or "").upper()
        tk = (m.group(2) or m.group(4) or "").upper()
        if tk:
            tickers.setdefault(tk, tk)
            explicit_exch[tk] = "NASDAQ" if "NASDAQ" in ex else ("NYSE" if "NYSE" in ex else ex)
    for m in CASHTAG_RE.finditer(text):
        if m.group(1) in db.ticker_name:
            tickers.setdefault(m.group(1), m.group(1))

    tokens = tokenize(text)
    used: set[int] = set()
    for n in range(5, 0, -1):
        for i in range(len(tokens) - n + 1):
            if any(j in used for j in range(i, i + n)):
                continue
            g = " ".join(tokens[i:i + n])
            if g in KNOWN_PRIVATE:
                if KNOWN_PRIVATE[g] not in privates:
                    privates.append(KNOWN_PRIVATE[g])
                used.update(range(i, i + n))
            elif g in db.name_to_ticker:
                tickers.setdefault(db.name_to_ticker[g], g)
                used.update(range(i, i + n))
    return tickers, privates, explicit_exch


@dataclass
class Company:
    ticker: str
    name: str
    cap: float | None
    exchange: str


def classify(text: str, db: TickerDB, caps: MarketCaps):
    """يرجع (الكبرى، الشركاء، شركات خاصة) أو None لو الخبر ما يطابق الشروط."""
    tickers, privates, explicit_exch = detect(text, db)
    companies = []
    for tk, mention in tickers.items():
        exch = explicit_exch.get(tk) or db.exchange(tk)
        nm = db.name(tk) if tk in db.ticker_name else mention.title()
        companies.append(Company(tk, nm, caps.get(tk), exch))

    big = [c for c in companies if c.cap and c.cap >= BIG_CAP_MIN]
    big_private = [p for p in privates if p in BIG_PRIVATE.values()]
    if not big and not big_private:
        return None

    big_set = {c.ticker for c in big}
    partners = []
    for c in companies:
        if c.cap is not None and c.cap < MIN_MARKET_CAP:
            continue
        if PARTNER_EXCHANGES and c.exchange and c.exchange not in PARTNER_EXCHANGES:
            continue
        # الشريك ممكن يكون كبير بعد (مثلاً NVDA + AMZN) بس لازم يختلف عن الكبرى الأولى
        partners.append(c)

    # لازم يكون فيه طرفين على الأقل: كبرى + سهم ناسداك ثاني
    if big:
        lead = max(big, key=lambda c: c.cap or 0)
        others = [p for p in partners if p.ticker != lead.ticker]
        if others:
            return [lead], others, [p for p in privates]
        if not big_private:
            return None
        # مثل: SpaceX (خاصة كبرى) + QCOM → السهم الكبير يصير هو الشريك
    # الكبرى شركة خاصة (SpaceX/OpenAI...) والشريك سهم ناسداك
    if not partners:
        return None
    return [], partners, privates


# ─────────────────────────── تيليجرام ───────────────────────────
def send_telegram(text: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log("⚠️ TELEGRAM_BOT_TOKEN أو TELEGRAM_CHAT_ID ناقص — بطبع الرسالة بس")
        print(text)
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=20,
        )
        if r.status_code != 200:
            log(f"تيليجرام رفض الرسالة: {r.text[:200]}")
            return False
        return True
    except Exception as e:
        log(f"خطأ إرسال تيليجرام: {e}")
        return False


def build_message(art: Article, lead: list[Company], partners: list[Company], privates: list[str]) -> str:
    esc = html.escape
    lines = ["🔔 <b>شراكة / صفقة جديدة</b>", ""]
    for c in lead:
        lines.append(f"🏢 الكبرى: <b>{esc(c.ticker)}</b> — {esc(c.name)} — {fmt_cap(c.cap)}")
    big_priv = [p for p in privates if p in BIG_PRIVATE.values()]
    if not lead and big_priv:
        lines.append(f"🏢 الكبرى: <b>{esc(big_priv[0])}</b> (شركة خاصة)")
    lines.append("🤝 الشركاء:")
    for c in partners:
        ex = f" [{esc(c.exchange)}]" if c.exchange else ""
        lines.append(f"   • <b>{esc(c.ticker)}</b>{ex} — {esc(c.name)} — {fmt_cap(c.cap)}")
    for p in privates:
        if lead or p != (big_priv[0] if big_priv else None):
            lines.append(f"   • {esc(p)} — شركة خاصة (ما لها رمز)")
    all_tk = [c.ticker for c in lead + partners]
    lines += ["", "📊 الرموز: " + " ".join(f"${t}" for t in dict.fromkeys(all_tk)),
              "", f"📰 {esc(clean_title(art.title))}"]
    if art.source:
        lines.append(f"🗞 {esc(art.source)}")
    if art.published:
        lines.append(f"🕒 {art.published.astimezone(RIYADH):%Y-%m-%d %H:%M} (الرياض)")
    lines.append(f"🔗 {esc(art.link)}")
    return "\n".join(lines)


# ─────────────────────────── المسح ───────────────────────────
def story_key(art: Article) -> str:
    t = re.sub(r"[^a-z0-9 ]", "", clean_title(art.title).lower())
    return hashlib.sha1(" ".join(t.split()[:12]).encode()).hexdigest()[:16]


def scan(db: TickerDB, caps: MarketCaps, seen: dict, notify: bool, dry_run: bool) -> int:
    arts = fetch_articles()
    log(f"جبت {len(arts)} خبر")
    cutoff = datetime.now(timezone.utc) - timedelta(hours=MAX_AGE_HOURS)
    sent = 0
    for art in arts:
        key = story_key(art)
        if key in seen:
            continue
        seen[key] = time.time()
        if art.published and art.published < cutoff:
            continue
        text = f"{clean_title(art.title)}. {art.summary}"
        if not is_deal(text):
            continue
        res = classify(text, db, caps)
        if not res:
            continue
        if not notify:
            continue
        msg = build_message(art, *res)
        if dry_run:
            print("\n" + "─" * 50 + "\n" + msg)
        else:
            send_telegram(msg)
            time.sleep(1)
        sent += 1

    old = time.time() - 7 * 86400
    for k in [k for k, v in seen.items() if v < old]:
        del seen[k]
    return sent


def main() -> None:
    ap = argparse.ArgumentParser(description="ماسح شراكات الشركات الكبرى")
    ap.add_argument("--once", action="store_true", help="مسح واحد ثم خروج")
    ap.add_argument("--test", action="store_true", help="رسالة تجربة لتيليجرام")
    ap.add_argument("--dry-run", action="store_true", help="اطبع التنبيهات بدل الإرسال")
    ap.add_argument("--send-existing", action="store_true",
                    help="بأول تشغيل أرسل أخبار آخر 24 ساعة (الافتراضي: يحفظها بدون إرسال)")
    args = ap.parse_args()

    if args.test:
        ok = send_telegram("✅ بوت ماسح الشراكات شغّال!\nبيوصلك تنبيه أول ما يطلع خبر شراكة جديدة.")
        print("تم الإرسال ✅" if ok else "فشل الإرسال ❌ — تأكد من التوكن ورقم المحادثة")
        return

    seen_path = BASE_DIR / "seen.json"
    first_run = not seen_path.exists()
    seen: dict = load_json(seen_path, {})
    db, caps = TickerDB(), MarketCaps()
    log(f"بدأ المسح — الكبرى ≥ {fmt_cap(BIG_CAP_MIN)}، الشريك ≥ {fmt_cap(MIN_MARKET_CAP)} "
        f"في {','.join(sorted(PARTNER_EXCHANGES)) or 'أي بورصة'}، كل {SCAN_MINUTES:g} دقيقة")

    while True:
        notify = args.dry_run or args.send_existing or not first_run
        try:
            n = scan(db, caps, seen, notify=notify, dry_run=args.dry_run)
            save_json(seen_path, seen)
            if first_run and not notify:
                log("أول تشغيل: حفظت أخبار اليوم بدون إرسال. من الحين أي جديد يوصلك 🔔")
            else:
                log(f"أرسلت {n} تنبيه")
        except Exception as e:
            log(f"خطأ بالمسح: {e}")
        first_run = False
        if args.once:
            break
        time.sleep(SCAN_MINUTES * 60)


if __name__ == "__main__":
    main()
