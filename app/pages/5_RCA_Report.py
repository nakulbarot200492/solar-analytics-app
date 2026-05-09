import streamlit as st
import pandas as pd
from core.rca_engine import get_rca_summary
from app.styles import inject_global_css

if "anomaly_df" not in st.session_state:
    st.warning("Please upload and process data first.")
    st.stop()

st.set_page_config(page_title="RCA Engine", page_icon="🛠️", layout="wide")
inject_global_css()

st.title("🛠️ Root Cause Analysis")

anomaly_df = st.session_state["anomaly_df"]

if anomaly_df.empty:
    st.markdown("""
    <div style="background: rgba(16,185,129,0.08); border: 1px solid rgba(16,185,129,0.2); border-radius: 12px; padding: 24px; text-align: center;">
        <p style="font-size: 2rem; margin: 0;">✅</p>
        <h3 style="color: #6ee7b7; margin: 8px 0;">System Operating Normally</h3>
        <p style="color: #94a3b8; margin: 0;">No anomalies detected. No root causes to analyze.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── RCA Summary ─────────────────────────────────────────────────────────────
st.markdown("### RCA Summary")
st.markdown("""
<div style="background: rgba(59,130,246,0.06); border: 1px solid rgba(59,130,246,0.15); border-radius: 10px; padding: 12px 16px; margin-bottom: 16px;">
    <p style="margin: 0; color: #93c5fd; font-size: 0.85rem;">
        The table below maps detected anomalies to probable root causes with recommended corrective actions.
    </p>
</div>
""", unsafe_allow_html=True)

rca_summary = get_rca_summary(anomaly_df)

def highlight_priority(val):
    if val == "Immediate":
        return "background-color: #7f1d1d; color: #fca5a5; font-weight: bold;"
    elif val == "High":
        return "background-color: #78350f; color: #fde68a; font-weight: bold;"
    elif val == "Medium":
        return "background-color: #1e3a5f; color: #93c5fd; font-weight: bold;"
    return ""

if not rca_summary.empty:
    st.dataframe(
        rca_summary.style.map(highlight_priority, subset=["Priority"]),
        width='stretch',
        hide_index=True
    )
else:
    st.info("No RCA data to display.")

# ── Filter by Priority ──────────────────────────────────────────────────────
st.markdown("### Filter by Priority")
priorities = ["All", "Immediate", "High", "Medium", "Low"]
sel_pri = st.selectbox("Select Priority Level", priorities)

if sel_pri == "All":
    filtered_rca = anomaly_df
else:
    filtered_rca = anomaly_df[anomaly_df.get("Priority", pd.Series()) == sel_pri] if "Priority" in anomaly_df.columns else anomaly_df

display_cols = [c for c in ["Timestamp", "Inverter_ID", "MPPT_ID", "Anomaly_Type", "Root_Cause", "Recommended_Action", "Priority"] if c in filtered_rca.columns]

st.dataframe(
    filtered_rca[display_cols] if display_cols else filtered_rca,
    width='stretch',
    hide_index=True
)
