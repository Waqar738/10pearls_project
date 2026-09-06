"""
Bara Khyber AQI Forecast — Production Dashboard
Author: Muhammad Waqar | 10 Pearls Shine Internship, Cohort 9
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Bara Khyber AQI Forecast | Muhammad Waqar",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# CONSTANTS
# ============================================================

BASE_URL = "https://aqi-predictor-karachi-production.up.railway.app"
WAQI_TOKEN = "593d56f2c0edba0cb9ccd27eac295534c4206b65"
BARA_KHYBER_LAT, BARA_KHYBER_LON = 33.9167, 71.4500

# Single source of truth for AQI bands — used by gauges, badges, and advisory text.
# (lo, hi, label, css_slug, hex_color)
AQI_BANDS = [
    (0, 50, "Good", "good", "#00e396"),
    (51, 100, "Moderate", "moderate", "#ffd54f"),
    (101, 150, "Unhealthy (Sensitive)", "unhealthy", "#ff9900"),
    (151, 200, "Unhealthy", "unhealthy", "#ff3333"),
    (201, 300, "Hazardous", "hazardous", "#c44dff"),
    (301, 999, "Hazardous", "hazardous", "#8b0000"),
]

ADVISORY_TEXT = {
    "good": ("🟢 Good Air Quality", "Air quality is satisfactory — enjoy outdoor activities and open your windows for fresh air."),
    "moderate": ("🟡 Moderate Air Quality", "Unusually sensitive individuals should limit prolonged outdoor exposure. General public is safe."),
    "unhealthy": ("🟠 Unhealthy Air Quality", "Limit outdoor physical activity, keep windows closed, and sensitive groups should stay indoors."),
    "hazardous": ("🔴 Hazardous Air Quality", "Avoid all outdoor exposure, stay indoors with air purifiers, and wear an N95 mask if you must go out."),
}

# ============================================================
# STYLE — sky / cloud themed redesign
# ============================================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    h1, h2, h3, h4 { font-family: 'Sora', sans-serif !important; }

    /* ---------- Sky background with drifting clouds ---------- */
    .stApp {
        background: linear-gradient(180deg, #0d1b2e 0%, #10233d 30%, #0a1626 70%, #060c17 100%);
        color: #ffffff;
        overflow-x: hidden;
    }

    .cloud-layer {
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        pointer-events: none;
        z-index: 0;
        overflow: hidden;
    }
    .cloud {
        position: absolute;
        opacity: 0.10;
        filter: blur(1px);
        animation: drift linear infinite;
    }
    .cloud svg { width: 100%; height: 100%; fill: #ffffff; }
    .cloud.c1 { width: 340px; top: 6%;  left: -20%; animation-duration: 70s; opacity: 0.08; }
    .cloud.c2 { width: 220px; top: 22%; left: -25%; animation-duration: 50s; animation-delay: -10s; opacity: 0.10; }
    .cloud.c3 { width: 420px; top: 48%; left: -30%; animation-duration: 90s; animation-delay: -30s; opacity: 0.06; }
    .cloud.c4 { width: 260px; top: 68%; left: -20%; animation-duration: 60s; animation-delay: -5s; opacity: 0.08; }
    .cloud.c5 { width: 180px; top: 85%; left: -15%; animation-duration: 45s; animation-delay: -20s; opacity: 0.09; }
    @keyframes drift {
        from { transform: translateX(0); }
        to   { transform: translateX(140vw); }
    }

    .glow-orb {
        position: fixed; border-radius: 50%; filter: blur(90px); z-index: 0; pointer-events: none;
    }
    .glow-1 { width: 480px; height: 480px; background: rgba(0, 195, 255, 0.16); top: -140px; left: -120px; }
    .glow-2 { width: 420px; height: 420px; background: rgba(124, 58, 237, 0.14); bottom: -120px; right: -100px; }

    section.main > div { position: relative; z-index: 1; }

    /* ---------- Sidebar ---------- */
    section[data-testid="stSidebar"] {
        background: linear-gradient(200deg, #0b1524 0%, #060d18 100%);
        border-right: 1px solid rgba(255,255,255,0.06);
    }

    /* ---------- Hero banner ---------- */
    .hero-banner {
        position: relative;
        text-align: center;
        padding: 40px 24px 34px 24px;
        border-radius: 26px;
        margin: 6px 0 10px 0;
        background: linear-gradient(135deg, rgba(0,195,255,0.10), rgba(124,58,237,0.10) 60%, rgba(0,195,255,0.04));
        border: 1px solid rgba(255,255,255,0.10);
        overflow: hidden;
    }
    .hero-banner::before {
        content: "";
        position: absolute; inset: 0;
        background: radial-gradient(circle at 15% 20%, rgba(255,255,255,0.10), transparent 40%);
    }
    .hero-icon { font-size: 46px; margin-bottom: 6px; }
    .hero-title {
        font-size: 44px; font-weight: 800; margin: 4px 0 0 0; letter-spacing: -1px;
        background: linear-gradient(135deg, #ffffff 15%, #8fe3ff 55%, #c7a9ff 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .hero-sub { color: #a9b3c6; font-size: 16.5px; margin: 12px auto 0 auto; max-width: 660px; }
    .hero-meta {
        display: inline-flex; gap: 18px; margin-top: 20px; flex-wrap: wrap; justify-content: center;
    }
    .hero-chip {
        background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12);
        color: #cfd8e8; font-size: 12.5px; padding: 7px 16px; border-radius: 999px;
    }
    .hero-chip strong { color: #6dd3ff; }

    /* ---------- Cards ---------- */
    .glass-card {
        background: rgba(255,255,255,0.035);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.09);
        border-radius: 20px;
        padding: 24px;
        margin: 8px 0;
        box-shadow: 0 10px 34px rgba(0, 0, 0, 0.35);
        transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
    }
    .glass-card:hover {
        transform: translateY(-3px);
        border-color: rgba(0, 195, 255, 0.30);
        box-shadow: 0 18px 45px rgba(0, 195, 255, 0.10);
    }

    .gradient-text {
        background: linear-gradient(135deg, #00c3ff 0%, #7c3aed 60%, #d68bff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
    }

    h1, h2, h3, h4 { color: #ffffff !important; font-weight: 700 !important; letter-spacing: -0.02em; }
    p, span, label { color: #c7ced9; }

    /* ---------- Metric boxes ---------- */
    .metric-box {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 18px;
        padding: 22px 18px;
        text-align: center;
        height: 100%;
        transition: border-color 0.25s ease, transform 0.25s ease;
    }
    .metric-box:hover { border-color: rgba(0, 195, 255, 0.3); transform: translateY(-2px); }
    .metric-value {
        font-size: 30px; font-weight: 800;
        background: linear-gradient(135deg, #00c3ff, #7c3aed);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .metric-label {
        color: #8b93a7; font-size: 12px; margin-top: 6px;
        letter-spacing: 0.08em; text-transform: uppercase; font-weight: 600;
    }

    /* ---------- Badges ---------- */
    .badge {
        padding: 6px 18px; border-radius: 999px; font-size: 12.5px; font-weight: 700;
        display: inline-block; letter-spacing: 0.03em;
    }
    .badge-good        { background: rgba(0, 227, 150, 0.15); color: #00e396; border: 1px solid rgba(0, 227, 150, 0.35); }
    .badge-moderate     { background: rgba(255, 213, 79, 0.15); color: #ffd54f; border: 1px solid rgba(255, 213, 79, 0.35); }
    .badge-unhealthy    { background: rgba(255, 153, 0, 0.15); color: #ff9900; border: 1px solid rgba(255, 153, 0, 0.35); }
    .badge-hazardous    { background: rgba(196, 77, 255, 0.15); color: #c44dff; border: 1px solid rgba(196, 77, 255, 0.35); }

    .divider {
        border: none; height: 1px;
        background: linear-gradient(to right, transparent, rgba(255,255,255,0.14), transparent);
        margin: 36px 0;
    }

    .section-tag {
        display: inline-block; background: rgba(109, 211, 255, 0.12); color: #6dd3ff;
        border: 1px solid rgba(109, 211, 255, 0.28); border-radius: 8px; padding: 4px 12px;
        font-size: 11.5px; font-weight: 700; letter-spacing: 0.09em; text-transform: uppercase;
        margin-bottom: 8px;
    }

    /* ---------- Footer ---------- */
    .footer-wrap {
        margin-top: 44px;
        border-radius: 22px;
        padding: 30px 24px 22px 24px;
        background: linear-gradient(135deg, rgba(0,195,255,0.06), rgba(124,58,237,0.06));
        border: 1px solid rgba(255,255,255,0.08);
        text-align: center;
    }
    .footer-wrap .foot-icon { font-size: 30px; margin-bottom: 8px; }
    .footer-wrap .foot-title { font-size: 16px; font-weight: 800; color: #ffffff; }
    .footer-wrap .foot-line { color: #9aa4b8; font-size: 13px; margin-top: 6px; }
    .footer-wrap .foot-line strong { color: #6dd3ff; }
    .footer-wrap .foot-tags {
        display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; margin-top: 16px;
    }
    .footer-wrap .foot-tag {
        background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.10);
        color: #8b93a7; font-size: 11px; padding: 5px 12px; border-radius: 999px;
    }
    .footer-wrap .foot-bottom {
        font-size: 11px; color: #4b5468; margin-top: 18px; padding-top: 14px;
        border-top: 1px solid rgba(255,255,255,0.06);
    }
    .footer-wrap a { color: #6dd3ff; text-decoration: none; font-weight: 600; }
    .footer-wrap a:hover { text-decoration: underline; }

    /* ---------- Buttons ---------- */
    .stButton > button {
        border-radius: 14px; font-weight: 700; transition: all 0.25s ease;
        background: linear-gradient(135deg, #00c3ff, #7c3aed); color: white; border: none;
        padding: 11px 24px; box-shadow: 0 6px 24px rgba(0, 195, 255, 0.22);
    }
    .stButton > button:hover { transform: scale(1.03); box-shadow: 0 10px 32px rgba(0, 195, 255, 0.32); }

    /* ---------- Status dots ---------- */
    .live-dot {
        display: inline-block; width: 9px; height: 9px; border-radius: 50%;
        background: #00e396; animation: pulse-dot 1.6s ease-in-out infinite; margin-right: 8px;
    }
    .dead-dot { display: inline-block; width: 9px; height: 9px; border-radius: 50%; background: #ff3333; margin-right: 8px; }
    @keyframes pulse-dot {
        0% { opacity: 1; box-shadow: 0 0 0 0 rgba(0,227,150,0.4); }
        70% { opacity: 0.75; box-shadow: 0 0 0 7px rgba(0,227,150,0); }
        100% { opacity: 1; box-shadow: 0 0 0 0 rgba(0,227,150,0); }
    }

    /* ---------- Advisory box ---------- */
    .advisory-box { border-radius: 18px; padding: 22px 26px; border-left: 4px solid; }
    .advisory-good        { background: rgba(0,227,150,0.07); border-color: #00e396; }
    .advisory-moderate     { background: rgba(255,213,79,0.07); border-color: #ffd54f; }
    .advisory-unhealthy    { background: rgba(255,153,0,0.07); border-color: #ff9900; }
    .advisory-hazardous    { background: rgba(196,77,255,0.07); border-color: #c44dff; }

    /* ---------- Sidebar blocks ---------- */
    .sb-header {
        text-align:center; padding: 22px 10px 18px 10px;
        border-bottom: 1px solid rgba(255,255,255,0.07);
        margin-bottom: 14px;
    }
    .sb-avatar {
        width: 64px; height: 64px; border-radius: 50%; margin: 0 auto 10px auto;
        display:flex; align-items:center; justify-content:center; font-size: 30px;
        background: linear-gradient(135deg, #00c3ff, #7c3aed);
        box-shadow: 0 6px 20px rgba(0,195,255,0.35);
    }
    .sb-block {
        background: rgba(255,255,255,0.035); border: 1px solid rgba(255,255,255,0.07);
        border-radius: 14px; padding: 13px 15px; margin: 6px 0;
    }
    .sidebar-profile {
        text-align:center; padding: 18px 12px; margin-top: 14px;
        background: linear-gradient(180deg, rgba(0,195,255,0.08), rgba(124,58,237,0.06));
        border: 1px solid rgba(255,255,255,0.09); border-radius: 18px;
    }

    /* Scrollbar polish */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 8px; }
    ::-webkit-scrollbar-track { background: transparent; }
</style>

<div class="glow-orb glow-1"></div>
<div class="glow-orb glow-2"></div>
<div class="cloud-layer">
    <div class="cloud c1"><svg viewBox="0 0 200 90" xmlns="http://www.w3.org/2000/svg"><path d="M40,70 a30,30 0 1,1 6,-58 a24,24 0 0,1 44,-4 a26,26 0 1,1 30,60 a20,20 0 0,1 -14,34 h-70 a24,24 0 0,1 4,-32z"/></svg></div>
    <div class="cloud c2"><svg viewBox="0 0 200 90" xmlns="http://www.w3.org/2000/svg"><path d="M40,70 a30,30 0 1,1 6,-58 a24,24 0 0,1 44,-4 a26,26 0 1,1 30,60 a20,20 0 0,1 -14,34 h-70 a24,24 0 0,1 4,-32z"/></svg></div>
    <div class="cloud c3"><svg viewBox="0 0 200 90" xmlns="http://www.w3.org/2000/svg"><path d="M40,70 a30,30 0 1,1 6,-58 a24,24 0 0,1 44,-4 a26,26 0 1,1 30,60 a20,20 0 0,1 -14,34 h-70 a24,24 0 0,1 4,-32z"/></svg></div>
    <div class="cloud c4"><svg viewBox="0 0 200 90" xmlns="http://www.w3.org/2000/svg"><path d="M40,70 a30,30 0 1,1 6,-58 a24,24 0 0,1 44,-4 a26,26 0 1,1 30,60 a20,20 0 0,1 -14,34 h-70 a24,24 0 0,1 4,-32z"/></svg></div>
    <div class="cloud c5"><svg viewBox="0 0 200 90" xmlns="http://www.w3.org/2000/svg"><path d="M40,70 a30,30 0 1,1 6,-58 a24,24 0 0,1 44,-4 a26,26 0 1,1 30,60 a20,20 0 0,1 -14,34 h-70 a24,24 0 0,1 4,-32z"/></svg></div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# DATA HELPERS
# ============================================================

@st.cache_data(ttl=300, show_spinner=False)
def fetch_data(endpoint: str):
    try:
        resp = requests.get(f"{BASE_URL}/{endpoint}", timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException:
        return None


@st.cache_data(ttl=300, show_spinner=False)
def fetch_current_aqi():
    try:
        resp = requests.get(
            f"https://api.waqi.info/feed/geo:{BARA_KHYBER_LAT};{BARA_KHYBER_LON}/?token={WAQI_TOKEN}",
            timeout=30,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "ok":
                return data["data"]
    except requests.exceptions.RequestException:
        pass
    return None


def aqi_lookup(value: float):
    """Returns (label, css_slug, hex_color) for a given AQI value."""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "Unknown", "moderate", "#8b93a7"
    for lo, hi, label, slug, color in AQI_BANDS:
        if lo <= value <= hi:
            return label, slug, color
    return "Hazardous", "hazardous", "#8b0000"


def badge_html(value):
    label, slug, _ = aqi_lookup(value)
    return f"<span class='badge badge-{slug}'>{label}</span>"


def create_gauge(value, title_html):
    label, slug, color = aqi_lookup(value)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=float(value),
        title={'text': title_html, 'font': {'size': 14, 'color': '#c7ced9'}},
        number={'font': {'size': 30, 'color': '#ffffff'}},
        gauge={
            'axis': {'range': [0, 300], 'tickwidth': 1, 'tickcolor': '#8b93a7', 'tickfont': {'size': 10, 'color': '#8b93a7'}},
            'bar': {'color': color, 'thickness': 0.25},
            'bgcolor': 'rgba(255,255,255,0.02)',
            'borderwidth': 0,
            'steps': [
                {'range': [0, 50], 'color': 'rgba(0, 227, 150, 0.10)'},
                {'range': [50, 100], 'color': 'rgba(255, 213, 79, 0.10)'},
                {'range': [100, 150], 'color': 'rgba(255, 153, 0, 0.10)'},
                {'range': [150, 200], 'color': 'rgba(255, 51, 51, 0.10)'},
                {'range': [200, 300], 'color': 'rgba(196, 77, 255, 0.10)'},
            ],
            'threshold': {'line': {'color': '#ffffff', 'width': 2}, 'thickness': 0.5, 'value': float(value)},
        }
    ))
    fig.update_layout(
        height=270,
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#e2e8f0',
        margin=dict(l=20, r=20, t=60, b=10),
    )
    return fig, label, slug, color


def create_feature_importance_chart(features_data):
    if not features_data or "features" not in features_data:
        return None
    df = pd.DataFrame(features_data["features"])
    df = df.sort_values("importance", ascending=True).tail(10)
    n = len(df)
    colors = ["#7c3aed" if i >= n - 2 else "#60a5fa" if i >= n - 5 else "#94a3b8" for i in range(n)]

    fig = go.Figure(go.Bar(
        x=df["importance"], y=df["feature"], orientation='h',
        marker_color=colors, text=df["importance"].round(3), textposition='outside',
        textfont=dict(color='#e2e8f0', size=11),
        hovertemplate='<b>%{y}</b><br>Importance: %{x:.4f}<extra></extra>',
    ))
    fig.update_layout(
        height=400,
        xaxis=dict(title="Importance Score", title_font=dict(color='#94a3b8'), tickfont=dict(color='#94a3b8'), gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(title=None, tickfont=dict(color='#e2e8f0'), gridcolor='rgba(255,255,255,0.05)'),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=60, t=20, b=20),
        hovermode='y',
    )
    return fig


def status_row(label, ok, sublabel=""):
    dot = "live-dot" if ok else "dead-dot"
    text = "Online" if ok else "Unreachable"
    color = "#00e396" if ok else "#ff3333"
    st.markdown(f"""
        <div class="glass-card" style="padding: 18px;">
            <div style="font-size: 12px; color: #8b93a7; font-weight:600; letter-spacing:0.04em; text-transform:uppercase;">{label}</div>
            <div style="display:flex; align-items:center; gap:8px; margin-top:8px;">
                <span class="{dot}"></span>
                <span style="color:{color}; font-weight:700;">{text}</span>
                <span style="margin-left:auto; font-size:11px; color:#5b6478;">{sublabel}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)


