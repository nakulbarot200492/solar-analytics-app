"""
app/main.py
-----------
Entry point for the Streamlit application.
Premium dashboard landing page with KPI overview and feature cards.
"""
import streamlit as st
import pandas as pd
import sys
import os

# Ensure the core module can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(
    page_title="Solar Analytics Platform",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Inject Global CSS ────────────────────────────────────────────────────────
from app.styles import inject_global_css
inject_global_css()

# ── Top Navigation Bar ───────────────────────────────────────────────────────
st.markdown("""
<div style="
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    background: rgba(32,31,31,0.8);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px;
    padding: 10px 16px;
    margin-bottom: 24px;
    backdrop-filter: blur(10px);
">
    <span style="color:#ffd700; font-weight:700; font-size:0.85rem; align-self:center; margin-right:8px;">☀️ NAVIGATE:</span>
""", unsafe_allow_html=True)

nav_cols = st.columns(6)
with nav_cols[0]:
    st.page_link("app/main.py", label="🏠 Home", use_container_width=True)
with nav_cols[1]:
    st.page_link("app/pages/1_Upload.py", label="📁 Upload", use_container_width=True)
with nav_cols[2]:
    st.page_link("app/pages/2_Ranking.py", label="📊 Ranking", use_container_width=True)
with nav_cols[3]:
    st.page_link("app/pages/3_Anomalies.py", label="⚠️ Anomalies", use_container_width=True)
with nav_cols[4]:
    st.page_link("app/pages/4_MPPT_Analysis.py", label="⚡ MPPT", use_container_width=True)
with nav_cols[5]:
    st.page_link("app/pages/5_RCA_Report.py", label="🛠️ RCA", use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)

# ── Sidebar Control Panel ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🛠️ Control Panel")
    if st.button("🔄 Refresh Dashboard", type="primary", use_container_width=True):
        st.rerun()
    st.markdown("<hr>", unsafe_allow_html=True)


st.markdown("""
<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
    <span style="font-size: 2.2rem;">☀️</span>
    <h1 style="margin: 0; font-size: 2rem;">Solar SPV Analytics Platform</h1>
</div>
<p style="color: #64748b; font-size: 0.95rem; margin-top: 0;">
    Intelligent monitoring & diagnostics for utility-scale solar plants
</p>
""", unsafe_allow_html=True)

# ── KPI Summary Cards ───────────────────────────────────────────────────────
has_data = "cleaned_df" in st.session_state and not st.session_state["cleaned_df"].empty

