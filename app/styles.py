"""
app/styles.py
--------------
Global CSS theme for the Solar SPV Analytics Platform.
Inject with: inject_global_css()
"""

import streamlit as st

def inject_global_css():
    """Inject premium dark-theme CSS into the Streamlit app."""
    st.markdown("""
    <style>
    /* ─── Google Font ─────────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ─── Global Reset ────────────────────────────────────────────────── */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    h1, h2, h3, h4, h5, h6, p, span, div, a, button, input, select, textarea {
        font-family: 'Inter', sans-serif;
    }
    
    /* Preserve material icons font */
    .material-icons,
    [class*="IconMaterial"],
    [data-testid="stIconMaterial"] {
        font-family: 'Material Icons', 'Material Symbols Rounded', sans-serif !important;
    }
    
    .stApp {
        background: linear-gradient(145deg, #0a0e1a 0%, #111827 50%, #0f172a 100%) !important;
    }

    /* ─── Sidebar ──────────────────────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #111827 0%, #0d1321 100%) !important;
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown span {
        color: #94a3b8 !important;
    }
    
    /* Sidebar nav links */
    section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"] {
        border-radius: 8px !important;
        padding: 6px 12px !important;
        margin: 2px 8px !important;
        transition: all 0.2s ease !important;
    }
    section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"]:hover {
        background: rgba(247, 183, 49, 0.08) !important;
    }
    section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"][aria-selected="true"] {
        background: linear-gradient(135deg, rgba(247,183,49,0.15) 0%, rgba(59,130,246,0.12) 100%) !important;
        border-left: 3px solid #F7B731 !important;
    }

    /* ─── Headers ──────────────────────────────────────────────────────── */
    h1 {
        background: linear-gradient(135deg, #F7B731 0%, #f59e0b 50%, #fbbf24 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
        letter-spacing: -0.5px;
    }
    h2, h3 {
        color: #e2e8f0 !important;
        font-weight: 600 !important;
    }
    
    /* ─── Metric Cards ─────────────────────────────────────────────────── */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(30,41,59,0.8) 0%, rgba(15,23,42,0.9) 100%);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.08);
    }
    [data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    [data-testid="stMetricValue"] {
        color: #f1f5f9 !important;
        font-weight: 700 !important;
        font-size: 1.8rem !important;
    }

    /* ─── Dataframes ───────────────────────────────────────────────────── */
    [data-testid="stDataFrame"] {
        border-radius: 12px !important;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.08) !important;
    }
    
    /* ─── Buttons ──────────────────────────────────────────────────────── */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        letter-spacing: 0.3px;
        transition: all 0.3s ease !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #F7B731 0%, #f59e0b 100%) !important;
        color: #0f172a !important;
        font-weight: 700 !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(247,183,49,0.3) !important;
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 6px 25px rgba(247,183,49,0.5) !important;
        transform: translateY(-1px);
    }
    .stButton > button:not([kind="primary"]) {
        background: rgba(30,41,59,0.6) !important;
        color: #e2e8f0 !important;
    }
    .stButton > button:not([kind="primary"]):hover {
        background: rgba(51,65,85,0.8) !important;
    }

    /* ─── Expander ─────────────────────────────────────────────────────── */
    [data-testid="stExpander"] {
        background: rgba(30,41,59,0.4) !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        border-radius: 12px !important;
    }

    /* ─── Selectbox ────────────────────────────────────────────────────── */
    .stSelectbox > div > div {
        border-radius: 10px !important;
        border-color: rgba(255,255,255,0.1) !important;
    }
    
    /* ─── File Uploader ────────────────────────────────────────────────── */
    [data-testid="stFileUploader"] {
        border-radius: 12px !important;
    }
    [data-testid="stFileUploader"] section {
        border: 2px dashed rgba(247,183,49,0.3) !important;
        border-radius: 12px !important;
        background: rgba(247,183,49,0.03) !important;
    }
    [data-testid="stFileUploader"] section:hover {
        border-color: rgba(247,183,49,0.6) !important;
        background: rgba(247,183,49,0.06) !important;
    }

    /* ─── Status / Alerts ──────────────────────────────────────────────── */
    .stAlert {
        border-radius: 10px !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
    }
    
    /* ─── Tabs ─────────────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 8px 16px;
        font-weight: 500;
    }

    /* ─── Download Button ──────────────────────────────────────────────── */
    .stDownloadButton > button {
        border-radius: 10px !important;
        background: rgba(30,41,59,0.6) !important;
        border: 1px solid rgba(59,130,246,0.3) !important;
        color: #93c5fd !important;
        font-weight: 600 !important;
    }
    .stDownloadButton > button:hover {
        background: rgba(59,130,246,0.15) !important;
        border-color: rgba(59,130,246,0.5) !important;
    }
    
    /* ─── Plotly Charts ────────────────────────────────────────────────── */
    .js-plotly-plot .plotly .main-svg {
        border-radius: 12px !important;
    }

    /* ─── Custom KPI Card Classes ──────────────────────────────────────── */
    .kpi-card {
        background: linear-gradient(135deg, rgba(30,41,59,0.9) 0%, rgba(15,23,42,0.95) 100%);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 20px 24px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.05);
        transition: transform 0.3s ease;
    }
    .kpi-card:hover { transform: translateY(-3px); }
    .kpi-card .kpi-label {
        font-size: 0.75rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        font-weight: 500;
        margin-bottom: 4px;
    }
    .kpi-card .kpi-value {
        font-size: 1.8rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        line-height: 1.2;
    }
    .kpi-card .kpi-value.gold { color: #fbbf24; }
    .kpi-card .kpi-value.red { color: #ef4444; }
    .kpi-card .kpi-value.teal { color: #2dd4bf; }
    .kpi-card .kpi-value.blue { color: #60a5fa; }
    .kpi-card .kpi-icon {
        font-size: 1.4rem;
        margin-bottom: 8px;
        display: block;
    }

    /* ─── Feature Card ─────────────────────────────────────────────────── */
    .feature-card {
        background: linear-gradient(145deg, rgba(30,41,59,0.7) 0%, rgba(15,23,42,0.8) 100%);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 14px;
        padding: 24px;
        min-height: 220px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }
    .feature-card:hover {
        border-color: rgba(247,183,49,0.2);
        box-shadow: 0 8px 30px rgba(0,0,0,0.3);
        transform: translateY(-2px);
    }
    .feature-card h4 {
        color: #f1f5f9 !important;
        font-weight: 700 !important;
        font-size: 1rem;
        margin-bottom: 8px;
    }
    .feature-card p {
        color: #94a3b8 !important;
        font-size: 0.85rem;
        line-height: 1.5;
    }

    /* ─── Divider ──────────────────────────────────────────────────────── */
    hr {
        border: none;
        border-top: 1px solid rgba(255,255,255,0.06);
        margin: 2rem 0;
    }

    /* ─── Fix: File uploader button text overlap ─────────────────────── */
    [data-testid="stFileUploader"] button {
        min-width: 100px !important;
        padding: 4px 16px !important;
        white-space: nowrap !important;
        overflow: visible !important;
    }
    [data-testid="stFileUploader"] section > div {
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
    }
    [data-testid="stFileUploaderDropzone"] {
        padding: 16px 20px !important;
    }
    </style>
    """, unsafe_allow_html=True)
