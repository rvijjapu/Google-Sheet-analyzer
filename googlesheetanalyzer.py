import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Daily OTT Insights", page_icon="📡", layout="wide")

# Light theme (same as before)
st.markdown("""
    <style>
    :root { --bg: #f9fafb; --surface: #ffffff; --text: #111827; --text-muted: #6b7280; --primary: #2563eb; --border: #e5e7eb; }
    .stApp { background-color: var(--bg); }
    h1 { text-align: center; color: var(--text); }
    .subtitle { text-align: center; color: var(--text-muted); }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>Daily OTT Insights</h1>", unsafe_allow_html=True)
st.markdown('<p class="subtitle">Telecom OTT news, trends & alerts – updated daily for the team</p>', unsafe_allow_html=True)

# Try to get API key from Streamlit secrets first (safer)
try:
    api_key = st.secrets["news_api_key"]
except:
    api_key = None

# Fallback: sidebar input if no secret
if not api_key:
    st.sidebar.header("NewsAPI Key")
    api_key = st.sidebar.text_input("Enter your NewsAPI key", type="password", help="Get free from https://newsapi.org")
    if not api_key:
        st.info("Enter your NewsAPI key in the sidebar to fetch the latest telecom OTT news.")
        st.stop()

# Fetch function with error handling
@st.cache_data(ttl=3600, show_spinner="Fetching latest news...")
def fetch_ott_news(key):
    url = f"https://newsapi.org/v2/everything?q=(telecom+OR+5G)+OTT+OR+streaming+OR+VoD+OR+VoIP&language=en&sortBy=publishedAt&pageSize=12&apiKey={key}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        articles = response.json().get("articles", [])
        if not articles:
            st.warning("No articles found – try a different query or check quota.")
            return pd.DataFrame()
        df = pd.DataFrame(articles)
        df = df[["publishedAt", "title", "description", "url", "source"]]
        df["publishedAt"] = pd.to_datetime(df["publishedAt"]).dt.strftime("%d %b %Y %H:%M")
        df["source"] = df["source"].apply(lambda x: x["name"] if isinstance(x, dict) else x)
        return df
    except Exception as e:
        st.error(f"Error fetching news: {str(e)}. Check key, quota, or internet.")
        return pd.DataFrame()

news_df = fetch_ott_news(api_key)

# Display news
st.subheader("Latest Telecom & OTT News")
if not news_df.empty:
    for _, row in news_df.iterrows():
        with st.container(border=True):
            st.markdown(f"**{row['title']}**")
            st.caption(f"{row['source']} • {row['publishedAt']}")
            st.write(row['description'] or "No description available.")
            st.markdown(f"[Read full article →]({row['url']})")
else:
    st.info("No recent news loaded. Regenerate your key at newsapi.org if quota is exceeded.")

# Sample trend chart (static for now – can connect to real API later)
st.subheader("OTT Market Snapshot (Sample)")
trend_data = pd.DataFrame({
    "Date": ["20-Jan-26", "21-Jan-26", "22-Jan-26", "23-Jan-26", "24-Jan-26", "25-Jan-26", "26-Jan-26", "27-Jan-26"],
    "Global OTT Revenue (Billion USD)": [651.43, 670.17, 678.62, 693.44, 708.29, 725.01, 740.12, 755.90]
})
fig = px.line(trend_data, x="Date", y="Global OTT Revenue (Billion USD)", title="OTT Revenue Trend")
st.plotly_chart(fig, use_container_width=True)

st.caption("Powered by NewsAPI • For telecom & OTT teams • Regenerate key if expired")
