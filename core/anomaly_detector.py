"""
core/anomaly_detector.py
------------------------
Rule-based anomaly detection engine (8 anomaly types per PRD).

All detectors operate on the cleaned DataFrame and return a unified
anomaly log DataFrame with columns:
  Timestamp, Inverter_ID, MPPT_ID, Anomaly_Type, Severity,
  Layer, Detail, kWh_Loss_Est
"""

import pandas as pd
import numpy as np
from typing import List, Optional

# ── Thresholds (match PRD exactly) ───────────────────────────────────────────
DAYTIME_START = 8
DAYTIME_END   = 18
NIGHTTIME_START = 20
NIGHTTIME_END   = 6
IRRADIANCE_THRESHOLD = 50       # W/m² — if above this, should be generating
POWER_DROP_PCT = 0.40           # 40% drop in single timestep = sudden drop
MPPT_CURRENT_MISMATCH_PCT = 0.20  # >20% deviation from inverter mean
FLATLINE_STD_THRESHOLD = 0.05   # std dev < 0.05 A = flatline
FLATLINE_MIN_DURATION_MIN = 30  # flatline must persist > 30 minutes
VI_MISMATCH_PCT = 0.15          # V×I vs DC_Power_kW > 15%
VOLTAGE_IMBALANCE_PCT = 0.05    # MPPT voltage > 5% from inverter mean
VOLTAGE_INSTABILITY_CV = 0.05   # Coeff of Variation > 5% = unstable


def _make_row(ts, inv_id, mppt_id, atype, severity, layer, detail, kwh_loss=0.0):
    return {
        "Timestamp": ts,
        "Inverter_ID": inv_id,
        "MPPT_ID": mppt_id,
        "Anomaly_Type": atype,
        "Severity": severity,
        "Layer": layer,
        "Detail": detail,
        "kWh_Loss_Est": round(kwh_loss, 4),
    }


