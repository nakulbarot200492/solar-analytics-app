"""
core/mppt_analyzer.py
----------------------
MPPT behavior analysis per inverter.
"""

import pandas as pd
import numpy as np
from typing import Tuple

UNDERPERFORM_DEV_PCT = 0.10
UNDERPERFORM_FREQ_PCT = 0.20
VOLTAGE_CV_THRESHOLD = 0.05


def compute_mppt_deviation(df: pd.DataFrame) -> pd.DataFrame:
    """Per timestamp+inverter: compute each MPPT's % deviation from inverter mean."""
    if df.empty or "Is_Daytime" not in df.columns or not df["Is_Daytime"].any():
        return pd.DataFrame(columns=[
            "Inverter_ID", "MPPT_ID", "Timestamp", "DC_Current_A", 
            "Inv_Mean_Current_A", "Current_Dev_Pct", "DC_Voltage_V", 
            "Inv_Mean_Voltage_V", "Voltage_Dev_Pct"
        ])
    daytime = df[df["Is_Daytime"]].copy()
    records = []
    for (inv_id, ts), grp in daytime.groupby(["Inverter_ID", "Timestamp"]):
        mean_i = grp["DC_Current_A"].mean()
        mean_v = grp["DC_Voltage_V"].mean()
        for _, r in grp.iterrows():
            i_dev = ((r["DC_Current_A"] - mean_i) / mean_i * 100) if mean_i > 0 else np.nan
            v_dev = ((r["DC_Voltage_V"] - mean_v) / mean_v * 100) if mean_v > 0 else np.nan
            records.append({
                "Inverter_ID": inv_id,
                "MPPT_ID": r["MPPT_ID"],
                "Timestamp": ts,
                "DC_Current_A": r["DC_Current_A"],
                "Inv_Mean_Current_A": round(mean_i, 3),
                "Current_Dev_Pct": round(i_dev, 2) if not np.isnan(i_dev) else np.nan,
                "DC_Voltage_V": r["DC_Voltage_V"],
                "Inv_Mean_Voltage_V": round(mean_v, 3),
                "Voltage_Dev_Pct": round(v_dev, 2) if not np.isnan(v_dev) else np.nan,
            })
    if not records:
        return pd.DataFrame(columns=[
            "Inverter_ID", "MPPT_ID", "Timestamp", "DC_Current_A", 
            "Inv_Mean_Current_A", "Current_Dev_Pct", "DC_Voltage_V", 
            "Inv_Mean_Voltage_V", "Voltage_Dev_Pct"
        ])
    return pd.DataFrame(records)


def find_underperforming_mpppts(dev_df: pd.DataFrame) -> pd.DataFrame:
    """Flag MPPTs consistently >10% below inverter mean for >20% of analysis period."""
    if dev_df.empty:
        return pd.DataFrame(columns=["Inverter_ID", "MPPT_ID", "Underperform_Frequency_Pct", "Avg_Current_Dev_Pct", "Status"])
    records = []
    for (inv_id, mppt_id), grp in dev_df.groupby(["Inverter_ID", "MPPT_ID"]):
        total = len(grp)
        if total == 0:
            continue
        underperform = (grp["Current_Dev_Pct"] < -UNDERPERFORM_DEV_PCT * 100).sum()
        freq = underperform / total
        if freq > UNDERPERFORM_FREQ_PCT:
            records.append({
                "Inverter_ID": inv_id,
                "MPPT_ID": mppt_id,
                "Underperform_Frequency_Pct": round(freq * 100, 1),
                "Avg_Current_Dev_Pct": round(grp["Current_Dev_Pct"].mean(), 2),
                "Status": "⚠️ Underperforming",
            })
    if not records:
        return pd.DataFrame(columns=["Inverter_ID", "MPPT_ID", "Underperform_Frequency_Pct", "Avg_Current_Dev_Pct", "Status"])
    result = pd.DataFrame(records)
    if not result.empty:
        result = result.sort_values("Avg_Current_Dev_Pct").reset_index(drop=True)
    return result


