import streamlit as st
import pandas as pd
import plotly.express as px
from core.mppt_analyzer import build_heatmap_data
from app.styles import inject_global_css

if "cleaned_df" not in st.session_state:
    st.warning("Please upload and process data first.")
    st.stop()

st.set_page_config(page_title="MPPT Analysis", page_icon="⚡", layout="wide")
inject_global_css()

st.title("⚡ MPPT Behavior Analysis")

cleaned_df = st.session_state.get("cleaned_df", pd.DataFrame())
mppt_dev_df = st.session_state.get("mppt_dev_df", pd.DataFrame())
mppt_underperf_df = st.session_state.get("mppt_underperf_df", pd.DataFrame())
mppt_volt_stab_df = st.session_state.get("mppt_volt_stab_df", pd.DataFrame())
mppt_summary_df = st.session_state.get("mppt_summary_df", pd.DataFrame())

if cleaned_df.empty:
    st.warning("Please upload and process data first.")
    st.stop()

if "Inverter_ID" not in cleaned_df.columns:
    st.error("Data error: Inverter_ID column is missing from the cleaned dataset.")
    st.stop()

inverters = list(cleaned_df["Inverter_ID"].unique())
sel_inv = st.selectbox("🔍 Select Inverter to Analyze", inverters)

# ── Underperforming MPPTs ───────────────────────────────────────────────
st.markdown("### Underperforming MPPTs")
inv_underperf = mppt_underperf_df[mppt_underperf_df["Inverter_ID"] == sel_inv] if not mppt_underperf_df.empty and "Inverter_ID" in mppt_underperf_df.columns else None

if inv_underperf is not None and not inv_underperf.empty:
    st.markdown(f"""
    <div style="background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.2); border-radius: 10px; padding: 12px 16px;">
        <p style="margin: 0; color: #fca5a5;">
            ⚠️ Found <strong>{len(inv_underperf)}</strong> consistently underperforming MPPT channel(s) for <strong>{sel_inv}</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.dataframe(inv_underperf, width='stretch', hide_index=True)
else:
    st.markdown(f"""
    <div style="background: rgba(16,185,129,0.08); border: 1px solid rgba(16,185,129,0.2); border-radius: 10px; padding: 12px 16px;">
        <p style="margin: 0; color: #6ee7b7;">
            ✅ No consistently underperforming MPPT channels found for <strong>{sel_inv}</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)

# ── Voltage Stability ───────────────────────────────────────────────────
st.markdown("### Voltage Stability")
if not mppt_volt_stab_df.empty and "Inverter_ID" in mppt_volt_stab_df.columns:
    inv_volt = mppt_volt_stab_df[mppt_volt_stab_df["Inverter_ID"] == sel_inv]
    if not inv_volt.empty:
        st.dataframe(inv_volt, width='stretch', hide_index=True)
    else:
        st.info(f"No voltage stability data for {sel_inv}.")
else:
    st.info("No voltage stability data available.")

# ── Heatmaps ────────────────────────────────────────────────────────────
st.markdown("### MPPT Heatmaps")

metric_choice = st.radio("Select Metric", ["DC_Current_A", "DC_Voltage_V"], horizontal=True)

pivot_df, label = build_heatmap_data(cleaned_df, sel_inv, metric_choice)

if not pivot_df.empty:
    fig = px.imshow(
        pivot_df.T,
        aspect="auto",
        labels=dict(x="Time", y="MPPT ID", color=label),
        title=f"{label} across MPPTs for {sel_inv}",
        color_continuous_scale="Viridis" if metric_choice == "DC_Voltage_V" else "Inferno"
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Space Grotesk"),
    )
    st.plotly_chart(fig, width='stretch')
else:
    st.info("No daylight data available to generate heatmap.")

# ── Summary Stats ───────────────────────────────────────────────────────
st.markdown("### MPPT Summary Stats")
if not mppt_summary_df.empty and "Inverter_ID" in mppt_summary_df.columns:
    inv_summary = mppt_summary_df[mppt_summary_df["Inverter_ID"] == sel_inv]
    if not inv_summary.empty:
        # Deviation bar chart dynamically based on metric selection
        target_col = "Mean_Current_A" if metric_choice == "DC_Current_A" else "Mean_Voltage_V"
        target_label = "Mean Current (A)" if metric_choice == "DC_Current_A" else "Mean Voltage (V)"
        
        if target_col in inv_summary.columns and inv_summary[target_col].notna().any():
            fig_bar = px.bar(
                inv_summary.sort_values("MPPT_ID"),
                x="MPPT_ID",
                y=target_col,
                color=target_col,
                color_continuous_scale="RdYlGn" if metric_choice == "DC_Current_A" else "Viridis",
                title=f"{target_label} per MPPT — {sel_inv}",
                labels={"MPPT_ID": "MPPT Channel", target_col: target_label},
            )
            fig_bar.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Space Grotesk"),
                showlegend=False,
            )
            st.plotly_chart(fig_bar, width='stretch')
        
        st.dataframe(inv_summary, width='stretch', hide_index=True)
    else:
        st.info(f"No summary stats available for {sel_inv}.")
else:
    st.info("No MPPT summary data available.")
