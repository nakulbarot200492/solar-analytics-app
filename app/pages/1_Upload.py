import streamlit as st
import pandas as pd
import sys
import os

# Add project root to sys.path for core module imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.data_loader import load_excel, get_column_summary, validate_bounds, get_site_info
from core.data_cleaner import clean, get_audit_summary
from core.inverter_ranking import compute_ranking
from core.anomaly_detector import run_all_detectors, get_anomaly_summary
from core.mppt_analyzer import compute_mppt_deviation, find_underperforming_mpppts, compute_voltage_stability, get_mppt_summary_per_inverter
from core.rca_engine import apply_rca, get_rca_summary
from app.styles import inject_global_css

st.set_page_config(page_title="Data Upload", page_icon="📁", layout="wide")
inject_global_css()

st.title("📁 Data Upload & Processing")

st.markdown("""
<div style="background: rgba(247,183,49,0.06); border: 1px solid rgba(247,183,49,0.15); border-radius: 12px; padding: 16px 20px; margin-bottom: 24px;">
    <p style="margin: 0; color: #e2e8f0; font-size: 0.9rem;">
        📤 Upload Excel files containing SMA inverter data. The system will auto-detect column formats,
        clean the data, and generate all analytics.
    </p>
</div>
""", unsafe_allow_html=True)

uploaded_files = st.file_uploader("Choose Excel files (.xlsx, .xls)", type=["xlsx", "xls"], accept_multiple_files=True)

