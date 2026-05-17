import streamlit as st
import pandas as pd
from core.exporter import build_export_package
from core.rca_engine import get_rca_summary
from core.pdf_exporter import build_pdf_report
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
        Export all four deliverables — Inverter Ranking, Anomaly Log (with RCA), RCA Report, and MPPT Analysis:
    </p>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 12px;">
        <div style="color: #e2e8f0; font-size: 0.85rem;">📊 Inverter Ranking</div>
        <div style="color: #e2e8f0; font-size: 0.85rem;">⚠️ Anomaly Log (with RCA)</div>
        <div style="color: #e2e8f0; font-size: 0.85rem;">🛠️ RCA Report (Aggregated)</div>
        <div style="color: #e2e8f0; font-size: 0.85rem;">⚡ MPPT Analysis (Summary)</div>
    </div>
</div>
""", unsafe_allow_html=True)

ranking_df     = st.session_state["ranking_df"]
anomaly_df     = st.session_state.get("anomaly_df", pd.DataFrame())
mppt_summary_df = st.session_state.get("mppt_summary_df", pd.DataFrame())
cleaned_df     = st.session_state.get("cleaned_df", pd.DataFrame())

rca_summary_df = get_rca_summary(anomaly_df)

# Detect site name
site_name = "Site_1"
if not cleaned_df.empty and "Site" in cleaned_df.columns:
    site_name = str(cleaned_df["Site"].iloc[0])

# ── Generate Files ──────────────────────────────────────────────────────────
with st.spinner("Preparing reports..."):
    excel_data = build_export_package(
        ranking_df=ranking_df,
        anomaly_df=anomaly_df,
        rca_df=rca_summary_df,
        mppt_summary_df=mppt_summary_df
    )

    pdf_data = build_pdf_report(
        ranking_df=ranking_df,
        anomaly_df=anomaly_df,
        rca_df=rca_summary_df,
        mppt_summary_df=mppt_summary_df,
        site_name=site_name
    )

# ── Download Buttons ─────────────────────────────────────────────────────────
st.markdown("### Choose Download Format")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div style="background: rgba(32,31,31,0.6); border: 1px solid rgba(255,215,0,0.15); 
         border-radius: 14px; padding: 20px; text-align: center; margin-bottom: 12px;">
        <div style="font-size: 2.5rem;">📊</div>
        <h4 style="color: #ffd700; margin: 8px 0;">Excel Workbook</h4>
        <p style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 16px;">
            Multi-sheet .xlsx file with all tables.<br>Best for further data analysis.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.download_button(
        label="⬇️  Download Excel (.xlsx)",
        data=excel_data,
        file_name=f"solar_analytics_{site_name}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        use_container_width=True
    )

with col2:
    st.markdown("""
    <div style="background: rgba(32,31,31,0.6); border: 1px solid rgba(74,142,255,0.2);
         border-radius: 14px; padding: 20px; text-align: center; margin-bottom: 12px;">
        <div style="font-size: 2.5rem;">📄</div>
        <h4 style="color: #4a8eff; margin: 8px 0;">PDF Report</h4>
        <p style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 16px;">
            Branded A4 PDF with all analytics.<br>Best for sharing with clients & management.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.download_button(
        label="⬇️  Download PDF Report (.pdf)",
        data=pdf_data,
        file_name=f"solar_analytics_{site_name}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

st.markdown("""
<div style="text-align: center; margin-top: 20px;">
    <p style="color: #64748b; font-size: 0.8rem;">
        Both reports contain identical data. Excel is editable; PDF is print-ready and client-friendly.
    </p>
</div>
""", unsafe_allow_html=True)