# ============================================================
# LOAD DATA
# ============================================================

with st.spinner("🔄 Connecting to inference backend..."):
    forecast_data = fetch_data("forecast")
    best_model_data = fetch_data("models/best")
    feature_importance_data = fetch_data("features/importance?horizon=1")
    current_aqi_data = fetch_current_aqi()

api_online = forecast_data is not None

# ============================================================
# SIDEBAR 
# ============================================================

with st.sidebar:
    st.markdown("""
        <div class="sb-header">
            <div class="sb-avatar">🌤️</div>
            <h2 style="margin:0; font-size:20px;">Bara Khyber AQI</h2>
            <p style="color:#8b93a7; font-size:12px; letter-spacing:0.06em; text-transform:uppercase; margin-top:2px;">Forecast Console · v2.1</p>
        </div>
    """, unsafe_allow_html=True)

    dot_class = "live-dot" if api_online else "dead-dot"
    status_text = "LIVE" if api_online else "OFFLINE"
    status_color = "#00e396" if api_online else "#ff3333"
    st.markdown(f"""
        <div class="sb-block">
            <div style="display:flex; align-items:center; gap:10px;">
                <span class="{dot_class}"></span>
                <span style="color:#8b93a7; font-size:14px;">Backend</span>
                <span style="margin-left:auto; color:{status_color}; font-size:12px; font-weight:700;">● {status_text}</span>
            </div>
            <div style="display:flex; justify-content:space-between; font-size:11px; color:#5b6478; margin-top:8px;">
                <span>Checked {datetime.now(ZoneInfo("Asia/Karachi").strftime('%H:%M')}</span>
                <span>Open-Meteo + AQICN</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("<hr class='divider' style='margin:16px 0;'>", unsafe_allow_html=True)
    st.markdown("#### 📊 Model Performance")
    performance_data = {
        "H1 (24h)": {"RMSE": 5.97, "R2": 0.843, "MAE": 4.59},
        "H2 (48h)": {"RMSE": 5.56, "R2": 0.862, "MAE": 4.15},
        "H3 (72h)": {"RMSE": 5.70, "R2": 0.855, "MAE": 4.34},
    }
    for horizon, metrics in performance_data.items():
        st.markdown(f"""
            <div class="sb-block">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="color:#8b93a7; font-size:13px; font-weight:600;">{horizon}</span>
                    <span style="color:#e2e8f0; font-size:13px; font-weight:600;">R² <span class="gradient-text">{metrics['R2']:.3f}</span></span>
                </div>
                <div style="display:flex; justify-content:space-between; font-size:11px; color:#5b6478; margin-top:4px;">
                    <span>RMSE: {metrics['RMSE']:.2f}</span>
                    <span>MAE: {metrics['MAE']:.2f}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr class='divider' style='margin:16px 0;'>", unsafe_allow_html=True)

    with st.expander("🧠 Features Used in Model", expanded=False):
        st.markdown("""
            <div style="font-size:13px; color:#8b93a7; line-height:2;">
                <b style="color:#e2e8f0;">🌤️ Pollutant Features</b><br>
                pm2_5, pm10, carbon_monoxide,<br>nitrogen_dioxide, sulphur_dioxide, ozone<br><br>
                <b style="color:#e2e8f0;">⏰ Time Features</b><br>
                hour, day, month<br><br>
                <b style="color:#e2e8f0;">🔄 Lag Features</b><br>
                lag_1 (1h), lag_3 (3h), lag_6 (6h)<br><br>
                <b style="color:#e2e8f0;">📊 Rolling Statistics</b><br>
                roll_mean_6, roll_mean_12<br><br>
                <b style="color:#e2e8f0;">🎯 Target</b><br>
                aqi_pm25 (PM2.5 concentration)
            </div>
        """, unsafe_allow_html=True)

    with st.expander("📊 Feature Importance Insights", expanded=False):
        st.markdown("""
            <div style="font-size:13px; color:#8b93a7; line-height:2;">
                <b style="color:#e2e8f0;">🔑 Top Predictors</b><br>
                • <span style="color:#00c3ff;">pm2_5</span> — strongest predictor<br>
                • <span style="color:#7c3aed;">aqi_pm25</span> — target lag<br>
                • <span style="color:#7c3aed;">day</span> — weekly patterns<br>
                • <span style="color:#7c3aed;">roll_mean_12</span> — smoothing effect<br>
                • <span style="color:#7c3aed;">nitrogen_dioxide</span> — traffic indicator
            </div>
        """, unsafe_allow_html=True)

    st.markdown("""
        <div class="sidebar-profile">
            <div style="color:#6dd3ff; font-weight:800; font-size:14.5px;">👨‍💻 Muhammad Waqar</div>
            <div style="color:#8b93a7; font-size:12px; margin-top:2px;">10 Pearls Shine Intern • Cohort 9</div>
            <div style="color:#5b6478; font-size:11px; margin-top:4px;">AI/ML Engineer</div>
            <div style="display:flex; justify-content:center; gap:12px; margin-top:10px; font-size:13px;">
                <a href="https://github.com/Waqar738" target="_blank" style="color:#6dd3ff; text-decoration:none; font-weight:600;">GitHub ↗</a>
            </div>
        </div>
    """, unsafe_allow_html=True)

# ============================================================
# MAIN DASHBOARD
# ============================================================

if forecast_data:
    try:
        values = [
            forecast_data["1_day"]["value"],
            forecast_data["2_day"]["value"],
            forecast_data["3_day"]["value"],
        ]
        dates = [
            forecast_data["1_day"]["date"],
            forecast_data["2_day"]["date"],
            forecast_data["3_day"]["date"],
        ]
    except (KeyError, TypeError):
        st.error("🚨 The forecast response from the backend was in an unexpected format.")
        st.json(forecast_data)
        st.stop()

    # ---- NEW HERO BANNER ----
    st.markdown(f"""
        <div class="hero-banner">
            <div class="hero-icon">🌤️</div>
            <h1 class="hero-title">Bara Khyber Air Quality</h1>
            <p class="hero-sub">A clear, simple view of the air around you — with a 72-hour AI forecast, live readings, and health tips, all in one place.</p>
            <div class="hero-meta">
                <span class="hero-chip">📍 <strong>Bara Khyber</strong>, Pakistan</span>
                <span class="hero-chip">🕒 <strong>{datetime.now(ZoneInfo("Asia/Karachi")).strftime('%d %b %Y, %H:%M')}</strong></span>
                <span class="hero-chip">👨‍💻 Built by <strong>Muhammad Waqar</strong></span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # ---- CURRENT AQI ----
    st.markdown("<span class='section-tag'>Live</span>", unsafe_allow_html=True)
    st.markdown("## 📍 Current Air Quality")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        live_val = current_aqi_data.get("aqi") if current_aqi_data else None
        if isinstance(live_val, (int, float)):
            st.markdown(f"""
                <div class="glass-card" style="text-align:center;">
                    <div style="font-size:13px; color:#8b93a7; font-weight:600; letter-spacing:0.05em; text-transform:uppercase;">Live AQI</div>
                    <div style="font-size:56px; font-weight:800; color:{aqi_lookup(live_val)[2]}; line-height:1.2; margin-top:6px;">{live_val}</div>
                    <div style="margin-top:6px;">{badge_html(live_val)}</div>
                    <div style="font-size:12px; color:#5b6478; margin-top:10px;">Updated: {datetime.now().strftime('%H:%M')}</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="glass-card" style="text-align:center;">
                    <div style="font-size:13px; color:#8b93a7; font-weight:600; letter-spacing:0.05em; text-transform:uppercase;">Live AQI</div>
                    <div style="font-size:30px; font-weight:600; color:#5b6478; margin-top:14px;">N/A</div>
                    <div style="font-size:12px; color:#5b6478; margin-top:10px;">Live feed unavailable — using model forecast below</div>
                </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div class="glass-card">
                <div style="font-size:13px; color:#8b93a7; font-weight:600; letter-spacing:0.05em; text-transform:uppercase; margin-bottom:14px;">📊 AQI Scale</div>
                <div style="display:grid; grid-template-columns:1fr 1fr 1fr 1fr 1fr; gap:10px; text-align:center;">
                    <div style="background:rgba(255,255,255,0.035); border:1px solid rgba(255,255,255,0.06); border-radius:10px; padding:10px;">
                        <div style="color:#00e396; font-weight:800;">0–50</div><div style="font-size:11px; color:#5b6478; margin-top:2px;">Good</div>
                    </div>
                    <div style="background:rgba(255,255,255,0.035); border:1px solid rgba(255,255,255,0.06); border-radius:10px; padding:10px;">
                        <div style="color:#ffd54f; font-weight:800;">51–100</div><div style="font-size:11px; color:#5b6478; margin-top:2px;">Moderate</div>
                    </div>
                    <div style="background:rgba(255,255,255,0.035); border:1px solid rgba(255,255,255,0.06); border-radius:10px; padding:10px;">
                        <div style="color:#ff9900; font-weight:800;">101–150</div><div style="font-size:11px; color:#5b6478; margin-top:2px;">Unhealthy(S)</div>
                    </div>
                    <div style="background:rgba(255,255,255,0.035); border:1px solid rgba(255,255,255,0.06); border-radius:10px; padding:10px;">
                        <div style="color:#ff3333; font-weight:800;">151–200</div><div style="font-size:11px; color:#5b6478; margin-top:2px;">Unhealthy</div>
                    </div>
                    <div style="background:rgba(255,255,255,0.035); border:1px solid rgba(255,255,255,0.06); border-radius:10px; padding:10px;">
                        <div style="color:#c44dff; font-weight:800;">201+</div><div style="font-size:11px; color:#5b6478; margin-top:2px;">Hazardous</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
            <div class="glass-card">
                <div style="font-size:13px; color:#8b93a7; font-weight:600; letter-spacing:0.05em; text-transform:uppercase;">Data Sources</div>
                <div style="font-size:13px; color:#c7ced9; margin-top:12px; text-align:left; line-height:2;">
                    <div>🔹 Open-Meteo (Weather)</div>
                    <div>🔹 AQICN (Live AQI)</div>
                    <div>🔹 Custom Model (Forecast)</div>
                    <div style="margin-top:10px; font-size:11px; color:#5b6478;">Location: Bara Khyber, Pakistan</div>
                    <div style="font-size:11px; color:#5b6478;">Last sync: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ---- KEY METRICS ----
    st.markdown("<span class='section-tag'>Summary</span>", unsafe_allow_html=True)
    st.markdown("## 📊 Key Metrics")

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""<div class="metric-box"><div class="metric-value">{max(values):.1f}</div><div class="metric-label">Peak AQI</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-box"><div class="metric-value">{np.mean(values):.1f}</div><div class="metric-label">Average AQI</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="metric-box"><div class="metric-value">{min(values):.1f}</div><div class="metric-label">Minimum AQI</div></div>""", unsafe_allow_html=True)
    with c4:
        delta = values[-1] - values[0]
        arrow = "🔺" if delta > 0 else ("🔻" if delta < 0 else "➖")
        st.markdown(f"""<div class="metric-box"><div class="metric-value" style="font-size:26px;">{arrow} {delta:+.1f}</div><div class="metric-label">3-Day Trend</div></div>""", unsafe_allow_html=True)
    with c5:
        st.markdown("""<div class="metric-box"><div class="metric-value" style="font-size:26px;">72h</div><div class="metric-label">Forecast Window</div></div>""", unsafe_allow_html=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ---- GAUGES ----
    st.markdown("<span class='section-tag'>Forecast</span>", unsafe_allow_html=True)
    st.markdown("## 📅 72-Hour AQI Forecast")

    g1, g2, g3 = st.columns(3)
    days = [("Day 1", dates[0], values[0]), ("Day 2", dates[1], values[1]), ("Day 3", dates[2], values[2])]
    for idx, (day, date, value) in enumerate(days):
        with [g1, g2, g3][idx]:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            fig, label, slug, color = create_gauge(value, f"{day} · {date}")
            st.plotly_chart(fig, use_container_width=True, key=f"gauge_{idx}", config={"displayModeBar": False})
            st.markdown(f"<div style='text-align:center; margin-top:-6px;'>{badge_html(value)}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ---- TREND CHART ----
    st.markdown("<span class='section-tag'>Trend</span>", unsafe_allow_html=True)
    st.markdown("## 📈 Forecast Trend Analysis")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=values, mode='lines+markers',
        line=dict(color='#00c3ff', width=4),
        marker=dict(size=14, color='#00c3ff', symbol='circle', line=dict(width=2, color='#ffffff')),
        name='AQI Forecast', fill='tozeroy', fillcolor='rgba(0, 195, 255, 0.08)',
        hovertemplate='<b>%{x}</b><br>AQI: %{y:.1f}<extra></extra>',
    ))
    fig.add_hline(y=50, line_dash="dash", line_color="#00e396", opacity=0.5, annotation_text="Good", annotation_font_size=10, annotation_font_color="#00e396")
    fig.add_hline(y=100, line_dash="dash", line_color="#ffd54f", opacity=0.5, annotation_text="Moderate", annotation_font_size=10, annotation_font_color="#ffd54f")
    fig.add_hline(y=150, line_dash="dash", line_color="#ff9900", opacity=0.5, annotation_text="Unhealthy", annotation_font_size=10, annotation_font_color="#ff9900")

    fig.update_layout(
        height=380,
        xaxis=dict(title="Date", title_font=dict(color='#8b93a7'), tickfont=dict(color='#8b93a7'), gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(title="AQI Value", title_font=dict(color='#8b93a7'), tickfont=dict(color='#8b93a7'), gridcolor='rgba(255,255,255,0.05)', range=[0, max(values) + 60]),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(255,255,255,0.015)',
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, font=dict(color='#8b93a7', size=11)),
        margin=dict(l=10, r=10, t=30, b=10),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ---- HEALTH ADVISORY ----
    st.markdown("<span class='section-tag'>Advisory</span>", unsafe_allow_html=True)
    st.markdown("## 🚨 Health Advisory")

    max_aqi = max(values)
    label, slug, color = aqi_lookup(max_aqi)
    title, body = ADVISORY_TEXT[slug]

    a1, a2 = st.columns([1, 2.5])
    with a1:
        st.markdown(f"""
            <div style="text-align:center; background:rgba(255,255,255,0.035); border-radius:18px; padding:26px; border:1px solid rgba(255,255,255,0.08);">
                <div style="font-size:54px; font-weight:800; color:{color};">{max_aqi:.0f}</div>
                <div style="font-size:13px; color:#8b93a7; font-weight:600; letter-spacing:0.05em; text-transform:uppercase; margin-top:2px;">Peak AQI (3-day)</div>
                <div style="margin-top:10px;">{badge_html(max_aqi)}</div>
            </div>
        """, unsafe_allow_html=True)
    with a2:
        st.markdown(f"""
            <div class="advisory-box advisory-{slug}">
                <div style="font-size:17px; font-weight:800;">{title}</div>
                <div style="font-size:14px; color:#c7ced9; margin-top:10px; line-height:1.6;">{body}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ---- MODEL PERFORMANCE + FEATURE IMPORTANCE ----
    m1, m2 = st.columns([1, 1.2])

    with m1:
        st.markdown("<span class='section-tag'>Model</span>", unsafe_allow_html=True)
        st.markdown("## 🏆 Model Performance")
        if best_model_data and "model" in best_model_data:
            model = best_model_data["model"]
            st.markdown(f"""
                <div class="glass-card">
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px;">
                        <div style="background:rgba(255,255,255,0.035); border:1px solid rgba(255,255,255,0.06); border-radius:14px; padding:16px; text-align:center;">
                            <div style="font-size:11px; color:#8b93a7; font-weight:600; letter-spacing:0.04em; text-transform:uppercase;">Model</div>
                            <div style="font-size:15px; font-weight:700; color:#6dd3ff; margin-top:4px;">{model.get('model_name', 'Random Forest')}</div>
                        </div>
                        <div style="background:rgba(255,255,255,0.035); border:1px solid rgba(255,255,255,0.06); border-radius:14px; padding:16px; text-align:center;">
                            <div style="font-size:11px; color:#8b93a7; font-weight:600; letter-spacing:0.04em; text-transform:uppercase;">Horizon</div>
                            <div style="font-size:15px; font-weight:700; color:#e2e8f0; margin-top:4px;">H{model.get('horizon', 1)} (24h)</div>
                        </div>
                        <div style="background:rgba(255,255,255,0.035); border:1px solid rgba(255,255,255,0.06); border-radius:14px; padding:16px; text-align:center;">
                            <div style="font-size:11px; color:#8b93a7; font-weight:600; letter-spacing:0.04em; text-transform:uppercase;">RMSE</div>
                            <div style="font-size:19px; font-weight:800; color:#00c3ff; margin-top:4px;">{model.get('rmse', 0):.2f}</div>
                        </div>
                        <div style="background:rgba(255,255,255,0.035); border:1px solid rgba(255,255,255,0.06); border-radius:14px; padding:16px; text-align:center;">
                            <div style="font-size:11px; color:#8b93a7; font-weight:600; letter-spacing:0.04em; text-transform:uppercase;">R² Score</div>
                            <div style="font-size:19px; font-weight:800; color:#7c3aed; margin-top:4px;">{model.get('r2', 0):.3f}</div>
                        </div>
                    </div>
                    <div style="margin-top:14px; text-align:center; font-size:13px; color:#8b93a7;">
                        Status: <span style="color:#00e396; font-weight:700;">● Production Ready</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ Best model details unavailable from the registry.")

    with m2:
        st.markdown("<span class='section-tag'>Interpretability</span>", unsafe_allow_html=True)
        st.markdown("## 📊 Feature Importance")
        fi_fig = create_feature_importance_chart(feature_importance_data)
        if fi_fig:
            st.plotly_chart(fi_fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.warning("⚠️ Feature importance data unavailable.")

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ---- FEATURE IMPACT (static explainer, clearly labeled illustrative) ----
    st.markdown("<span class='section-tag'>Explainability</span>", unsafe_allow_html=True)
    st.markdown("## 🔬 Feature Impact Analysis")
    st.caption("Illustrative directional impact of top features on the model's predictions, based on training-time analysis.")

    fi1, fi2, fi3 = st.columns(3)
    with fi1:
        st.markdown("""
            <div class="glass-card" style="padding:20px;">
                <div style="font-size:13px; color:#8b93a7; font-weight:600; letter-spacing:0.04em; text-transform:uppercase;">🔹 Strongest Positive Drivers</div>
                <div style="margin-top:12px;">
                    <div style="display:flex; justify-content:space-between; padding:6px 0; border-bottom:1px solid rgba(255,255,255,0.05);"><span style="color:#e2e8f0;">pm2_5</span><span style="color:#00c3ff; font-weight:700;">+0.19</span></div>
                    <div style="display:flex; justify-content:space-between; padding:6px 0; border-bottom:1px solid rgba(255,255,255,0.05);"><span style="color:#e2e8f0;">aqi_pm25 (lag)</span><span style="color:#00c3ff; font-weight:700;">+0.17</span></div>
                    <div style="display:flex; justify-content:space-between; padding:6px 0;"><span style="color:#e2e8f0;">day</span><span style="color:#7c3aed; font-weight:700;">+0.12</span></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    with fi2:
        st.markdown("""
            <div class="glass-card" style="padding:20px;">
                <div style="font-size:13px; color:#8b93a7; font-weight:600; letter-spacing:0.04em; text-transform:uppercase;">🔸 Reading This Chart</div>
                <div style="margin-top:12px; font-size:13px; color:#8b93a7; line-height:1.8;">
                    Values show how strongly each feature moves the predicted AQI.<br><br>
                    <span style="color:#00c3ff; font-weight:600;">Higher magnitude</span> = stronger influence on the forecast.
                </div>
            </div>
        """, unsafe_allow_html=True)
    with fi3:
        st.markdown("""
            <div class="glass-card" style="padding:20px;">
                <div style="font-size:13px; color:#8b93a7; font-weight:600; letter-spacing:0.04em; text-transform:uppercase;">🔹 Key Takeaways</div>
                <div style="margin-top:12px; font-size:13px; color:#8b93a7; line-height:1.9;">
                    • <span style="color:#00c3ff;">pm2_5</span> is the dominant predictor<br>
                    • <span style="color:#7c3aed;">day</span> captures weekly cycles<br>
                    • <span style="color:#7c3aed;">nitrogen_dioxide</span> reflects traffic load<br>
                    • <span style="color:#7c3aed;">rolling means</span> smooth short-term noise
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ---- SYSTEM STATUS ----
    st.markdown("<span class='section-tag'>Infra</span>", unsafe_allow_html=True)
    st.markdown("## ⚙️ System Status")

    s1, s2, s3 = st.columns(3)
    with s1:
        status_row("Backend API", api_online, "Railway")
    with s2:
        status_row("Model Registry", best_model_data is not None, "GridFS")
    with s3:
        status_row("Live AQI Feed", current_aqi_data is not None, "AQICN")

else:
    st.markdown("""
        <div class="glass-card" style="text-align:center; padding:56px 20px;">
            <div style="font-size:50px; margin-bottom:18px;">🔌</div>
            <h3>Backend Connection Error</h3>
            <p style="color:#8b93a7;">Unable to reach the prediction engine. It may be cold-starting on Railway — please retry in a few seconds.</p>
        </div>
    """, unsafe_allow_html=True)
    if st.button("🔄 Retry Connection"):
        st.cache_data.clear()
        st.rerun()

# ============================================================
# FOOTER — redesigned
# ============================================================

st.markdown(f"""
    <div class="footer-wrap">
        <div class="foot-icon">🌤️</div>
        <div class="foot-title">Bara Khyber AQI Forecast System</div>
        <div class="foot-line">Built with ❤️ by <strong>Muhammad Waqar</strong> · 10 Pearls Shine Intern · Cohort 9</div>
        <div class="foot-tags">
            <span class="foot-tag">🚀 Production MLOps</span>
            <span class="foot-tag">⚡ FastAPI + Streamlit</span>
            <span class="foot-tag">🔬 Feature Importance</span>
            <span class="foot-tag">📍 Bara Khyber, Pakistan</span>
        </div>
        <div class="foot-bottom">
            Last refreshed {datetime.now().strftime('%Y-%m-%d %H:%M')} · © 2026 All Rights Reserved
        </div>
    </div>
""", unsafe_allow_html=True)