if uploaded_files:
    # ── 1. Load Data ────────────────────────────────────────────────────────
    st.markdown("### 1. Data Loading")
    
    raw_df = None
    all_warnings = []
    
    for uf in uploaded_files:
        with st.spinner(f"Parsing {uf.name}..."):
            try:
                df, warnings = load_excel(uf)
                
                if df.empty:
                    st.error(f"Failed to load {uf.name}:")
                    for w in warnings:
                        st.markdown(f"- {w}")
                    
                    with st.expander("🛠️ How to Fix This Error"):
                        st.markdown("""
                        **The system could not recognize your file format.**
                        
                        **Checklist:**
                        1. **File Type:** Ensure you are uploading `.xlsx`, `.xls`, or `.csv`.
                        2. **Headers:** Does your file have a header row? The system looks for:
                           - Time/Timestamp columns
                           - Voltage/Current/Power columns
                        3. **SMA Format:** If it's an SMA Sunny Portal export, ensure it's the 'Detailed' report type.
                        4. **Encrypted Files:** If the Excel file is password protected, the system cannot read it.
                        
                        **Example Supported Headers:**
                        `Timestamp, Inverter, MPPT, DC Voltage, DC Current, DC Power`
                        """)
                    st.stop()

                all_warnings.extend(warnings)
                
                if raw_df is None:
                    raw_df = df
                else:
                    raw_df = pd.concat([raw_df, df], ignore_index=True)
                    raw_df = raw_df.drop_duplicates(subset=["Timestamp", "Inverter_ID", "MPPT_ID"], keep="first")
                
    st.session_state["raw_df"] = raw_df
    
    # Auto-calculate power if we have both V and I
    if "DC_Current_A" in raw_df.columns and "DC_Voltage_V" in raw_df.columns:
        if "DC_Power_kW" not in raw_df.columns or raw_df["DC_Power_kW"].isna().all():
            raw_df["DC_Power_kW"] = (raw_df["DC_Voltage_V"] * raw_df["DC_Current_A"]) / 1000
            all_warnings.append("⚠️ Auto-calculated DC_Power_kW from Voltage and Current.")
            
    for w in set(all_warnings):
        st.warning(w)
        
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Site Overview")
        info = get_site_info(raw_df)
        for k, v in info.items():
            st.markdown(f"**{k}:** {v}")
    with col2:
        st.markdown("#### Data Summary")
        st.dataframe(get_column_summary(raw_df), width="stretch", hide_index=True)
        
    bounds_warnings = validate_bounds(raw_df)
    for bw in bounds_warnings:
        st.warning(bw)
        
    # ── 2. Clean Data ───────────────────────────────────────────────────────
    st.markdown("### 2. Data Cleaning")
    with st.spinner("Cleaning and structuring data..."):
        cleaned_df, audit = clean(raw_df)
        st.session_state["cleaned_df"] = cleaned_df
        
    st.markdown(get_audit_summary(audit))
    
    with st.expander("🔍 Data Pipeline Health (Diagnostics)"):
        diag_col1, diag_col2 = st.columns(2)
        with diag_col1:
            st.write("**Row Count Progression**")
            prog_df = pd.DataFrame({
                "Stage": ["1. Raw Upload", "2. After ID Mapping", "3. After Cleaning"],
                "Rows": [len(st.session_state.get("raw_df", [])), len(raw_df), len(cleaned_df)]
            })
            st.table(prog_df)
            
            if len(cleaned_df) < len(raw_df):
                st.warning(f"Note: {len(raw_df) - len(cleaned_df)} rows were filtered out. Check 'Rows dropped' in Audit Summary.")
                
        with diag_col2:
            st.write("**Column Schema Check**")
            schema_check = {
                "Inverter_ID": "✅ Found" if "Inverter_ID" in cleaned_df.columns else "❌ Missing",
                "MPPT_ID": "✅ Found" if "MPPT_ID" in cleaned_df.columns else "❌ Missing",
                "DC_Voltage_V": "✅ Found" if "DC_Voltage_V" in cleaned_df.columns else "⚠️ Missing",
                "DC_Current_A": "✅ Found" if "DC_Current_A" in cleaned_df.columns else "⚠️ Missing",
                "DC_Power_kW": "✅ Found" if "DC_Power_kW" in cleaned_df.columns else "⚠️ Missing",
            }
            st.json(schema_check)
            
        st.write("**Raw Columns Found in File:**")
        st.code(", ".join(st.session_state.get("raw_df", pd.DataFrame()).columns.tolist()))
            
        if len(cleaned_df) == 0 and len(raw_df) > 0:
            st.error("🚨 **CRITICAL:** All data was dropped during cleaning. This usually happens if timestamps are invalid or all data is during night hours.")

    # ── 3. Run Analytics Pipeline ───────────────────────────────────────────
    st.markdown("### 3. Analytics Pipeline")
    
    if st.button("▶️  Run Analysis", type="primary"):
        with st.status("Running complete analytics pipeline...", expanded=True) as status:
            # Ranking
            st.write("📊 Computing Inverter Rankings...")
            ranking_df = compute_ranking(cleaned_df)
            st.session_state["ranking_df"] = ranking_df
            
            # Anomalies
            st.write("🔍 Detecting Anomalies...")
            anomaly_df = run_all_detectors(cleaned_df)
            st.session_state["raw_anomaly_df"] = anomaly_df
            
            # RCA
            st.write("🛠️ Applying Root Cause Analysis...")
            rca_df = apply_rca(anomaly_df)
            st.session_state["anomaly_df"] = rca_df
            
            # MPPT Analysis
            st.write("⚡ Analyzing MPPT Behavior...")
            dev_df = compute_mppt_deviation(cleaned_df)
            st.session_state["mppt_dev_df"] = dev_df
            
            underperf_df = find_underperforming_mpppts(dev_df)
            st.session_state["mppt_underperf_df"] = underperf_df
            
            volt_stab_df = compute_voltage_stability(cleaned_df)
            st.session_state["mppt_volt_stab_df"] = volt_stab_df
            
            mppt_summary_df = get_mppt_summary_per_inverter(cleaned_df)
            st.session_state["mppt_summary_df"] = mppt_summary_df
            
            status.update(label="✅ Analytics complete!", state="complete", expanded=False)
            
        st.success("🎉 Analysis complete! Explore results using the sidebar navigation.")
