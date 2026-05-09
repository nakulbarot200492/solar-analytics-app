"""
core/inverter_ranking.py
------------------------
Compute inverter-wise performance metrics and produce a ranked table.

Metrics (per PRD):
  Primary:   Total Energy Generated (kWh), Performance Ratio (PR)
  Secondary: DC-AC Efficiency, Availability (%)
  Tertiary:  Specific Yield (kWh/kWp)  ← requires installed_kwp dict
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict


def compute_time_interval_hours(df: pd.DataFrame) -> float:
    """Estimate the median timestep in hours from the dataset."""
    timestamps = df["Timestamp"].sort_values().drop_duplicates()
    if len(timestamps) < 2:
        return 0.25  # assume 15-min default
    deltas = timestamps.diff().dropna().dt.total_seconds() / 3600
    return float(deltas.median())


def compute_ranking(
    df: pd.DataFrame,
    installed_kwp: Optional[Dict[str, float]] = None,
) -> pd.DataFrame:
    """
    Compute inverter-level metrics and return a ranked DataFrame.
    """
    if df.empty:
        return pd.DataFrame(columns=["Inverter_ID", "Energy_kWh", "PR_%", "DC_AC_Efficiency_%", "Availability_%", "Specific_Yield_kWhkWp", "Rank", "Performance_Tier"])
    
    dt_h = compute_time_interval_hours(df)
    total_hours = (df["Timestamp"].max() - df["Timestamp"].min()).total_seconds() / 3600

    records = []
    for inv_id, grp in df.groupby("Inverter_ID"):
        # Skip empty groups
        if grp.empty:
            continue

        # Collapse to inverter-level (sum MPPT values for DC, use AC_Power_kW as-is)
        agg_map = {}
        if "AC_Power_kW" in grp.columns and not grp["AC_Power_kW"].isna().all():
            agg_map["AC_Power_kW"] = "first"
        if "DC_Power_kW" in grp.columns and not grp["DC_Power_kW"].isna().all():
            agg_map["DC_Power_kW"] = "sum"
        if "Irradiance_Wm2" in grp.columns and not grp["Irradiance_Wm2"].isna().all():
            agg_map["Irradiance_Wm2"] = "mean"
        if "DC_Current_A" in grp.columns and not grp["DC_Current_A"].isna().all():
            agg_map["DC_Current_A"] = "sum"
        if "DC_Voltage_V" in grp.columns and not grp["DC_Voltage_V"].isna().all():
            agg_map["DC_Voltage_V"] = "mean"

        # If no columns to aggregate, skip this inverter
        if not agg_map:
            continue

        # Ensure we have Timestamp column and data
        if "Timestamp" not in grp.columns or grp["Timestamp"].isna().all():
            continue

        try:
            # Group by Timestamp and aggregate
            inv_ts = grp.groupby("Timestamp").agg(agg_map).reset_index()
            
            if inv_ts.empty:
                continue
        except (ValueError, KeyError, TypeError) as e:
            # Skip this inverter if aggregation fails
            continue
        
        # Ensure all columns exist in inv_ts even if they were missing from grp
        for c in ["AC_Power_kW", "DC_Power_kW", "Irradiance_Wm2"]:
            if c not in inv_ts.columns:
                inv_ts[c] = np.nan

        # ── Total Energy Generated (kWh) ────────────────────────────────────
        # Fallback chain: AC_Power → DC_Power → estimate from V×I
        if inv_ts["AC_Power_kW"].notna().any():
            p_col = "AC_Power_kW"
        elif inv_ts["DC_Power_kW"].notna().any():
            p_col = "DC_Power_kW"
        else:
            p_col = None
        
        if p_col:
            energy_kwh = (inv_ts[p_col].fillna(0) * dt_h).sum()
        else:
            energy_kwh = 0.0

        # ── Mean Current (fallback metric when no power) ─────────────────────
        mean_current = np.nan
        if "DC_Current_A" in inv_ts.columns and inv_ts["DC_Current_A"].notna().any():
            mean_current = inv_ts["DC_Current_A"].fillna(0).mean()

        # ── Availability (%) ─────────────────────────────────────────────────
        if p_col:
            uptime_steps = (inv_ts[p_col].fillna(0) > 0).sum()
        elif "DC_Current_A" in inv_ts.columns and inv_ts["DC_Current_A"].notna().any():
            uptime_steps = (inv_ts["DC_Current_A"].fillna(0) > 0).sum()
        else:
            uptime_steps = 0
        total_steps = len(inv_ts)
        availability_pct = (uptime_steps / total_steps * 100) if total_steps > 0 else 0

        # ── DC-AC Efficiency ─────────────────────────────────────────────────
        dc_sum = inv_ts["DC_Power_kW"].replace(0, np.nan).fillna(np.nan)
        ac_sum = inv_ts["AC_Power_kW"].replace(0, np.nan).fillna(np.nan)
        valid = ac_sum.notna() & dc_sum.notna() & (dc_sum > 0)
        if valid.any():
            efficiency = (ac_sum[valid] / dc_sum[valid]).mean() * 100
        else:
            efficiency = np.nan

        # ── Performance Ratio (PR) ────────────────────────────────────────────
        has_irradiance = inv_ts["Irradiance_Wm2"].notna().any()
        kWp = (installed_kwp or {}).get(inv_id, None)
        if has_irradiance and kWp:
            expected_kwh = ((inv_ts["Irradiance_Wm2"].fillna(0) / 1000) * kWp * dt_h).sum()
            pr = (energy_kwh / expected_kwh * 100) if expected_kwh > 0 else np.nan
        else:
            pr = np.nan

        # ── Specific Yield ────────────────────────────────────────────────────
        specific_yield = (energy_kwh / kWp) if kWp else np.nan

        # ── MPPT Health Score (0-100) ─────────────────────────────────────────
        # Measures how consistent the MPPT channels are within this inverter.
        # An inverter with one badly underperforming MPPT gets a lower score.
        mppt_health = 100.0
        mppt_means = grp.groupby("MPPT_ID")["DC_Current_A"].mean().dropna()
        if len(mppt_means) >= 2:
            median_i = mppt_means.median()
            if median_i > 0.01:
                # Deviation of each MPPT from the median
                deviations = ((mppt_means - median_i) / median_i).abs()
                # Worst MPPT deviation (e.g., 0.5 means 50% below median)
                worst_dev = deviations.max()
                # Mean deviation across all MPPTs
                mean_dev = deviations.mean()
                # Score: 100 = perfect, penalize by worst and mean deviation
                mppt_health = max(0, 100 - (worst_dev * 60) - (mean_dev * 40))
                mppt_health = round(mppt_health, 1)

        records.append({
            "Inverter_ID": inv_id,
            "Energy_kWh": round(energy_kwh, 2),
            "Mean_Current_A": round(mean_current, 2) if not np.isnan(mean_current) else np.nan,
            "PR_%": round(pr, 2) if not np.isnan(pr) else np.nan,
            "DC_AC_Efficiency_%": round(efficiency, 2) if not np.isnan(efficiency) else np.nan,
            "Availability_%": round(availability_pct, 2),
            "MPPT_Health": mppt_health,
            "Specific_Yield_kWhkWp": round(specific_yield, 3) if not np.isnan(specific_yield) else np.nan,
        })

    if not records:
        return pd.DataFrame(columns=["Inverter_ID", "Energy_kWh", "Mean_Current_A", "PR_%", "DC_AC_Efficiency_%", "Availability_%", "MPPT_Health", "Specific_Yield_kWhkWp", "Rank", "Performance_Tier"])
    result = pd.DataFrame(records)

    # ── Relative PR fallback (when no irradiance / kWp) ──────────────────────
    pr_missing = result["PR_%"].isna()
    if pr_missing.all():
        # Use energy if available, otherwise mean current
        if result["Energy_kWh"].sum() > 0:
            site_mean = result["Energy_kWh"].mean()
            if site_mean > 0:
                result.loc[pr_missing, "PR_%"] = (
                    result.loc[pr_missing, "Energy_kWh"] / site_mean * 100
                ).round(2)
        elif result["Mean_Current_A"].notna().any():
            site_mean_i = result["Mean_Current_A"].mean()
            if site_mean_i > 0:
                result.loc[pr_missing, "PR_%"] = (
                    result.loc[pr_missing, "Mean_Current_A"] / site_mean_i * 100
                ).round(2)

    # ── Composite Score for Ranking ──────────────────────────────────────────
    # Combines energy/current performance with MPPT health
    # This ensures inverters with weak MPPTs rank lower
    if result["Energy_kWh"].sum() > 0:
        max_e = result["Energy_kWh"].max()
        result["_perf_score"] = (result["Energy_kWh"] / max_e * 100) if max_e > 0 else 0
    elif result["Mean_Current_A"].notna().any():
        max_i = result["Mean_Current_A"].max()
        result["_perf_score"] = (result["Mean_Current_A"] / max_i * 100) if max_i > 0 else 0
    else:
        result["_perf_score"] = result["Availability_%"]

    # Weighted composite: 60% performance + 40% MPPT health
    result["_composite"] = result["_perf_score"] * 0.6 + result["MPPT_Health"] * 0.4

    # ── Rank by composite score ──────────────────────────────────────────────
    result = result.sort_values("_composite", ascending=False).reset_index(drop=True)
    result["Rank"] = result.index + 1

    # ── Performance tier ──────────────────────────────────────────────────────
    n = len(result)
    top_cutoff = max(1, int(np.ceil(n * 0.10)))
    bot_cutoff = max(1, int(np.ceil(n * 0.10)))
    result["Performance_Tier"] = "Average"
    result.loc[result["Rank"] <= top_cutoff, "Performance_Tier"] = "Top 10%"
    result.loc[result["Rank"] > n - bot_cutoff, "Performance_Tier"] = "Bottom 10%"

    # Drop internal scoring columns
    result = result.drop(columns=["_perf_score", "_composite"])

    return result
