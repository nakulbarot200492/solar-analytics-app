import streamlit as st
import pandas as pd
from core.exporter import build_export_package
from core.rca_engine import get_rca_summary
from app.styles import inject_global_css, inject_nav_bar

st.set_page_config(page_title="Export Reports", page_icon="📥", layout="wide")
inject_global_css()
inject_nav_bar()

if "ranking_df" not in st.session_state:
    st.warning("⚠️ Please go to Upload page and process your data first.")
    st.stop()

st.title("📥 Export Reports")

st.markdown("""
<div style="background: rgba(30,41,59,0.6); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 24px; margin-bottom: 24px;">
    <h4 style="color: #f1f5f9; margin-top: 0;">Download Complete Analytics Package</h4>
    <p style="color: #94a3b8; margin-bottom: 0;">
        Export all four deliverables in a single Excel workbook:
    </p>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 12px;">
        <div style="color: #e2e8f0; font-size: 0.85rem;">📊 Inverter Ranking</div>
        <div style="color: #e2e8f0; font-size: 0.85rem;">⚠️ Anomaly Log (with RCA)</div>
        <div style="color: #e2e8f0; font-size: 0.85rem;">🛠️ RCA Report (Aggregated)</div>
        <div style="color: #e2e8f0; font-size: 0.85rem;">⚡ MPPT Analysis (Summary)</div>
    </div>
</div>
""", unsafe_allow_html=True)

ranking_df = st.session_state["ranking_df"]
anomaly_df = st.session_state.get("anomaly_df", pd.DataFrame())
mppt_summary_df = st.session_state.get("mppt_summary_df", pd.DataFrame())

rca_summary_df = get_rca_summary(anomaly_df)

excel_data = build_export_package(
    ranking_df=ranking_df,
    anomaly_df=anomaly_df,
    rca_df=rca_summary_df,
    mppt_summary_df=mppt_summary_df
)

col_center = st.columns([1, 2, 1])[1]
with col_center:
    st.download_button(
        label="⬇️  Download Excel Workbook (.xlsx)",
        data=excel_data,
        file_name="solar_analytics_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        use_container_width=True
    )

st.markdown("""
<div style="text-align: center; margin-top: 16px;">
    <p style="color: #64748b; font-size: 0.8rem;">
        Report is ready for download. The Excel workbook contains all analytics results.
    </p>
</div>
""", unsafe_allow_html=True)
