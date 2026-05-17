"""
app/styles.py
--------------
Global CSS theme for the Solar SPV Analytics Platform.
Inject with: inject_global_css()
"""

import streamlit as st

def inject_global_css():
    """Inject the premium 'Solar Analytics' design system from Stitch."""
    st.markdown("""
    <style>
    /* ─── Google Fonts ────────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    /* ─── Global Reset & Typography ─────────────────────────────────────── */
    :root {
        --primary: #ffd700;
        --secondary: #4a8eff;
        --tertiary: #7bf29d;
        --background: #131313;
        --surface: #201f1f;
        --surface-border: rgba(255, 255, 255, 0.1);
        --font-headline: 'Space Grotesk', sans-serif;
        --font-body: 'Inter', sans-serif;
        --font-mono: 'JetBrains Mono', monospace;
    }

    html, body, [class*="css"] {
        font-family: var(--font-body);
        background-color: var(--background);
        color: #e5e2e1;
    }

    h1, h2, h3, .data-label, [data-testid="stMetricValue"] {
        font-family: var(--font-headline) !important;
    }

    code, pre, [data-testid="stCode"] {
        font-family: var(--font-mono) !important;
    }

    .stApp {
        background: var(--background) !important;
    }

    /* ─── Sidebar ──────────────────────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: #0e0e0e !important;
        border-right: 1px solid var(--surface-border);
    }
    
    section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"] {
        border-radius: 8px !important;
        margin: 4px 12px !important;
        transition: all 0.2s ease;
    }
    
    section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"][aria-selected="true"] {
        background: rgba(255, 215, 0, 0.1) !important;
        border-left: 4px solid var(--primary) !important;
        color: var(--primary) !important;
    }

    /* ─── Headers ──────────────────────────────────────────────────────── */
    h1 {
        color: var(--primary) !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
        font-size: 2.5rem !important;
    }
    
    h2, h3 {
        color: #e5e2e1 !important;
        font-weight: 600 !important;
        letter-spacing: -0.01em !important;
    }

    /* ─── Glassmorphism Cards (Metrics, Dataframes, Expanders) ──────────── */
    [data-testid="stMetric"], [data-testid="stDataFrame"], [data-testid="stExpander"], .kpi-card, .feature-card {
        background: rgba(32, 31, 31, 0.6) !important;
        backdrop-filter: blur(20px) !important;
        border: 1px solid var(--surface-border) !important;
        border-radius: 24px !important;
        padding: 20px !important;
        transition: transform 0.3s ease, border-color 0.3s ease !important;
    }

    [data-testid="stMetric"]:hover, .kpi-card:hover, .feature-card:hover {
        transform: translateY(-4px);
        border-color: rgba(255, 215, 0, 0.3) !important;
    }

    [data-testid="stMetricLabel"] {
        font-family: var(--font-body) !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600 !important;
        color: #d0c6ab !important;
    }

    [data-testid="stMetricValue"] {
        color: var(--primary) !important;
        font-size: 2.2rem !important;
    }

    /* ─── Buttons ──────────────────────────────────────────────────────── */
    .stButton > button {
        border-radius: 8px !important;
        font-family: var(--font-headline) !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }

    .stButton > button[kind="primary"] {
        background: var(--primary) !important;
        color: #131313 !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(255, 215, 0, 0.2) !important;
    }

    .stButton > button[kind="primary"]:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 20px rgba(255, 215, 0, 0.4) !important;
    }

    /* ─── Feature Cards ────────────────────────────────────────────────── */
    .feature-card {
        min-height: 180px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .feature-card h4 {
        color: var(--primary) !important;
        font-family: var(--font-headline) !important;
        margin-bottom: 12px !important;
    }

    /* ─── KPI Cards (Dashboard) ────────────────────────────────────────── */
    .kpi-card .kpi-label {
        font-family: var(--font-body);
        color: #d0c6ab;
        font-size: 0.75rem;
        font-weight: 600;
        margin-bottom: 4px;
    }
    
    .kpi-card .kpi-value {
        font-family: var(--font-headline);
        font-size: 2rem;
        font-weight: 700;
    }
    
    .kpi-card .kpi-value.gold { color: var(--primary); }
    .kpi-card .kpi-value.red { color: #ffb4ab; }
    .kpi-card .kpi-value.teal { color: var(--tertiary); }
    .kpi-card .kpi-value.blue { color: var(--secondary); }

    /* ─── File Uploader ────────────────────────────────────────────────── */
    [data-testid="stFileUploader"] section {
        border: 2px dashed rgba(255, 215, 0, 0.3) !important;
        border-radius: 16px !important;
        background: rgba(255, 215, 0, 0.02) !important;
    }

    /* ─── Custom scrollbar ─────────────────────────────────────────────── */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: var(--background); }
    ::-webkit-scrollbar-thumb { background: #353534; border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: #4d4732; }

    /* ─── Hide Streamlit Branding (Make it look Native) ────────────── */
    [data-testid="stToolbar"] { display: none !important; visibility: hidden !important; }
    .stDeployButton { display: none !important; }
    #MainMenu { display: none !important; }
    footer { display: none !important; }
    
    /* Aggressive Viewer Badge Hide */
    .viewerBadge_container__1JCIV, .viewerBadge_link__1S137, #viewerBadgeTootip { display: none !important; }
    div[class^="viewerBadge_"] { display: none !important; opacity: 0 !important; }
    iframe[src*="badge"] { display: none !important; }

    /* ─── Sidebar Toggle Button (Mobile) ────────────── */
    [data-testid="collapsedControl"] {
        background-color: var(--primary) !important;
        border-radius: 50% !important;
        margin: 10px !important;
        box-shadow: 0 4px 10px rgba(255, 215, 0, 0.3) !important;
        color: #131313 !important;
        z-index: 1000000 !important;
        display: flex !important;
    }
    [data-testid="collapsedControl"] svg, [data-testid="collapsedControl"] path {
        fill: #131313 !important;
        stroke: #131313 !important;
        color: #131313 !important;
    }
    </style>
    """, unsafe_allow_html=True)
