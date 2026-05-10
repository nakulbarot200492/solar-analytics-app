import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from app.styles import inject_global_css

if "ranking_df" not in st.session_state:
    st.warning("Please upload and process data first.")
    st.stop()

st.set_page_config(page_title="Inverter Ranking", page_icon="📊", layout="wide")
inject_global_css()

st.title("📊 Inverter Performance Ranking")

ranking_df = st.session_state["ranking_df"]

if ranking_df.empty:
    st.warning("No inverter data available for ranking. Please upload data and run analysis first.")
    st.stop()

# ── Summary Metrics ─────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    total_energy = ranking_df['Energy_kWh'].sum()
    if total_energy > 0:
        st.metric("Total Energy (kWh)", f"{total_energy:,.2f}")
    else:
        st.metric("Total Inverters", len(ranking_df))
with col2:
    mean_pr = ranking_df['PR_%'].mean()
    st.metric("Avg PR (%)", f"{mean_pr:.2f}%" if pd.notna(mean_pr) else "N/A")
with col3:
    mean_avail = ranking_df['Availability_%'].mean()
    st.metric("Avg Availability", f"{mean_avail:.1f}%" if pd.notna(mean_avail) else "N/A")
with col4:
    if "MPPT_Health" in ranking_df.columns:
        mean_health = ranking_df['MPPT_Health'].mean()
        st.metric("Avg MPPT Health", f"{mean_health:.1f}/100" if pd.notna(mean_health) else "N/A")
    else:
        st.metric("Total Inverters", len(ranking_df))

# ── Methodology ─────────────────────────────────────────────────────────────
with st.expander("ℹ️ How is the ranking calculated?"):
    st.markdown("""
    **Ranking = 60% Performance + 40% MPPT Health**
    
    | Component | Weight | What it measures |
    |-----------|--------|------------------|
    | **Performance Score** | 60% | Energy output (kWh) or Mean Current (A) relative to best inverter |
    | **MPPT Health Score** | 40% | How consistent the MPPT channels are within each inverter |
    
    **MPPT Health Score (0-100):** An inverter where all MPPTs produce similar current scores 100. 
    If one MPPT (e.g., MPPT 6 on A25) produces significantly less current than its peers, the score drops.
    
    **Performance Tiers:** Top 10% and Bottom 10% are based on the composite score.
    """)

# ── Visual: Bar Chart ───────────────────────────────────────────────────────
st.markdown("### Performance Overview")

# Choose the best metric to visualize
if ranking_df['Energy_kWh'].sum() > 0:
    chart_col = "Energy_kWh"
    chart_label = "Energy (kWh)"
elif "Mean_Current_A" in ranking_df.columns and ranking_df['Mean_Current_A'].notna().any():
    chart_col = "Mean_Current_A"
    chart_label = "Mean Current (A)"
else:
    chart_col = "Availability_%"
    chart_label = "Availability (%)"

# Color by tier
color_map = {"Top 10%": "#7bf29d", "Average": "#4a8eff", "Bottom 10%": "#ffb4ab"}

fig = px.bar(
    ranking_df.sort_values("Rank"),
    x="Inverter_ID",
    y=chart_col,
    color="Performance_Tier",
    color_discrete_map=color_map,
    title=f"Inverter {chart_label} by Rank",
    labels={"Inverter_ID": "Inverter", chart_col: chart_label},
)
fig.update_layout(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Space Grotesk"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    xaxis=dict(tickangle=-45),
)
st.plotly_chart(fig, width='stretch')

# ── Ranking Table ───────────────────────────────────────────────────────────
st.markdown("### Ranking Table")

def highlight_tiers(val):
    if val == "Top 10%":
        return "background-color: #064e3b; color: #6ee7b7;"
    elif val == "Bottom 10%":
        return "background-color: #7f1d1d; color: #fca5a5;"
    return ""

def highlight_health(val):
    try:
        v = float(val)
        if v >= 90: return "background-color: #064e3b; color: #6ee7b7;"
        elif v >= 70: return "background-color: #78350f; color: #fde68a;"
        elif v >= 50: return "background-color: #78350f; color: #fbbf24;"
        else: return "background-color: #7f1d1d; color: #fca5a5;"
    except (ValueError, TypeError):
        return ""

styled = ranking_df.style.map(highlight_tiers, subset=["Performance_Tier"])
if "MPPT_Health" in ranking_df.columns:
    styled = styled.map(highlight_health, subset=["MPPT_Health"])

st.dataframe(styled, width='stretch', hide_index=True)

st.download_button(
    label="📥 Download Ranking CSV",
    data=ranking_df.to_csv(index=False).encode('utf-8'),
    file_name="inverter_ranking.csv",
    mime="text/csv",
)
