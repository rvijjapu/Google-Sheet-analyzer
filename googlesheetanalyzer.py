import streamlit as st
import feedparser
import requests
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import html
import re
import time

# ────────────────────────────────────────────────────────────────
# PAGE CONFIG + KEEP-ALIVE + AUTO-REFRESH
# ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Global Telecom & OTT Stellar Nexus",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

@st.fragment(run_every=300)
def keep_alive():
    st.markdown("", unsafe_allow_html=True)

st.markdown(
    '<script>setTimeout(function(){window.location.reload();}, 300000);</script>',
    unsafe_allow_html=True
)

# ────────────────────────────────────────────────────────────────
# STYLING (your original + tweaks for better news card readability)
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
# PRIORITY & NEWSAPI SETUP
# ────────────────────────────────────────────────────────────────
PRIORITY_KWS = ["evergent", "nba", "amdocs", "matrixx", "netcracker", "nec", "csg", "sony", "ott", "5g", "vod", "voip", "billing", "bss", "oss"]

# API key handling (secrets first, then sidebar)
try:
    news_api_key = st.secrets["news_api_key"]
except:
    news_api_key = None

if not news_api_key:
    st.sidebar.header("NewsAPI Key (for real-time coverage)")
    news_api_key = st.sidebar.text_input("Paste your NewsAPI key", type="password", help="https://newsapi.org – free tier ok")
    if not news_api_key:
        st.sidebar.info("Add key for best coverage. Without it, only RSS is used.")

# ────────────────────────────────────────────────────────────────
# ENHANCED NEWSAPI FETCH – full coverage of your priorities
# ────────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_news_api(key):
    if not key:
        return []

    # Advanced query: group priorities + OR for topics + exclude noise
    query = (
        f"({'+evergent OR +nba OR +amdocs OR +matrixx OR +netcracker OR +nec OR +csg OR +sony'} OR "
        f"('OTT streaming' OR 5G OR VoD OR VoIP OR telecom OR BSS OR OSS)) "
        f"NOT (crypto OR bitcoin OR ethereum OR 'stock market')"
    )

    url = (
        f"https://newsapi.org/v2/everything?"
        f"q={requests.utils.quote(query)}"
        f"&language=en&sortBy=publishedAt&pageSize=20&apiKey={key}"
    )

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        articles = r.json().get("articles", [])
        items = []
        for art in articles:
            pub_str = art.get("publishedAt")
            pub = datetime.fromisoformat(pub_str.replace("Z", "+00:00")) if pub_str else datetime.utcnow()
            if (datetime.utcnow() - pub).days > 14:
                continue

            title_desc = (art.get("title", "") + " " + art.get("description", "")).lower()
            priority = any(kw in title_desc for kw in PRIORITY_KWS)

            items.append({
                "title": art.get("title", "No title"),
                "link": art.get("url", "#"),
                "source": art["source"].get("name", "NewsAPI"),
                "pub": pub,
                "category": "mixed",  # we'll assign later
                "priority": priority
            })
        return items
    except Exception as e:
        st.sidebar.warning(f"NewsAPI issue: {str(e)}. Using RSS fallback.")
        return []

# ────────────────────────────────────────────────────────────────
# RSS FETCH (your original)
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
                "priority": any(kw in title.lower() for kw in PRIORITY_KWS)
            })
    except:
        pass
    return items

@st.cache_data(ttl=900, show_spinner=False)
def load_all_news():
    api_items = fetch_news_api(news_api_key)
    rss_items = []
    with ThreadPoolExecutor(max_workers=12) as ex:
        futures = [ex.submit(fetch_feed, s, u, c) for s, u, c in RSS_FEEDS]
        for f in as_completed(futures):
            rss_items.extend(f.result())

    all_news = api_items + rss_items
    all_news.sort(key=lambda x: (not x["priority"], x["pub"]), reverse=True)

    # Group by category (NewsAPI items go to 'mixed' → distribute)
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
# LOADING + HEADER + HERO (unchanged)
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
    <p class="subtitle">AI Powered Real-time Competitive Intelligence Dashboard</p>
</div>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────────────────────
# NEWS GRID (now with API priority)
# ────────────────────────────────────────────────────────────────
with st.spinner("Scanning NewsAPI + RSS for latest signals..."):
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
            st.markdown('<div style="text-align:center; color:#94a3b8; padding:40px;">No recent signals...</div>', unsafe_allow_html=True)
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
    <strong>Priority:</strong> Evergent / NBA / Netcracker / Amdocs / NEC / CSG / Sony OTT<br>
    <strong>Live:</strong> NewsAPI + RSS • Auto-refresh every 5 min • Powered by Srinivasa Dasu @saptechsrini
</div>
""", unsafe_allow_html=True)

keep_alive()
