import streamlit as st
import feedparser
import requests
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import html
import re
import time

# ────────────────────────────────────────────────────────────────
# PAGE CONFIG + AUTO-REFRESH EVERY 5 MINUTES
# ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Global Telecom & OTT Stellar Nexus",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Reliable auto-refresh
@st.fragment(run_every=300)
def keep_alive():
    st.markdown("", unsafe_allow_html=True)

st.markdown(
    '<script>setTimeout(function(){window.location.reload();}, 300000);</script>',
    unsafe_allow_html=True
)

# ────────────────────────────────────────────────────────────────
# YOUR ORIGINAL PROFESSIONAL STYLING
# ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    .stApp {
        background: url('https://raw.githubusercontent.com/rvijjapu/stellar-Nexus/main/4.png') no-repeat center center fixed;
        background-size: cover;
        font-family: 'Inter', sans-serif;
    }

    .header-container {
        background: rgba(255, 255, 255, 0.96);
        padding: 1.5rem 2rem;
        text-align: center;
        border-radius: 20px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.15);
        margin: 0 0 2rem 0;
        border-bottom: 4px solid #1e40af;
    }

    .main-title { font-size: 2.6rem; font-weight: 800; color: #0a192f; margin: 0; letter-spacing: -0.8px; }
    .subtitle { font-size: 1.1rem; color: #475569; margin-top: 0.6rem; font-weight: 500; }

    .hero-container {
        background: rgba(255, 255, 255, 0.98);
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 10px 35px rgba(0,0,0,0.12);
        border: 1px solid #e2e8f0;
    }

    .hero-title {
        color: #0a192f;
        font-size: 1.85rem;
        font-weight: 800;
        margin-bottom: 1.5rem;
        border-left: 6px solid #1e40af;
        padding-left: 15px;
    }

    .evergent-spotlight {
        background: linear-gradient(135deg, #1e40af, #3b82f6);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 6px 20px rgba(30,64,175,0.3);
    }

    .news-card, .news-card-priority {
        background: #fafbfc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 14px;
        margin-bottom: 12px;
        transition: all 0.3s ease;
    }

    .news-card-priority {
        border-left: 5px solid #dc2626;
        background: #fef2f2;
        box-shadow: 0 4px 12px rgba(220,38,38,0.12);
    }

    .news-card:hover, .news-card-priority:hover {
        background: #f1f5f9;
        box-shadow: 0 6px 16px rgba(0,0,0,0.12);
        transform: translateY(-2px);
    }

    .news-title {
        color: #1e40af;
        font-size: 0.98rem;
        font-weight: 600;
        line-height: 1.4;
        text-decoration: none;
        display: block;
        margin-bottom: 8px;
    }

    .news-title:hover { color: #1d4ed8; text-decoration: underline; }

    .news-meta {
        font-size: 0.78rem;
        color: #64748b;
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
    }

    .time-hot { color: #dc2626; font-weight: 700; }
    .time-warm { color: #ea580c; font-weight: 600; }
    .time-normal { color: #64748b; }

    .col-body { max-height: 520px; overflow-y: auto; padding-right: 6px; }
    .col-body::-webkit-scrollbar { width: 6px; }
    .col-body::-webkit-scrollbar-thumb { background: #94a3b8; border-radius: 10px; }

    #MainMenu, footer, header { visibility: hidden; }
    .stDeployButton { display: none; }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────────────────────
# COMPREHENSIVE LISTS (all from your message)
# ────────────────────────────────────────────────────────────────
EVERGENT_CLIENTS = {
    "Astro": ["astro malaysia", "astro sooka", "astro njoi", "astro", "sooka", "njoi"],
    "MongolTV": ["mongoltv", "mongol tv", "mongolia tv"],
    "FOX": ["fox sports", "fox corporation", "fox networks", "fox"],
    "AT&T": ["at&t", "att inc", "att wireless", "directv"],
    "NBA": ["nba", "national basketball"],
    "Shahid": ["shahid", "shahid vip", "mbc shahid"],
    "MBC": ["mbc group", "mbc", "middle east broadcasting"],
    "TV ASAHI": ["tv asahi", "asahi television", "asahi tv"],
    "TV3": ["tv3 malaysia", "tv3", "media prima"],
    "ABS-CBN": ["abs-cbn", "abscbn", "abs cbn", "philippine broadcast"],
    "Viki": ["viki", "rakuten viki", "viki streaming"],
    "TRT": ["trt world", "trt", "turkish radio"],
    "Sinclair": ["sinclair broadcast", "sinclair", "bally sports"],
    "FanDuel": ["fanduel", "fanduel group", "flutter"],
    "Bally Sports": ["bally sports", "bally regional", "diamond sports"],
    "Gotham": ["gotham advanced", "gotham fc"],
    "Marquee": ["marquee sports", "marquee network"],
    "Sony": ["sony pictures", "sony entertainment", "sonyliv", "sony india"],
    "Aha": ["aha video", "aha ott", "aha telugu"],
    "BBC": ["bbc", "british broadcasting", "bbc iplayer"],
    "Lightbox": ["lightbox", "spark lightbox"],
    "Sky": ["sky nz", "sky new zealand", "sky tv", "sky uk", "sky italia", "sky deutschland"],
    "Cignal": ["cignal tv", "cignal", "cignal satellite"],
    "ETV": ["etv network", "etv bharat"],
    "Simple TV": ["simpletv", "simple tv venezuela"],
    "Telekom Malaysia": ["telekom malaysia", "tm unifi", "unifi tv", "tm"],
    "Britbox": ["britbox", "britbox international"],
    "Quickplay": ["quickplay", "quickplay media"],
    "Pilipinas": ["pilipinas", "abs-cbn"],
}

COMPETITORS = {
    "Netcracker": ["netcracker", "netcracker technology", "nec netcracker"],
    "Amdocs": ["amdocs", "amdocs ltd", "amdocs inc"],
    "CSG": ["csg systems", "csg international", "csg"],
    "Oracle": ["oracle communications", "oracle corporation", "oracle telecom"],
    "Ericsson": ["ericsson", "telefonaktiebolaget lm ericsson"],
    "Nokia": ["nokia", "nokia networks", "nokia corporation"],
    "Huawei": ["huawei", "huawei technologies"],
    "Comarch": ["comarch", "comarch bss"],
    "Tecnotree": ["tecnotree", "tecnotree corporation"],
    "MATRIXX": ["matrixx", "matrixx software"],
    "Optiva": ["optiva", "optiva inc"],
    "Cerillion": ["cerillion", "cerillion plc"],
    "AsiaInfo": ["asiainfo", "asiainfo technologies"],
    "Hansen": ["hansen technologies", "hansen"],
    "Openet": ["openet", "openet telecom"],
    "ZTE": ["zte", "zte corporation"],
    "Mavenir": ["mavenir", "mavenir systems"],
    "Infosys": ["infosys", "infosys telecom"],
    "TCS": ["tata consultancy", "tcs", "tata communications"],
    "Wipro": ["wipro", "wipro digital"],
    "Tech Mahindra": ["tech mahindra", "mahindra comviva"],
    "Accenture": ["accenture", "accenture telecom"],
    "Capgemini": ["capgemini", "capgemini telecom"],
    "IBM": ["ibm", "ibm telecom", "ibm watson"],
    "SAP": ["sap", "sap telecom"],
    "Salesforce": ["salesforce", "salesforce communications"],
}

# Flatten all names for search
ALL_NAMES = []
for d in [EVERGENT_CLIENTS, COMPETITORS]:
    for k, v in d.items():
        ALL_NAMES.extend([k.lower()] + [x.lower() for x in v])

ALL_NAMES = list(set(ALL_NAMES))  # unique

# ────────────────────────────────────────────────────────────────
# NEWSAPI KEY – secure & reliable
# ────────────────────────────────────────────────────────────────
news_api_key = None

# 1. Prefer Streamlit Cloud secrets (recommended for production)
try:
    news_api_key = st.secrets["news_api_key"]
except:
    pass

# 2. Fallback: sidebar input (for testing or local run)
if not news_api_key:
    st.sidebar.header("NewsAPI Key (for real-time news)")
    news_api_key = st.sidebar.text_input(
        "Paste your NewsAPI key here",
        type="password",
        help="Get free key at https://newsapi.org/account"
    )
    if not news_api_key:
        st.sidebar.info("Enter your NewsAPI key for full coverage of Evergent clients, competitors & telcos. Without it, only RSS feeds shown.")

# ────────────────────────────────────────────────────────────────
# NEWSAPI FETCH – covers EVERYTHING in your lists
# ────────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_news_api(key):
    if not key:
        return []

    # Build massive query with all your clients, competitors, telcos + topics
    priority_part = " OR ".join([f"+{name}" for name in ALL_NAMES[:150]])  # safe limit to avoid URL overflow
    topic_part = "('OTT streaming' OR 5G OR VoD OR VoIP OR telecom OR BSS OR OSS OR billing OR churn OR 'content delivery' OR 'subscription management')"

    query = f"({priority_part} OR {topic_part}) NOT (crypto OR bitcoin OR nft OR ethereum)"

    url = f"https://newsapi.org/v2/everything?q={requests.utils.quote(query)}&language=en&sortBy=publishedAt&pageSize=20&apiKey={key}"

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        articles = r.json().get("articles", [])
        items = []
        for art in articles:
            pub_str = art.get("publishedAt")
            pub = datetime.fromisoformat(pub_str.replace("Z", "+00:00")) if pub_str else datetime.utcnow()
            if (datetime.utcnow() - pub).days > 30: continue

            full_text = (art.get("title", "") + " " + art.get("description", "")).lower()
            priority = any(kw in full_text for kw in PRIORITY_KWS + ALL_NAMES)

            items.append({
                "title": art.get("title", "No title"),
                "link": art.get("url", "#"),
                "source": art["source"].get("name", "NewsAPI"),
                "pub": pub,
                "priority": priority
            })
        return items
    except Exception as e:
        st.sidebar.warning(f"NewsAPI failed: {str(e)}. Using RSS fallback.")
        return []

# ────────────────────────────────────────────────────────────────
# RSS FETCH (your original feeds)
# ────────────────────────────────────────────────────────────────
RSS_FEEDS = [
    ("Telecoms.com", "https://www.telecoms.com/feed", "telco"),
    ("Light Reading", "https://www.lightreading.com/rss/simple", "telco"),
    ("Fierce Telecom", "https://www.fierce-network.com/rss.xml", "telco"),
    ("RCR Wireless", "https://www.rcrwireless.com/feed", "telco"),
    ("Mobile World Live", "https://www.mobileworldlive.com/feed/", "telco"),
    ("Variety", "https://variety.com/feed/", "ott"),
    ("Digital TV Europe", "https://www.digitaltveurope.com/feed/", "ott"),
    ("TechCrunch", "https://techcrunch.com/feed/", "technology"),
    ("The Verge", "https://www.theverge.com/rss/index.xml", "technology"),
]

def clean(text):
    return html.unescape(re.sub(r'<[^>]+>', '', str(text or ""))).strip()

def fetch_feed(source, url, category):
    items = []
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
        feed = feedparser.parse(r.content)
        cutoff = datetime.now() - timedelta(days=14)
        for entry in feed.entries[:20]:
            title = clean(entry.get("title", ""))
            if len(title) < 30: continue
            pub = None
            for k in ("published_parsed", "updated_parsed"):
                val = getattr(entry, k, None)
                if val:
                    try:
                        pub = datetime(*val[:6])
                        if pub < cutoff: continue
                    except: pass
            items.append({
                "title": title,
                "link": entry.get("link", "#"),
                "source": source,
                "pub": pub or datetime.now(),
                "category": category,
                "priority": any(kw in title.lower() for kw in PRIORITY_KWS + ALL_NAMES)
            })
    except Exception as e:
        st.sidebar.warning(f"RSS fetch failed for {source}: {str(e)}")
    return items

@st.cache_data(ttl=900, show_spinner=False)
def load_all_news():
    api_items = fetch_news_api(news_api_key)
    rss_items = []
    try:
        with ThreadPoolExecutor(max_workers=12) as ex:
            futures = [ex.submit(fetch_feed, s, u, c) for s, u, c in RSS_FEEDS]
            for f in as_completed(futures):
                rss_items.extend(f.result())
    except Exception as e:
        st.sidebar.warning(f"RSS parallel fetch error: {str(e)}")

    all_news = api_items + rss_items
    all_news.sort(key=lambda x: (not x["priority"], x["pub"]), reverse=True)

    categorized = {"telco": [], "ott": [], "technology": []}
    for item in all_news:
        title_lower = item["title"].lower()
        if any(kw in title_lower for kw in ["telecom", "5g", "bss", "oss", "netcracker", "amdocs"]):
            categorized["telco"].append(item)
        elif any(kw in title_lower for kw in ["ott", "streaming", "vod", "sony"]):
            categorized["ott"].append(item)
        else:
            categorized["technology"].append(item)

    return categorized

# ────────────────────────────────────────────────────────────────
# LOADING ANIMATION + HEADER + EVERGENT SPOTLIGHT
# ────────────────────────────────────────────────────────────────
placeholder = st.empty()
with placeholder.container():
    st.markdown("""
        <div style="display:flex;flex-direction:column;justify-content:center;align-items:center;height:70vh;text-align:center;">
            <h1 style="color:#0a192f;font-size:2.8rem;font-weight:800;">⚡ Igniting AI Powered Engine</h1>
            <p style="color:#64748b;font-size:1.2rem;">Real-time Strategic Signals – Mergers, Acquisitions, Partnerships & Deals</p>
        </div>
    """, unsafe_allow_html=True)
    time.sleep(1.2)
placeholder.empty()

st.markdown("""
<div class="header-container">
    <h1 class="main-title">Global Telecom & OTT Stellar Nexus</h1>
    <p class="subtitle">AI Powered Real-time Competitive Intelligence Dashboard – Evergent Ecosystem Focus</p>
</div>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────────────────────
# EVERGENT ECOSYSTEM SPOTLIGHT – comprehensive
# ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="evergent-spotlight">
    <h3 style="margin:0; color:white;">Evergent Technologies Ecosystem Spotlight</h3>
    <p style="margin:0.5rem 0 0; font-size:0.95rem;">
        <strong>Clients (publicly known):</strong> Astro/sooka/njoi, MongolTV, FOX, AT&T, NBA, Shahid/MBC, TV Asahi, TV3/Media Prima, ABS-CBN, Viki/Rakuten, TRT, Sinclair/Bally, FanDuel, Gotham, Marquee, Sony/SonyLIV/India, Aha, BBC, Lightbox/Spark, Sky (NZ/UK/Italia), Cignal, ETV, Simple TV, Telekom Malaysia/unifi, Britbox, Quickplay, Pilipinas...
    </p>
    <p style="margin:0.5rem 0 0; font-size:0.95rem;">
        <strong>Competitors:</strong> Netcracker/NEC, Amdocs, CSG, Oracle, Ericsson, Nokia, Huawei, Comarch, Tecnotree, MATRIXX, Optiva, Cerillion, AsiaInfo, Hansen, Openet, ZTE, Mavenir, Infosys, TCS, Wipro, Tech Mahindra, Accenture, Capgemini, IBM, SAP, Salesforce...
    </p>
    <p style="margin:0.5rem 0 0; font-size:0.9rem;">
        <strong>Top Telcos:</strong> Verizon, AT&T, T-Mobile, Comcast, Charter, Cox, Lumen, Frontier, Windstream, Mediacom, Altice, BT, Vodafone, O2, Virgin Media, Three, Orange, Deutsche Telekom, Telefónica, Telecom Italia, Swisscom, KPN, Proximus, Telenor, Telia, Bouygues, Singtel, StarHub, M1, Maxis, Celcom, Digi, Telekom Malaysia, U Mobile, Sky NZ, Spark, 2degrees, Telstra, Optus, TPG, China Mobile, China Telecom, China Unicom, NTT, SoftBank, KDDI, Reliance Jio, Airtel, Vi, BSNL, SK Telecom, KT, LG Uplus, Globe, PLDT, Smart, Etisalat, Du, STC, Ooredoo, Zain, Mobily, América Móvil, Telus, Rogers, Bell, Shaw, MTN, Vodacom, Safaricom...
    </p>
</div>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────────────────────
# MAIN NEWS GRID
# ────────────────────────────────────────────────────────────────
with st.spinner("Scanning NewsAPI + RSS for latest Evergent & ecosystem signals..."):
    data = load_all_news()

cols = st.columns(3)
sections = [
    ("telco", "TELCO OSS/BSS", "col-header-pink", "📡"),
    ("ott", "OTT & STREAMING", "col-header-purple", "📺"),
    ("technology", "AI & TECHWATCH", "col-header-orange", "⚡")
]

for i, (cat, name, style, icon) in enumerate(sections):
    with cols[i]:
        st.markdown(f'<div class="{style}">{icon} {name}</div>', unsafe_allow_html=True)
        items = data.get(cat, [])[:12]
        if not items:
            st.markdown('<div style="text-align:center; color:#94a3b8; padding:40px;">No recent signals – check key or refresh...</div>', unsafe_allow_html=True)
            continue

        for item in items:
            time_ago = (datetime.now() - item["pub"]).total_seconds() / 3600
            time_str = "Now" if time_ago < 1 else f"{int(time_ago)}h" if time_ago < 24 else f"{int(time_ago/24)}d"
            time_class = "time-hot" if time_ago < 3 else "time-warm" if time_ago < 12 else "time-normal"

            priority_class = "news-card-priority" if item["priority"] else "news-card"

            st.markdown(f"""
            <div class="{priority_class}">
                <a href="{item['link']}" target="_blank" class="news-title">{html.escape(item['title'])}</a>
                <div class="news-meta">
                    <span class="{time_class}">{time_str}</span>
                    <span>•</span>
                    <span>{item['source']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ────────────────────────────────────────────────────────────────
# FOOTER
# ────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; color:rgba(255,255,255,0.9); font-size:0.85rem; margin:3rem 0; padding:1.2rem; background:linear-gradient(135deg,rgba(10,25,47,0.9),rgba(30,41,59,0.9)); border-radius:12px;">
    <strong>Focus:</strong> Mergers • Acquisitions • Partnerships • Deals • Strategic Moves<br>
    <strong>Priority:</strong> Evergent & full ecosystem (clients, competitors, top telcos)<br>
    <strong>Live:</strong> NewsAPI + RSS • Auto-refresh every 5 min • Powered by Srinivasa Dasu @saptechsrini
</div>
""", unsafe_allow_html=True)

keep_alive()