# ── Helper: inverter-level time series ───────────────────────────────────────
def _inverter_ts(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse MPPT rows to inverter-level per timestamp."""
    if df.empty:
        return pd.DataFrame(columns=["Inverter_ID", "Timestamp", "AC_Power_kW", "DC_Power_kW", "Irradiance_Wm2", "Hour", "Is_Daytime"])
        
    agg_map = {}
    if "AC_Power_kW" in df.columns: agg_map["AC_Power_kW"] = "first"
    if "DC_Power_kW" in df.columns: agg_map["DC_Power_kW"] = "sum"
    if "Irradiance_Wm2" in df.columns: agg_map["Irradiance_Wm2"] = "mean"
    if "Hour" in df.columns: agg_map["Hour"] = "first"
    if "Is_Daytime" in df.columns: agg_map["Is_Daytime"] = "first"
    
    if not agg_map:
        return pd.DataFrame(columns=["Inverter_ID", "Timestamp"])

    res = (
        df.groupby(["Inverter_ID", "Timestamp"])
        .agg(agg_map)
        .reset_index()
        .sort_values(["Inverter_ID", "Timestamp"])
    )
    
    # Fill in missing columns with NaN to avoid KeyErrors downstream
    for c in ["AC_Power_kW", "DC_Power_kW", "Irradiance_Wm2", "Hour", "Is_Daytime"]:
        if c not in res.columns:
            res[c] = np.nan
            
    return res


def _dt_hours(df: pd.DataFrame) -> float:
    ts = df["Timestamp"].sort_values().drop_duplicates()
    if len(ts) < 2:
        return 0.25
    return float(ts.diff().dropna().dt.total_seconds().median() / 3600)


# ─────────────────────────────────────────────────────────────────────────────
# Anomaly 1: Zero Generation (Daytime)                             [HIGH]
# ─────────────────────────────────────────────────────────────────────────────
def detect_zero_generation(df: pd.DataFrame, dt_h: float) -> List[dict]:
    rows = []
    inv_ts = _inverter_ts(df)
    has_irr = inv_ts["Irradiance_Wm2"].notna().any()

    for inv_id, grp in inv_ts.groupby("Inverter_ID"):
        grp = grp.copy()
        if has_irr:
            mask = (grp["AC_Power_kW"].fillna(0) == 0) & (
                (grp["Irradiance_Wm2"].fillna(0) > IRRADIANCE_THRESHOLD) |
                grp["Is_Daytime"]
            )
        else:
            mask = (grp["AC_Power_kW"].fillna(0) == 0) & grp["Is_Daytime"]

        for _, r in grp[mask].iterrows():
            irr = r.get("Irradiance_Wm2", np.nan)
            detail = f"AC=0 kW at {r['Hour']:02d}:xx, Irr={irr:.0f} W/m²" if not np.isnan(irr) else f"AC=0 kW at {r['Hour']:02d}:xx"
            rows.append(_make_row(
                r["Timestamp"], inv_id, "ALL", "Zero Generation (Daytime)",
                "HIGH", "Inverter", detail,
                kwh_loss=0  # expected power unknown without reference
            ))
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# Anomaly 2: Sudden Power Drop                                      [HIGH]
# ─────────────────────────────────────────────────────────────────────────────
def detect_sudden_power_drop(df: pd.DataFrame, dt_h: float) -> List[dict]:
    rows = []
    inv_ts = _inverter_ts(df)

    for inv_id, grp in inv_ts.groupby("Inverter_ID"):
        grp = grp.sort_values("Timestamp").copy()
        ac = grp["AC_Power_kW"].fillna(0)
        irr = grp["Irradiance_Wm2"].fillna(0)

        prev_ac = ac.shift(1)
        prev_irr = irr.shift(1)
        drop_pct = (prev_ac - ac) / prev_ac.replace(0, np.nan)

        irr_drop = (prev_irr - irr) / prev_irr.replace(0, np.nan)
        mask = (
            (drop_pct > POWER_DROP_PCT) &
            (prev_ac > 0) &
            (irr_drop < POWER_DROP_PCT)  # no corresponding irradiance drop
        )

        for idx in grp.index[mask]:
            r = grp.loc[idx]
            p_before = prev_ac.loc[idx]
            p_after = ac.loc[idx]
            kwh_loss = (p_before - p_after) * dt_h
            detail = f"Drop from {p_before:.2f}→{p_after:.2f} kW ({drop_pct.loc[idx]*100:.1f}%)"
            rows.append(_make_row(
                r["Timestamp"], inv_id, "ALL", "Sudden Power Drop",
                "HIGH", "Inverter", detail, kwh_loss
            ))
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# Anomaly 3: MPPT Current Mismatch                                  [MEDIUM]
# ─────────────────────────────────────────────────────────────────────────────
def detect_mppt_current_mismatch(df: pd.DataFrame, dt_h: float) -> List[dict]:
    """Flag MPPTs with significant current deviation from inverter peers (Daily Aggregate)."""
    rows = []
    for inv_id, inv_grp in df.groupby("Inverter_ID"):
        stats = []
        for mppt_id, mppt_grp in inv_grp.groupby("MPPT_ID"):
            stats.append({
                "MPPT_ID": mppt_id,
                "Mean_I": mppt_grp["DC_Current_A"].mean(),
                "TS": mppt_grp["Timestamp"].iloc[0] if not mppt_grp.empty else None
            })
        if len(stats) < 2: continue
        
        if not stats or all(pd.isna(s["Mean_I"]) for s in stats): continue
        median_i = np.median([s["Mean_I"] for s in stats if pd.notna(s["Mean_I"])])
        if pd.isna(median_i) or median_i < 0.1: continue
        
        for s in stats:
            if pd.isna(s["Mean_I"]): continue
            dev = abs(s["Mean_I"] - median_i) / median_i
            if dev > MPPT_CURRENT_MISMATCH_PCT:
                detail = f"MPPT {s['MPPT_ID']} daily avg current ({s['Mean_I']:.2f}A) deviates {dev*100:.1f}% from inverter median ({median_i:.2f}A)"
                rows.append(_make_row(
                    s["TS"], inv_id, s["MPPT_ID"], "MPPT Current Mismatch",
                    "MEDIUM", "MPPT", detail
                ))
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# Anomaly 4: Flatline Current                                        [MEDIUM]
# ─────────────────────────────────────────────────────────────────────────────
def detect_flatline_current(df: pd.DataFrame, dt_h: float) -> List[dict]:
    rows = []
    window_steps = max(2, int(FLATLINE_MIN_DURATION_MIN / (dt_h * 60)))

    for (inv_id, mppt_id), grp in df.groupby(["Inverter_ID", "MPPT_ID"]):
        grp = grp.sort_values("Timestamp").copy()
        daytime = grp[grp["Is_Daytime"]].copy()
        if len(daytime) < window_steps:
            continue

        curr = daytime["DC_Current_A"].fillna(0)
        rolling_std = curr.rolling(window=window_steps).std()
        flatline_mask = rolling_std < FLATLINE_STD_THRESHOLD

        # Group consecutive flatlines
        in_flatline = False
        for idx, is_flat in zip(daytime.index, flatline_mask):
            if is_flat and not in_flatline:
                in_flatline = True
                start_ts = daytime.loc[idx, "Timestamp"]
                val = daytime.loc[idx, "DC_Current_A"]
            elif not is_flat and in_flatline:
                in_flatline = False
                rows.append(_make_row(
                    start_ts, inv_id, mppt_id, "Flatline Current",
                    "MEDIUM", "MPPT",
                    f"Current flatlined at {val:.3f} A for >{FLATLINE_MIN_DURATION_MIN} min"
                ))
        if in_flatline:
            rows.append(_make_row(
                start_ts, inv_id, mppt_id, "Flatline Current",
                "MEDIUM", "MPPT",
                f"Current flatlined at {val:.3f} A (ongoing)"
            ))
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# Anomaly 5: Voltage-Current Mismatch                               [MEDIUM]
# ─────────────────────────────────────────────────────────────────────────────
def detect_vi_mismatch(df: pd.DataFrame, dt_h: float) -> List[dict]:
    rows = []
    if "VI_Power_Mismatch" not in df.columns:
        return rows
    mismatch = df[df["VI_Power_Mismatch"] == True]
    for _, r in mismatch.iterrows():
        vi = (r["DC_Voltage_V"] * r["DC_Current_A"]) / 1000
        detail = f"V×I={vi:.3f} kW vs DC_Power={r['DC_Power_kW']:.3f} kW"
        rows.append(_make_row(
            r["Timestamp"], r["Inverter_ID"], r["MPPT_ID"],
            "Voltage-Current Mismatch", "MEDIUM", "MPPT", detail
        ))
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# Anomaly 6: Voltage Imbalance                                       [LOW]
# ─────────────────────────────────────────────────────────────────────────────
def detect_voltage_imbalance(df: pd.DataFrame, dt_h: float) -> List[dict]:
    """Flag MPPTs with significant voltage deviation from inverter peers (Daily Aggregate)."""
    rows = []
    for inv_id, inv_grp in df.groupby("Inverter_ID"):
        stats = []
        for mppt_id, mppt_grp in inv_grp.groupby("MPPT_ID"):
            stats.append({
                "MPPT_ID": mppt_id,
                "Mean_V": mppt_grp["DC_Voltage_V"].mean(),
                "TS": mppt_grp["Timestamp"].iloc[0] if not mppt_grp.empty else None
            })
        if len(stats) < 2: continue
        
        if not stats or all(pd.isna(s["Mean_V"]) for s in stats): continue
        median_v = np.median([s["Mean_V"] for s in stats if pd.notna(s["Mean_V"])])
        if pd.isna(median_v) or median_v < 10: continue
        
        for s in stats:
            if pd.isna(s["Mean_V"]): continue
            dev = abs(s["Mean_V"] - median_v) / median_v
            if dev > VOLTAGE_IMBALANCE_PCT:
                detail = f"MPPT {s['MPPT_ID']} daily avg voltage ({s['Mean_V']:.1f}V) deviates {dev*100:.1f}% from inverter median ({median_v:.1f}V)"
                rows.append(_make_row(
                    s["TS"], inv_id, s["MPPT_ID"], "Voltage Imbalance",
                    "LOW", "MPPT", detail
                ))
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# Anomaly 7: Clipping Event                                          [LOW]
# ─────────────────────────────────────────────────────────────────────────────
def detect_clipping(df: pd.DataFrame, dt_h: float) -> List[dict]:
    rows = []
    inv_ts = _inverter_ts(df)

    for inv_id, grp in inv_ts.groupby("Inverter_ID"):
        grp = grp.sort_values("Timestamp").copy()
        ac = grp["AC_Power_kW"].fillna(0)
        dc = grp["DC_Power_kW"].fillna(0)

        rated = ac.quantile(0.98)  # approx rated capacity
        if rated == 0:
            continue

        dc_rising = dc.diff() > 0
        ac_at_rated = ac >= rated * 0.98  # within 2% of rated

        mask = ac_at_rated & dc_rising
        for _, r in grp[mask].iterrows():
            detail = f"AC={r['AC_Power_kW']:.2f} kW (≈rated {rated:.2f} kW) while DC rising"
            rows.append(_make_row(
                r["Timestamp"], inv_id, "ALL", "Clipping Event",
                "LOW", "Inverter", detail
            ))
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# Anomaly 8: Night-time Generation                                   [LOW]
# ─────────────────────────────────────────────────────────────────────────────
def detect_nighttime_generation(df: pd.DataFrame, dt_h: float) -> List[dict]:
    rows = []
    inv_ts = _inverter_ts(df)

    night_mask = (inv_ts["Hour"] >= NIGHTTIME_START) | (inv_ts["Hour"] < NIGHTTIME_END)
    nonzero_ac = inv_ts["AC_Power_kW"].fillna(0) > 0
    nonzero_dc = inv_ts["DC_Power_kW"].fillna(0) > 0

    flagged = inv_ts[night_mask & (nonzero_ac | nonzero_dc)]
    for _, r in flagged.iterrows():
        detail = f"AC={r['AC_Power_kW']:.3f}, DC={r['DC_Power_kW']:.3f} kW at {r['Hour']:02d}:xx"
        rows.append(_make_row(
            r["Timestamp"], r["Inverter_ID"], "ALL", "Night-time Generation",
            "LOW", "Inverter", detail
        ))
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# Anomaly 9: Voltage Instability                                     [LOW]
# ─────────────────────────────────────────────────────────────────────────────
def detect_voltage_instability(df: pd.DataFrame, dt_h: float) -> List[dict]:
    """Flag MPPTs with high temporal variance in DC Voltage during daytime."""
    rows = []
    # Need at least 1 hour of data to compute stability
    min_points = max(4, int(1.0 / dt_h))
    
    for (inv_id, mppt_id), grp in df.groupby(["Inverter_ID", "MPPT_ID"]):
        daytime = grp[grp["Is_Daytime"] | (grp["DC_Power_kW"] > 0)].copy()
        if len(daytime) < min_points:
            continue
            
        v = daytime["DC_Voltage_V"].dropna()
        if len(v) < min_points:
            continue
            
        mean_v = v.mean()
        std_v = v.std()
        cv = std_v / mean_v if mean_v > 0 else 0
        
        if cv > VOLTAGE_INSTABILITY_CV:
            # Report at the peak variance timestamp or first timestamp
            ts = daytime["Timestamp"].iloc[0] 
            detail = f"Voltage instability detected (CV={cv*100:.1f}%, mean={mean_v:.1f}V, std={std_v:.1f}V)"
            rows.append(_make_row(
                ts, inv_id, mppt_id, "Voltage Instability",
                "LOW", "MPPT", detail
            ))
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# Anomaly 10: Major MPPT Underperformance / Outage                   [HIGH]
# ─────────────────────────────────────────────────────────────────────────────
def detect_mppt_outage(df: pd.DataFrame, dt_h: float) -> List[dict]:
    """Flag MPPTs performing significantly below inverter peer performance."""
    rows = []
    
    for inv_id, inv_grp in df.groupby("Inverter_ID"):
        # We look at the average performance over the entire uploaded period
        mppt_stats = []
        for mppt_id, mppt_grp in inv_grp.groupby("MPPT_ID"):
            mppt_stats.append({
                "MPPT_ID": mppt_id,
                "Energy": (mppt_grp["DC_Power_kW"].fillna(0) * dt_h).sum(),
                "Mean_Current": mppt_grp["DC_Current_A"].mean(),
                "Mean_Voltage": mppt_grp["DC_Voltage_V"].mean(),
                "First_TS": mppt_grp["Timestamp"].iloc[0] if not mppt_grp.empty else None
            })
            
        if not mppt_stats:
            continue
            
        # Determine whether to use Energy or Current for comparison
        energies = [s["Energy"] for s in mppt_stats if pd.notna(s["Energy"])]
        currents = [s["Mean_Current"] for s in mppt_stats if pd.notna(s["Mean_Current"])]
        voltages = [s["Mean_Voltage"] for s in mppt_stats if pd.notna(s["Mean_Voltage"])]
        
        median_e = np.median(energies) if energies else 0
        median_i = np.median(currents) if currents else 0
        median_v = np.median(voltages) if voltages else 0
        
        # Use Current if it's more 'active' than Energy
        use_current = (median_i > 0.01)
        
        check_val = median_i if use_current else median_e
        metric_name = "current" if use_current else "energy"
        
        # Threshold for flagging
        if check_val < (0.01 if use_current else 0.001):
            # Fallback: check for massive voltage deviation even if current is zero
            if median_v > 100:
                for s in mppt_stats:
                    if pd.notna(s["Mean_Voltage"]) and s["Mean_Voltage"] < (median_v * 0.50):
                        detail = f"MPPT {s['MPPT_ID']} voltage ({s['Mean_Voltage']:.1f}V) is < 50% of inverter median ({median_v:.1f}V)"
                        rows.append(_make_row(
                            s["First_TS"], inv_id, s["MPPT_ID"], "Major MPPT Underperformance",
                            "HIGH", "MPPT", detail
                        ))
            continue
            
        for s in mppt_stats:
            val = s["Mean_Current"] if use_current else s["Energy"]
            if pd.isna(val): continue
            
            # 1. Check Primary Metric (Current/Energy)
            is_underperf = val < (check_val * 0.50)
            
            # 2. Check Voltage as a secondary confirmation
            is_v_low = pd.notna(s["Mean_Voltage"]) and median_v > 100 and s["Mean_Voltage"] < (median_v * 0.50)
            
            if is_underperf or is_v_low:
                v_detail = f" (Voltage: {s['Mean_Voltage']:.1f}V vs median {median_v:.1f}V)" if is_v_low else ""
                detail = f"MPPT {s['MPPT_ID']} {metric_name} ({val:.2f}) is < 50% of median{v_detail}"
                rows.append(_make_row(
                    s["First_TS"], inv_id, s["MPPT_ID"], "Major MPPT Underperformance",
                    "HIGH", "MPPT", detail,
                    kwh_loss=(median_e - s["Energy"]) if not use_current and median_e > 0 else 0
                ))
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# Master runner
# ─────────────────────────────────────────────────────────────────────────────
DETECTORS = [
    detect_zero_generation,
    detect_sudden_power_drop,
    detect_mppt_current_mismatch,
    detect_flatline_current,
    detect_vi_mismatch,
    detect_voltage_imbalance,
    detect_clipping,
    detect_nighttime_generation,
    detect_voltage_instability,
    detect_mppt_outage,
]

SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def run_all_detectors(df: pd.DataFrame) -> pd.DataFrame:
    """Run all detectors and return a unified log."""
    dt_h = _dt_hours(df)
    all_rows = []
    ts_min = df["Timestamp"].min() if not df.empty else pd.Timestamp.now()

    for detector in DETECTORS:
        try:
            results = detector(df, dt_h)
            if results:
                all_rows.extend(results)
        except Exception as e:
            # Log the error but use a real timestamp, not SYSTEM placeholders
            all_rows.append(_make_row(
                ts_min, "SYSTEM", "ALL", "Detector Error",
                "HIGH", "System", f"Detector {detector.__name__} failed: {str(e)}"
            ))

    anomaly_df = pd.DataFrame(all_rows)
    if "Severity" in anomaly_df.columns:
        anomaly_df["Severity_Order"] = anomaly_df["Severity"].map(SEVERITY_ORDER).fillna(9)
        anomaly_df = anomaly_df.sort_values(["Severity_Order", "Timestamp"]).drop(columns="Severity_Order")
    
    return anomaly_df.reset_index(drop=True)


def get_anomaly_summary(anomaly_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate anomaly counts."""
    if anomaly_df.empty: return pd.DataFrame()
    return (
        anomaly_df.groupby(["Anomaly_Type", "Severity", "Layer"])
        .size().reset_index(name="Count")
        .sort_values("Count", ascending=False)
    )
