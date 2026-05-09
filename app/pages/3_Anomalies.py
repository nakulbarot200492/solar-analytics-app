import streamlit as st
import pandas as pd
import plotly.express as px
from core.anomaly_detector import run_all_detectors, get_anomaly_summary
from core.rca_engine import apply_rca
from app.styles import inject_global_css

if "cleaned_df" not in st.session_state:
    st.warning("Please upload and process data first.")
    st.stop()

st.set_page_config(page_title="Anomalies", page_icon="⚠️", layout="wide")
inject_global_css()

st.title("⚠️ Anomaly Detection")

# ── Force fresh analysis ────────────────────────────────────────────────────
with st.status("🔍 Running anomaly detection...", expanded=False) as status:
    cdf = st.session_state["cleaned_df"]
    raw_anomalies = run_all_detectors(cdf)
    
    if not raw_anomalies.empty:
        anomaly_df = apply_rca(raw_anomalies)
    else:
        anomaly_df = raw_anomalies
    
    st.session_state["anomaly_df"] = anomaly_df
    status.update(label=f"✅ Found {len(anomaly_df)} events", state="complete")

if anomaly_df.empty:
    st.markdown("""
    <div style="background: rgba(16,185,129,0.08); border: 1px solid rgba(16,185,129,0.2); border-radius: 12px; padding: 24px; text-align: center;">
        <p style="font-size: 2rem; margin: 0;">✅</p>
        <h3 style="color: #6ee7b7; margin: 8px 0;">No Anomalies Detected</h3>
        <p style="color: #94a3b8; margin: 0;">
            The dataset contains {len(cdf)} rows across {cdf['Inverter_ID'].nunique()} inverter(s) 
            and {cdf['MPPT_ID'].nunique()} MPPT(s). All readings are within normal parameters.
        </p>
    </div>
    """.format(), unsafe_allow_html=True)
    st.stop()

# ── Summary Metrics ─────────────────────────────────────────────────────────
high_sev = len(anomaly_df[anomaly_df["Severity"] == "HIGH"])
med_sev = len(anomaly_df[anomaly_df["Severity"] == "MEDIUM"])
low_sev = len(anomaly_df[anomaly_df["Severity"] == "LOW"])
total_loss = anomaly_df["kWh_Loss_Est"].sum() if "kWh_Loss_Est" in anomaly_df.columns else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("🔴 High Severity", high_sev)
col2.metric("🟠 Medium Severity", med_sev)
col3.metric("🟡 Low Severity", low_sev)
col4.metric("⚡ Est. Loss (kWh)", f"{total_loss:.2f}")

# ── Data context ────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background: rgba(59,130,246,0.06); border: 1px solid rgba(59,130,246,0.15); border-radius: 10px; padding: 12px 16px; margin: 16px 0;">
    <p style="margin: 0; color: #93c5fd; font-size: 0.85rem;">
        📊 Analyzing <strong>{len(cdf)}</strong> data points across 
        <strong>{cdf['Inverter_ID'].nunique()}</strong> inverters
    </p>
</div>
""", unsafe_allow_html=True)

# ── Timeline Chart ──────────────────────────────────────────────────────────
st.markdown("### Anomaly Timeline")
fig = px.scatter(
    anomaly_df,
    x="Timestamp",
    y="Inverter_ID",
    color="Severity",
    size_max=12,
    hover_data=["Anomaly_Type", "Detail", "kWh_Loss_Est"] if "kWh_Loss_Est" in anomaly_df.columns else ["Anomaly_Type", "Detail"],
    color_discrete_map={"HIGH": "#ef4444", "MEDIUM": "#f59e0b", "LOW": "#fbbf24"},
)
fig.update_layout(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter"),
    xaxis_title="Timestamp",
    yaxis_title="Inverter",
)
fig.update_traces(marker=dict(size=10, line=dict(width=1, color="rgba(0,0,0,0.3)")))
st.plotly_chart(fig, width='stretch')

# ── Summary Table ───────────────────────────────────────────────────────────
st.markdown("### Summary by Anomaly Type")
summary_df = get_anomaly_summary(anomaly_df)
st.dataframe(summary_df, width='stretch', hide_index=True)

# ── Detailed Log ────────────────────────────────────────────────────────────
st.markdown("### Detailed Anomaly Log")

inverters = ["All"] + list(anomaly_df["Inverter_ID"].unique())
sel_inv = st.selectbox("Filter by Inverter", inverters)

filtered_df = anomaly_df if sel_inv == "All" else anomaly_df[anomaly_df["Inverter_ID"] == sel_inv]

st.dataframe(filtered_df, width='stretch', hide_index=True)

st.download_button(
    label="📥 Download Anomaly Log CSV",
    data=filtered_df.to_csv(index=False).encode('utf-8'),
    file_name="anomaly_log.csv",
    mime="text/csv",
)
