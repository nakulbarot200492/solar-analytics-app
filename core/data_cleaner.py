"""
core/data_cleaner.py
--------------------
Data cleaning pipeline:
  - Missing value handling
  - Duplicate timestamp+inverter+MPPT removal
  - Timestamp sorting
  - Physical bounds enforcement
  - V×I vs DC_Power_kW consistency check
"""

import pandas as pd
import numpy as np
from typing import Tuple, List, Dict


def clean(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
    """
    Run the full cleaning pipeline.
    Returns (cleaned_df, audit_log_dict).
    """
    audit: Dict = {}
    df = df.copy()

    # ── 1. Sort by Timestamp ────────────────────────────────────────────────
    df = df.sort_values(["Inverter_ID", "MPPT_ID", "Timestamp"]).reset_index(drop=True)

    # ── 2. Remove duplicates ────────────────────────────────────────────────
    dup_mask = df.duplicated(subset=["Timestamp", "Inverter_ID", "MPPT_ID"], keep="first")
    n_dups = dup_mask.sum()
    audit["duplicates_removed"] = int(n_dups)
    if n_dups:
        df = df[~dup_mask].reset_index(drop=True)

    # ── 3. Missing value report ─────────────────────────────────────────────
    required_cols = ["Timestamp", "Site_ID", "Inverter_ID", "MPPT_ID"]
    # Drop rows missing any required column
    before = len(df)
    missing_counts = {}
    for col in required_cols:
        n_missing = df[col].isna().sum()
        if n_missing:
            missing_counts[col] = int(n_missing)
    audit["missing_per_col"] = missing_counts
    
    df = df.dropna(subset=required_cols).reset_index(drop=True)
    audit["rows_dropped_missing"] = int(before - len(df))

    # ── 4. Bounds enforcement ────────────────────────────────────────────────
    bounds_violations: Dict[str, int] = {}
    bounds = {
        "DC_Voltage_V":  (0, 1500),
        "DC_Current_A":  (0, None),
        "DC_Power_kW":   (0, None),
        "AC_Power_kW":   (0, None),
        "Irradiance_Wm2":(0, 1500),
    }
    for col, (lo, hi) in bounds.items():
        if col not in df.columns:
            continue
        mask = pd.Series(False, index=df.index)
        if lo is not None:
            mask |= df[col] < lo
        if hi is not None:
            mask |= df[col] > hi
        n_bad = mask.sum()
        if n_bad:
            bounds_violations[col] = int(n_bad)
            df.loc[mask, col] = np.nan  # nullify out-of-bounds values
    audit["bounds_violations_nullified"] = bounds_violations

    # ── 5. V×I vs DC_Power_kW consistency ──────────────────────────────────
    if {"DC_Voltage_V", "DC_Current_A", "DC_Power_kW"}.issubset(df.columns):
        vi_product = (df["DC_Voltage_V"] * df["DC_Current_A"]) / 1000  # → kW
        valid_mask = df["DC_Power_kW"].notna() & (df["DC_Power_kW"] > 0)
        pct_diff = ((vi_product - df["DC_Power_kW"]).abs() / df["DC_Power_kW"].where(valid_mask)).fillna(0)
        mismatch_mask = (pct_diff > 0.15) & valid_mask
        audit["vi_power_mismatches"] = int(mismatch_mask.sum())
        df["VI_Power_Mismatch"] = mismatch_mask  # flag column for downstream use

    # ── 6. Add time features ────────────────────────────────────────────────
    df["Hour"] = df["Timestamp"].dt.hour
    df["Date"] = df["Timestamp"].dt.date
    # Daytime window for analysis (e.g., MPPT deviation)
    # Widened to 6 AM - 8 PM to capture early/late generation
    df["Is_Daytime"] = df["Hour"].between(6, 20) 
    
    # ── 7. NaN Report (Critical Metrics) ────────────────────────────────────
    nan_report = {}
    for col in ["DC_Voltage_V", "DC_Current_A", "DC_Power_kW"]:
        if col in df.columns:
            n_nan = df[col].isna().sum()
            if n_nan:
                nan_report[col] = int(n_nan)
    audit["nan_metrics"] = nan_report
    audit["rows_dropped_night"] = 0  # Disabled filtering to prevent empty tables

    audit["final_row_count"] = len(df)
    return df, audit


def get_audit_summary(audit: Dict) -> str:
    """Return a human-readable audit summary string."""
    lines = [
        f"✅ **Rows after cleaning:** {audit.get('final_row_count', '—')}",
        f"🗑️ **Duplicates removed:** {audit.get('duplicates_removed', 0)}",
        f"🗑️ **Rows dropped (missing required):** {audit.get('rows_dropped_missing', 0)}",
        f"🌙 **Night-time rows removed (before 6AM / after 8PM):** {audit.get('rows_dropped_night', 0)}",
    ]
    mv = audit.get("missing_values", {})
    if mv:
        lines.append("⚠️ **Missing identifiers (Dropped):**")
        for col, n in mv.items():
            lines.append(f"  - `{col}`: {n} rows")
    
    nm = audit.get("nan_metrics", {})
    if nm:
        lines.append("⚠️ **Missing metrics (NaNs kept, but skipped in averages):**")
        for col, n in nm.items():
            lines.append(f"  - `{col}`: {n} values")
    bv = audit.get("bounds_violations_nullified", {})
    if bv:
        lines.append("⚠️ **Out-of-bounds values nullified:**")
        for col, n in bv.items():
            lines.append(f"  - `{col}`: {n} values")
    vi = audit.get("vi_power_mismatches", 0)
    if vi:
        lines.append(f"⚠️ **V×I / DC_Power mismatches (>15%):** {vi} rows")
    return "\n".join(lines)
