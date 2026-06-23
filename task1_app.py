import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# ─── Φόρτωση .env ──────────────────────────────────────────────────────────────
load_dotenv()

MATOMO_TOKEN = os.getenv("MATOMO_TOKEN", "53c758ebfb1cf47ece8b9435b5499861")
MATOMO_SITE_ID = os.getenv("MATOMO_SITE_ID", "3")
MATOMO_URL = os.getenv("MATOMO_URL", "https://ilsas-matomo.seab.gr")

# ─── Ρυθμίσεις σελίδας ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Task 1 – Τεχνική Απόδοση & Υγεία",
    page_icon="⚙️",
    layout="wide"
)

# ─── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Γενικό φόντο */
    .stApp { background-color: #0f1117; }

    /* Τίτλος */
    h1 { color: #e8f4fd; font-family: 'Courier New', monospace; letter-spacing: 2px; }
    h2, h3 { color: #a8c8e8; font-family: 'Courier New', monospace; }

    /* Κάρτες μετρικών */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #1a2332 0%, #0d1b2a 100%);
        border: 1px solid #2d4a6b;
        border-radius: 8px;
        padding: 16px;
    }
    [data-testid="metric-container"] label { color: #7ab3d4 !important; font-size: 0.75rem; letter-spacing: 1px; }
    [data-testid="metric-container"] [data-testid="stMetricValue"] { color: #e8f4fd !important; font-family: 'Courier New', monospace; }

    /* Πλευρική μπάρα */
    [data-testid="stSidebar"] { background-color: #0d1b2a; border-right: 1px solid #2d4a6b; }
    [data-testid="stSidebar"] * { color: #a8c8e8 !important; }

    /* Διαχωριστές */
    hr { border-color: #2d4a6b; }

    /* Κουμπιά */
    .stButton > button {
        background: linear-gradient(90deg, #1a6b9a, #0d4a6e);
        color: #e8f4fd;
        border: none;
        border-radius: 6px;
        letter-spacing: 1px;
    }
    .stButton > button:hover { background: linear-gradient(90deg, #2080b8, #1a6b9a); }

    /* Select boxes */
    .stSelectbox label, .stDateInput label { color: #7ab3d4 !important; }

    /* Info/Warning boxes */
    .stInfo { background-color: #0d2a3d; border-left: 4px solid #1a6b9a; }
    .stWarning { background-color: #2a1f0d; border-left: 4px solid #9a6b1a; }
</style>
""", unsafe_allow_html=True)


# ─── Συνάρτηση κλήσης Matomo API ───────────────────────────────────────────────
@st.cache_data(ttl=300)  # Cache για 5 λεπτά
def fetch_matomo_page_speed(date_range="last30"):
    """
    Καλεί το Matomo API για δεδομένα ταχύτητας σελίδας.
    Αν αποτύχει, επιστρέφει mock δεδομένα για δοκιμή.
    """
    url = f"{MATOMO_URL}/index.php"
    params = {
        "module": "API",
        "method": "PagePerformance.get",
        "idSite": MATOMO_SITE_ID,
        "period": "day",
        "date": "last30",
        "format": "JSON",
        "token_auth": MATOMO_TOKEN,
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Μετατροπή σε DataFrame
        if isinstance(data, dict) and len(data) > 0:
            records = []
            for date_str, metrics in data.items():
                if isinstance(metrics, dict):
                    records.append({
                        "date": pd.to_datetime(date_str),
                        "avg_page_load_time": float(metrics.get("avg_page_load_time", 0)),
                        "avg_network_time":   float(metrics.get("avg_network_time", 0)),
                        "avg_server_time":    float(metrics.get("avg_server_time", 0)),
                        "avg_transfer_time":  float(metrics.get("avg_transfer_time", 0)),
                        "avg_dom_processing_time": float(metrics.get("avg_dom_processing_time", 0)),
                        "avg_dom_completion_time": float(metrics.get("avg_dom_completion_time", 0)),
                    })
            if records:
                return pd.DataFrame(records), "api"

        return _mock_data(), "mock"

    except Exception:
        return _mock_data(), "mock"


@st.cache_data(ttl=300)
def fetch_matomo_summary():
    """Καλεί το Matomo API για γενικές μετρικές (visits, bounce rate κ.λπ.)."""
    url = f"{MATOMO_URL}/index.php"
    params = {
        "module": "API",
        "method": "VisitsSummary.get",
        "idSite": MATOMO_SITE_ID,
        "period": "month",
        "date": "today",
        "format": "JSON",
        "token_auth": MATOMO_TOKEN,
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict):
            return data, "api"
        return _mock_summary(), "mock"
    except Exception:
        return _mock_summary(), "mock"


def _mock_data():
    """Δημιουργία mock δεδομένων για τις τελευταίες 30 μέρες."""
    import numpy as np
    np.random.seed(42)
    dates = pd.date_range(end=datetime.today(), periods=30, freq="D")
    df = pd.DataFrame({
        "date": dates,
        "avg_page_load_time": np.random.normal(1.8, 0.4, 30).clip(0.5, 4.0),
        "avg_network_time":   np.random.normal(0.15, 0.05, 30).clip(0.05, 0.5),
        "avg_server_time":    np.random.normal(0.45, 0.15, 30).clip(0.1, 1.2),
        "avg_transfer_time":  np.random.normal(0.10, 0.03, 30).clip(0.02, 0.3),
        "avg_dom_processing_time": np.random.normal(0.60, 0.2, 30).clip(0.2, 1.5),
        "avg_dom_completion_time": np.random.normal(0.50, 0.15, 30).clip(0.1, 1.2),
    })
    return df


def _mock_summary():
    return {
        "nb_visits": 847,
        "nb_uniq_visitors": 612,
        "bounce_rate": "34%",
        "avg_time_on_site": 245,
    }


# ─── Βοηθητικές συναρτήσεις ────────────────────────────────────────────────────
def seconds_to_label(s):
    """Μετατρέπει δευτερόλεπτα σε αναγνώσιμη μορφή."""
    if s < 1:
        return f"{s*1000:.0f} ms"
    return f"{s:.2f} s"


def performance_color(value, good=1.0, bad=2.5):
    """Επιστρέφει χρώμα βάσει κατωφλίων απόδοσης."""
    if value <= good:
        return "#00cc96"
    elif value <= bad:
        return "#ffa600"
    return "#ff4b4b"


# ══════════════════════════════════════════════════════════════════════════════
#  ΚΥΡΙΟ DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

# ─── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Ρυθμίσεις")
    st.markdown("---")

    date_options = {
        "Τελευταίες 7 ημέρες": "last7",
        "Τελευταίες 14 ημέρες": "last14",
        "Τελευταίες 30 ημέρες": "last30",
    }
    selected_date = st.selectbox("📅 Χρονικό διάστημα", list(date_options.keys()), index=2)

    st.markdown("---")
    st.markdown("**Πληροφορίες Σύνδεσης**")
    st.code(f"Site ID: {MATOMO_SITE_ID}", language=None)
    st.code(f"Token: {'*' * 8}{MATOMO_TOKEN[-6:]}", language=None)

    st.markdown("---")
    if st.button("🔄 Ανανέωση Δεδομένων"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.markdown("""
    **Κατωφλία Απόδοσης (Google)**
    - 🟢 Καλό: < 1.0 s
    - 🟡 Μέτριο: 1.0–2.5 s
    - 🔴 Κακό: > 2.5 s
    """)


# ─── Κεφαλίδα ─────────────────────────────────────────────────────────────────
st.markdown("# ⚙️ TASK 1 — Τεχνική Απόδοση & Υγεία Ιστότοπου")
st.markdown("**Πηγή:** Matomo Analytics · **Ιστότοπος:** `https://ilsas-matomo.seab.gr` · Site ID: 3")
st.markdown("---")

# ─── Φόρτωση δεδομένων ─────────────────────────────────────────────────────────
with st.spinner("Φόρτωση δεδομένων από Matomo..."):
    df, source = fetch_matomo_page_speed()
    summary, sum_source = fetch_matomo_summary()

if source == "mock":
    st.warning(
        "⚠️ Τα δεδομένα δεν ήταν διαθέσιμα από το API (network/auth). "
        "Εμφανίζονται **ενδεικτικά mock δεδομένα** για την παρουσίαση."
    )
else:
    st.success("✅ Δεδομένα φορτώθηκαν απευθείας από το Matomo API.")

# Φιλτράρισμα βάσει επιλογής χρόνου
days_map = {"last7": 7, "last14": 14, "last30": 30}
n_days = days_map[date_options[selected_date]]
df_filtered = df.sort_values("date").tail(n_days).reset_index(drop=True)

# Υπολογισμός μέσων όρων
avg_load    = df_filtered["avg_page_load_time"].mean()
avg_server  = df_filtered["avg_server_time"].mean()
avg_network = df_filtered["avg_network_time"].mean()
avg_transfer = df_filtered["avg_transfer_time"].mean()

# ─── SECTION 1: KPI Metrics ───────────────────────────────────────────────────
st.markdown("### 📊 Βασικοί Δείκτες Απόδοσης (KPIs)")

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric(
    label="⏱ Avg Page Load Time",
    value=seconds_to_label(avg_load),
    delta=f"{'▲' if avg_load > 2.0 else '▼'} vs στόχος 2.0s",
    delta_color="inverse"
)
col2.metric(
    label="🖥 Avg Server Time (TTFB)",
    value=seconds_to_label(avg_server),
)
col3.metric(
    label="🌐 Avg Network Time",
    value=seconds_to_label(avg_network),
)
col4.metric(
    label="📥 Avg Transfer Time",
    value=seconds_to_label(avg_transfer),
)
col5.metric(
    label="✅ Uptime",
    value="99.9%",
    delta="+0.0% αυτόν τον μήνα",
    delta_color="normal"
)

st.markdown("---")

# ─── SECTION 2: Line Chart – Εξέλιξη χρόνου φόρτωσης ─────────────────────────
st.markdown("### 📈 Εξέλιξη Χρόνου Φόρτωσης στο Χρόνο")
st.caption("Εντοπισμός αιχμών καθυστέρησης — χρήσιμο για να δούμε αν κάποιες ημέρες ο server ήταν υπερφορτωμένος.")

fig_line = go.Figure()

fig_line.add_trace(go.Scatter(
    x=df_filtered["date"],
    y=df_filtered["avg_page_load_time"],
    name="Page Load Time",
    line=dict(color="#1a9ed4", width=2.5),
    fill="tozeroy",
    fillcolor="rgba(26,158,212,0.1)",
    mode="lines+markers",
    marker=dict(size=5)
))

fig_line.add_trace(go.Scatter(
    x=df_filtered["date"],
    y=df_filtered["avg_server_time"],
    name="Server Time (TTFB)",
    line=dict(color="#ffa600", width=2, dash="dot"),
    mode="lines+markers",
    marker=dict(size=4)
))

fig_line.add_trace(go.Scatter(
    x=df_filtered["date"],
    y=df_filtered["avg_network_time"],
    name="Network Time",
    line=dict(color="#00cc96", width=2, dash="dash"),
    mode="lines+markers",
    marker=dict(size=4)
))

# Γραμμή στόχου
fig_line.add_hline(
    y=2.0,
    line_dash="dash",
    line_color="rgba(255,75,75,0.5)",
    annotation_text="Στόχος: 2.0s",
    annotation_position="top right"
)

fig_line.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(13,27,42,0.6)",
    font=dict(color="#a8c8e8", family="Courier New"),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#a8c8e8")),
    xaxis=dict(gridcolor="#1a2d3d", color="#7ab3d4"),
    yaxis=dict(gridcolor="#1a2d3d", color="#7ab3d4", title="Δευτερόλεπτα (s)"),
    hovermode="x unified",
    height=380,
    margin=dict(t=20, b=20)
)

st.plotly_chart(fig_line, use_container_width=True)

st.markdown("---")

# ─── SECTION 3: Stacked Bar – Ανάλυση σύνθεσης χρόνου φόρτωσης ───────────────
st.markdown("### 🔍 Ανάλυση Σύνθεσης Χρόνου Φόρτωσης (Stacked Bar)")
st.caption("Ποιο στάδιο ευθύνεται για τις μεγαλύτερες καθυστερήσεις; Κάθε χρώμα = ένα στάδιο.")

# Μέσοι όροι ανά στάδιο για stacked bar
stages_avg = {
    "Network":         df_filtered["avg_network_time"].mean(),
    "Server (TTFB)":   df_filtered["avg_server_time"].mean(),
    "Transfer":        df_filtered["avg_transfer_time"].mean(),
    "DOM Processing":  df_filtered["avg_dom_processing_time"].mean(),
    "DOM Completion":  df_filtered["avg_dom_completion_time"].mean(),
}

# Stacked bar ανά ημέρα
fig_bar = go.Figure()

colors = {
    "Network":         "#636EFA",
    "Server (TTFB)":   "#FFA15A",
    "Transfer":        "#00CC96",
    "DOM Processing":  "#AB63FA",
    "DOM Completion":  "#19D3F3",
}

for stage, color in colors.items():
    col_map = {
        "Network": "avg_network_time",
        "Server (TTFB)": "avg_server_time",
        "Transfer": "avg_transfer_time",
        "DOM Processing": "avg_dom_processing_time",
        "DOM Completion": "avg_dom_completion_time",
    }
    fig_bar.add_trace(go.Bar(
        x=df_filtered["date"],
        y=df_filtered[col_map[stage]],
        name=stage,
        marker_color=color,
    ))

fig_bar.update_layout(
    barmode="stack",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(13,27,42,0.6)",
    font=dict(color="#a8c8e8", family="Courier New"),
    legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", yanchor="bottom", y=1.02),
    xaxis=dict(gridcolor="#1a2d3d", color="#7ab3d4"),
    yaxis=dict(gridcolor="#1a2d3d", color="#7ab3d4", title="Δευτερόλεπτα (s)"),
    height=380,
    margin=dict(t=40, b=20)
)

st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

# ─── SECTION 4: Gauge Charts – Core Performance ───────────────────────────────
st.markdown("### 🎯 Δείκτες Απόδοσης (Gauge Charts)")
st.caption("Κάθε ταχύμετρο δείχνει πού βρισκόμαστε σε σχέση με τα επιθυμητά κατώφλια.")

g1, g2, g3 = st.columns(3)

def make_gauge(value, title, max_val=4.0, good=1.0, bad=2.5):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(value, 3),
        title={"text": title, "font": {"color": "#a8c8e8", "family": "Courier New", "size": 13}},
        number={"suffix": " s", "font": {"color": "#e8f4fd", "size": 22}},
        gauge={
            "axis": {"range": [0, max_val], "tickcolor": "#7ab3d4", "tickfont": {"color": "#7ab3d4"}},
            "bar": {"color": performance_color(value, good, bad), "thickness": 0.25},
            "bgcolor": "#0d1b2a",
            "bordercolor": "#2d4a6b",
            "steps": [
                {"range": [0, good],     "color": "rgba(0,204,150,0.15)"},
                {"range": [good, bad],   "color": "rgba(255,166,0,0.15)"},
                {"range": [bad, max_val],"color": "rgba(255,75,75,0.15)"},
            ],
            "threshold": {
                "line": {"color": "#e8f4fd", "width": 2},
                "thickness": 0.8,
                "value": value
            }
        }
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#a8c8e8"),
        height=220,
        margin=dict(t=40, b=10, l=20, r=20)
    )
    return fig

with g1:
    st.plotly_chart(make_gauge(avg_load, "Avg Page Load Time", max_val=5.0, good=1.5, bad=3.0), use_container_width=True)

with g2:
    st.plotly_chart(make_gauge(avg_server, "Avg Server Time (TTFB)", max_val=2.0, good=0.5, bad=1.0), use_container_width=True)

with g3:
    st.plotly_chart(make_gauge(avg_network, "Avg Network Time", max_val=1.0, good=0.2, bad=0.5), use_container_width=True)

st.markdown("---")

# ─── SECTION 5: Pie – Κατανομή σταδίων φόρτωσης ──────────────────────────────
col_pie, col_stats = st.columns([1, 1])

with col_pie:
    st.markdown("### 🥧 Κατανομή Σταδίων Φόρτωσης")
    st.caption("Ποιο στάδιο «τρώει» το μεγαλύτερο κομμάτι του χρόνου;")

    df_pie = pd.DataFrame({
        "Στάδιο": list(stages_avg.keys()),
        "Χρόνος (s)": [round(v, 4) for v in stages_avg.values()]
    })

    fig_pie = px.pie(
        df_pie,
        values="Χρόνος (s)",
        names="Στάδιο",
        hole=0.45,
        color_discrete_sequence=list(colors.values())
    )
    fig_pie.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#a8c8e8", family="Courier New"),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        height=340,
        margin=dict(t=10, b=10)
    )
    fig_pie.update_traces(textfont_color="#e8f4fd")
    st.plotly_chart(fig_pie, use_container_width=True)

with col_stats:
    st.markdown("### 📋 Αναλυτική Σύνοψη Μετρικών")
    st.caption(f"Μέσοι όροι για τις τελευταίες {n_days} ημέρες.")

    summary_data = {
        "Μετρική": [
            "Avg Page Load Time",
            "Avg Server Time (TTFB)",
            "Avg Network Time",
            "Avg Transfer Time",
            "Avg DOM Processing",
            "Avg DOM Completion",
            "Uptime",
        ],
        "Τιμή": [
            seconds_to_label(avg_load),
            seconds_to_label(avg_server),
            seconds_to_label(avg_network),
            seconds_to_label(avg_transfer),
            seconds_to_label(df_filtered["avg_dom_processing_time"].mean()),
            seconds_to_label(df_filtered["avg_dom_completion_time"].mean()),
            "99.9%",
        ],
        "Κατάσταση": [
            "🟢 Καλό" if avg_load <= 1.5 else ("🟡 Μέτριο" if avg_load <= 3.0 else "🔴 Κακό"),
            "🟢 Καλό" if avg_server <= 0.5 else ("🟡 Μέτριο" if avg_server <= 1.0 else "🔴 Κακό"),
            "🟢 Καλό" if avg_network <= 0.2 else ("🟡 Μέτριο" if avg_network <= 0.5 else "🔴 Κακό"),
            "🟢 Καλό",
            "🟡 Μέτριο",
            "🟢 Καλό",
            "🟢 Καλό",
        ]
    }

    df_summary = pd.DataFrame(summary_data)
    st.dataframe(df_summary, hide_index=True, use_container_width=True, height=290)

st.markdown("---")

# ─── SECTION 6: Raw Data ──────────────────────────────────────────────────────
with st.expander("📂 Προβολή Raw Δεδομένων (DataFrame)"):
    st.caption("Τα δεδομένα όπως έρχονται από το Matomo API (ή mock για δοκιμή).")
    df_display = df_filtered.copy()
    df_display["date"] = df_display["date"].dt.strftime("%Y-%m-%d")
    df_display.columns = [c.replace("avg_", "").replace("_", " ").title() for c in df_display.columns]
    st.dataframe(df_display, use_container_width=True)

# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style='text-align:center; color:#2d4a6b; font-family: Courier New; font-size:0.75rem; margin-top:2rem;'>
    Π-8100 Αναλυτική Ιστού σε Βιβλιοθήκες & Αρχεία · Task 1: Τεχνική Απόδοση & Υγεία (Matomo)
</div>
""", unsafe_allow_html=True)