def compute_voltage_stability(df: pd.DataFrame) -> pd.DataFrame:
    """Coefficient of variation of DC voltage per MPPT channel."""
    if df.empty or "Is_Daytime" not in df.columns or not df["Is_Daytime"].any():
        return pd.DataFrame(columns=["Inverter_ID", "MPPT_ID", "Voltage_Mean_V", "Voltage_Std_V", "Voltage_CV_Pct", "Status"])
    daytime = df[df["Is_Daytime"]].copy()
    records = []
    for (inv_id, mppt_id), grp in daytime.groupby(["Inverter_ID", "MPPT_ID"]):
        v = grp["DC_Voltage_V"].dropna()
        if len(v) < 3:
            continue
        mean_v = v.mean()
        std_v = v.std()
        cv = std_v / mean_v if mean_v > 0 else np.nan
        records.append({
            "Inverter_ID": inv_id,
            "MPPT_ID": mppt_id,
            "Voltage_Mean_V": round(mean_v, 2),
            "Voltage_Std_V": round(std_v, 3),
            "Voltage_CV_Pct": round(cv * 100, 2) if not np.isnan(cv) else np.nan,
            "Status": "⚠️ Unstable" if (not np.isnan(cv) and cv > VOLTAGE_CV_THRESHOLD) else "✅ Stable",
        })
    if not records:
        return pd.DataFrame(columns=["Inverter_ID", "MPPT_ID", "Voltage_Mean_V", "Voltage_Std_V", "Voltage_CV_Pct", "Status"])
    return pd.DataFrame(records)


def build_heatmap_data(df: pd.DataFrame, inverter_id: str, metric: str = "DC_Current_A") -> Tuple[pd.DataFrame, str]:
    """Pivot table for Plotly heatmap: rows=time, columns=MPPT."""
    inv_data = df[(df["Inverter_ID"] == inverter_id) & df["Is_Daytime"]].copy()
    if inv_data.empty:
        return pd.DataFrame(), metric
    inv_data["Time_Label"] = inv_data["Timestamp"].dt.strftime("%m/%d %H:%M")
    pivot = inv_data.pivot_table(index="Time_Label", columns="MPPT_ID", values=metric, aggfunc="mean")
    label = "Current (A)" if metric == "DC_Current_A" else "Voltage (V)"
    return pivot, label


def get_mppt_summary_per_inverter(df: pd.DataFrame) -> pd.DataFrame:
    """Summary stats per inverter+MPPT."""
    if df.empty:
        return pd.DataFrame(columns=["Inverter_ID", "MPPT_ID", "Mean_Current_A", "Mean_Voltage_V", "DC_Energy_kWh", "Data_Points"])
    ts_sorted = df["Timestamp"].sort_values().drop_duplicates()
    dt_h = ts_sorted.diff().dropna().dt.total_seconds().median() / 3600 if len(ts_sorted) > 1 else 0.25
    records = []
    for (inv_id, mppt_id), grp in df.groupby(["Inverter_ID", "MPPT_ID"]):
        mean_i = grp["DC_Current_A"].mean() if "DC_Current_A" in grp.columns else np.nan
        mean_v = grp["DC_Voltage_V"].mean() if "DC_Voltage_V" in grp.columns else np.nan
        
        records.append({
            "Inverter_ID": inv_id,
            "MPPT_ID": mppt_id,
            "Mean_Current_A": round(mean_i, 3) if not np.isnan(mean_i) else None,
            "Mean_Voltage_V": round(mean_v, 2) if not np.isnan(mean_v) else None,
            "DC_Energy_kWh": round((grp["DC_Power_kW"].fillna(0) * dt_h).sum(), 2) if "DC_Power_kW" in grp.columns else 0.0,
            "Data_Points": len(grp),
        })
    if not records:
        return pd.DataFrame(columns=["Inverter_ID", "MPPT_ID", "Mean_Current_A", "Mean_Voltage_V", "DC_Energy_kWh", "Data_Points"])
    return pd.DataFrame(records)