if has_data:
    cdf = st.session_state["cleaned_df"]
    ranking_df = st.session_state.get("ranking_df", pd.DataFrame())
    anomaly_df = st.session_state.get("anomaly_df", pd.DataFrame())
    
    # Compute KPIs
    n_inverters = cdf["Inverter_ID"].nunique() if "Inverter_ID" in cdf.columns else 0
    n_mppts = cdf["MPPT_ID"].nunique() if "MPPT_ID" in cdf.columns else 0
    
    pr_val = "N/A"
    if not ranking_df.empty and "PR_%" in ranking_df.columns:
        mean_pr = ranking_df["PR_%"].mean()
        pr_val = f"{mean_pr:.1f}%" if pd.notna(mean_pr) else "N/A"
    
    n_high = 0
    n_anomalies = 0
    if not anomaly_df.empty:
        n_anomalies = len(anomaly_df)
        n_high = len(anomaly_df[anomaly_df["Severity"] == "HIGH"]) if "Severity" in anomaly_df.columns else 0
    
    total_energy = 0.0
    if not ranking_df.empty and "Energy_kWh" in ranking_df.columns:
        total_energy = ranking_df["Energy_kWh"].sum()

    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <span class="kpi-icon">📊</span>
            <div class="kpi-label">Overall Fleet PR</div>
            <div class="kpi-value gold">{pr_val}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        anomaly_color = "red" if n_high > 0 else "teal"
        anomaly_text = f"{n_high} High-Priority" if n_high > 0 else f"{n_anomalies} Total"
        st.markdown(f"""
        <div class="kpi-card">
            <span class="kpi-icon">⚠️</span>
            <div class="kpi-label">Active Anomalies</div>
            <div class="kpi-value {anomaly_color}">{anomaly_text}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        if total_energy > 1000:
            energy_str = f"{total_energy/1000:.1f} MWh"
        elif total_energy > 0:
            energy_str = f"{total_energy:.1f} kWh"
        else:
            energy_str = f"{n_inverters} Units"
        st.markdown(f"""
        <div class="kpi-card">
            <span class="kpi-icon">⚡</span>
            <div class="kpi-label">{'Total Generation' if total_energy > 0 else 'Fleet Size'}</div>
            <div class="kpi-value teal">{energy_str}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        health_val = "N/A"
        if not ranking_df.empty and "MPPT_Health" in ranking_df.columns:
            mean_h = ranking_df["MPPT_Health"].mean()
            health_val = f"{mean_h:.0f}/100" if pd.notna(mean_h) else "N/A"
        st.markdown(f"""
        <div class="kpi-card">
            <span class="kpi-icon">🔋</span>
            <div class="kpi-label">Avg MPPT Health</div>
            <div class="kpi-value blue">{health_val}</div>
        </div>
        """, unsafe_allow_html=True)

else:
    # No data uploaded yet — show placeholder KPIs
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
        <div class="kpi-card">
            <span class="kpi-icon">📊</span>
            <div class="kpi-label">Overall Fleet PR</div>
            <div class="kpi-value" style="color: #475569;">—</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="kpi-card">
            <span class="kpi-icon">⚠️</span>
            <div class="kpi-label">Active Anomalies</div>
            <div class="kpi-value" style="color: #475569;">—</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="kpi-card">
            <span class="kpi-icon">⚡</span>
            <div class="kpi-label">Total Generation</div>
            <div class="kpi-value" style="color: #475569;">—</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown("""
        <div class="kpi-card">
            <span class="kpi-icon">🔋</span>
            <div class="kpi-label">Avg MPPT Health</div>
            <div class="kpi-value" style="color: #475569;">—</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Features Section ─────────────────────────────────────────────────────────
st.markdown("### Features")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="feature-card">
        <h4>📊 Inverter Ranking</h4>
        <p>Rank all inverters by a composite score combining energy output, 
        availability, and MPPT channel health. Identify top and bottom performers 
        at a glance with color-coded performance tiers.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <h4>⚠️ Anomaly Detection</h4>
        <p>Rule-based detection of 8 failure modes on real-time data: 
        Zero Generation, Sudden Power Drops, MPPT Current Mismatches, 
        Voltage Instability, Flatline Current, Clipping, and more.</p>
    </div>
    """, unsafe_allow_html=True)

col3, col4 = st.columns(2)

with col3:
    st.markdown("""
    <div class="feature-card">
        <h4>⚡ MPPT Analysis</h4>
        <p>Deviation analysis and cleanliness comparison across MPPT channels. 
        Interactive heatmaps show current and voltage patterns with color-coded 
        anomaly indicators per inverter.</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="feature-card">
        <h4>🛠️ RCA Engine</h4>
        <p>Map detected anomalies to probable root causes with actionable 
        O&M recommendations. Priority-based filtering helps teams focus on 
        the most critical issues first.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Getting Started ──────────────────────────────────────────────────────────
st.markdown("""
<div class="feature-card" style="text-align: center; max-width: 600px; margin: 0 auto;">
    <h4>🚀 Getting Started</h4>
    <p style="margin-bottom: 16px;">Upload your <code>.xlsx</code> or <code>.xls</code> SMA dataset to begin analysis.</p>
</div>
""", unsafe_allow_html=True)

col_center = st.columns([1, 2, 1])[1]
with col_center:
    if st.button("📁  START ANALYSIS  →", type="primary", use_container_width=True):
        st.switch_page("pages/1_Upload.py")

# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown("""
<hr>
<p style="text-align: center; color: #475569; font-size: 0.75rem;">
    Solar SPV Analytics Platform v3.0 &nbsp;|&nbsp; Built for O&M Engineers &nbsp;|&nbsp; Powered by Streamlit
</p>
""", unsafe_allow_html=True)
