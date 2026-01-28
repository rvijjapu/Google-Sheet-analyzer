import streamlit as st
import pandas as pd
import plotly.express as px
from st_gsheets_connection import GSheetsConnection

# ────────────────────────────────────────────────────────────────
# Page configuration
# ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sheet Intel",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Light modern professional styling
st.markdown("""
    <style>
    :root {
        --bg: #f9fafb;
        --surface: #ffffff;
        --text: #111827;
        --text-muted: #6b7280;
        --primary: #2563eb;
        --primary-light: #60a5fa;
        --border: #e5e7eb;
        --shadow-sm: 0 1px 3px rgba(0,0,0,0.1);
        --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
    }

    .stApp {
        background-color: var(--bg);
    }

    .block-container {
        padding-top: 2rem !important;
        max-width: 1400px !important;
    }

    h1 {
        color: var(--text);
        font-weight: 600;
        letter-spacing: -0.025em;
        text-align: center;
        margin-bottom: 0.5rem !important;
    }

    .subtitle {
        text-align: center;
        color: var(--text-muted);
        font-size: 1.125rem;
        margin-bottom: 2rem !important;
    }

    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 1px solid var(--border);
        padding: 0.75rem 1rem;
        background: white;
    }

    .stRadio > div {
        flex-direction: row;
        gap: 1.25rem;
        justify-content: center;
    }

    .stRadio > div > label {
        background: white;
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        transition: all 0.15s;
    }

    .stRadio > div > label:hover,
    .stRadio > div > label[data-checked="true"] {
        border-color: var(--primary);
        color: var(--primary);
        box-shadow: 0 0 0 3px rgba(37,99,235,0.1);
    }

    [data-testid="stMetric"] {
        background: white;
        border-radius: 12px;
        border: 1px solid var(--border);
        box-shadow: var(--shadow-sm);
        padding: 1.25rem 1rem;
    }

    hr {
        border-color: var(--border) !important;
        margin: 2.5rem 0 1.5rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────────────────────
# Header
# ────────────────────────────────────────────────────────────────
st.markdown("<h1>Sheet Intel</h1>", unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">Smart analysis of any public Google Sheet – fast, clean, insightful</p>',
    unsafe_allow_html=True
)

# ────────────────────────────────────────────────────────────────
# Main input
# ────────────────────────────────────────────────────────────────
sheet_url = st.text_input(
    label="Google Sheet URL",
    placeholder="https://docs.google.com/spreadsheets/d/.../edit?usp=sharing",
    help="The sheet must be shared publicly → Anyone with the link → Viewer",
    label_visibility="collapsed"
)

view_mode = st.radio(
    label="View",
    options=["Summary", "Charts", "Combined"],
    horizontal=True,
    label_visibility="collapsed"
)

if not sheet_url:
    st.markdown(
        """
        <div style="text-align:center; padding: 5rem 1rem; color: var(--text-muted);">
            Paste a publicly shared Google Sheet URL to start<br>
            <small>No login • No installation • Instant results</small>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.stop()

# ────────────────────────────────────────────────────────────────
# Load & clean data
# ────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading and preparing data...")
def load_sheet(url):
    conn = st.connection("gsheet", type=GSheetsConnection, url=url, ttl="10m")
    worksheets = conn.worksheets()
    selected = st.selectbox("Worksheet", worksheets, index=0)

    df_raw = conn.read(worksheet=selected)
    df = df_raw.dropna(how='all').fillna('').copy()

    # Clean column names
    df.columns = (
        df.columns.astype(str).str.strip().str.lower()
        .str.replace(r'[^a-z0-9_]', '_', regex=True)
        .str.replace(r'_+', '_', regex=True)
        .str.strip('_')
    )

    return df, selected

try:
    df, ws_name = load_sheet(sheet_url)
except Exception:
    st.error("Could not load the sheet. Please make sure it is shared publicly (Anyone with the link → Viewer).")
    st.stop()

# ────────────────────────────────────────────────────────────────
# Column detection
# ────────────────────────────────────────────────────────────────
def find_col(keywords):
    for col in df.columns:
        if any(k.lower() in col for k in keywords):
            return col
    return None

status_col  = find_col(["status", "state", "stage", "phase"])
progress_col = find_col(["percent", "%", "complete", "progress", "done"])
due_col     = find_col(["due", "deadline", "target", "end", "finish"])

# ────────────────────────────────────────────────────────────────
# Prepare metrics & charts
# ────────────────────────────────────────────────────────────────
metrics = {}
charts = {}

if status_col:
    valid_status = df[status_col][df[status_col].str.strip() != '']
    if not valid_status.empty:
        counts = valid_status.value_counts()
        metrics["status"] = counts

        charts["pie"] = px.pie(
            values=counts.values,
            names=counts.index,
            title="Status Distribution",
            hole=0.35,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )

        charts["bar"] = px.bar(
            x=counts.index,
            y=counts.values,
            title="Status Counts",
            text_auto=True,
            color=counts.index,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )

if progress_col:
    try:
        cleaned = df[progress_col].astype(str).str.replace(r'[% ]', '', regex=True).replace('', '0')
        numeric = pd.to_numeric(cleaned, errors='coerce').clip(0, 100)
        avg = numeric.mean()
        if not pd.isna(avg):
            metrics["progress"] = round(avg, 1)
    except:
        pass

# ────────────────────────────────────────────────────────────────
# Dashboard layout
# ────────────────────────────────────────────────────────────────
st.markdown("---")

if view_mode in ["Summary", "Combined"]:
    st.subheader("Key Insights")

    cols = st.columns(4)

    cols[0].metric("Total Rows", len(df))

    if "status" in metrics:
        total_valid = len(df[df[status_col].str.strip() != ''])
        if total_valid > 0:
            completed = metrics["status"].get("completed", 0) + metrics["status"].get("done", 0)
            pct = round(completed / total_valid * 100, 1)
            cols[1].metric("Est. Completion", f"{pct}%")

    if "progress" in metrics:
        cols[2].metric("Avg Progress", f"{metrics['progress']}%")

    if "status" in metrics:
        st.markdown("**Status breakdown**")
        st.dataframe(
            metrics["status"].reset_index(name="Count"),
            column_config={"index": "Status"},
            use_container_width=True,
            hide_index=True
        )

if view_mode in ["Charts", "Combined"]:
    st.subheader("Visuals")

    if "pie" in charts:
        st.plotly_chart(charts["pie"], use_container_width=True)

    if "bar" in charts:
        st.plotly_chart(charts["bar"], use_container_width=True)

# ────────────────────────────────────────────────────────────────
# Footer / preview
# ────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)

with st.expander("Data Preview (cleaned – first 12 rows)"):
    st.dataframe(df.head(12), use_container_width=True)

st.markdown(
    "<p style='text-align:center; color:#6b7280; font-size:0.9rem; margin-top:3rem;'>"
    "Sheet Intel • Public Google Sheets only • No login required</p>",
    unsafe_allow_html=True
)
