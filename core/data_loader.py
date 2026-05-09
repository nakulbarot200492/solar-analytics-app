"""
core/data_loader.py
-------------------
Handles raw data ingestion from SMA Excel/CSV files.
Supports wide-format (multi-column) and long-format data.
"""

import pandas as pd
import numpy as np
import io
import re
from typing import Tuple, List, Optional

# ── PRD Column Mapping ───────────────────────────────────────────────────────
COLUMN_MAP = {
    "Timestamp": ["Timestamp", "Time", "Date", "DateTime", "Zeit"],
    "DC_Voltage_V": ["Voltage", "V_PV", "U_PV", "DC Voltage", "V_DC", "Mean_Voltage_V", "Voltage_V", "Voltage [V]", "Mean_Voltage"],
    "DC_Current_A": ["Current", "I_PV", "A_PV", "DC Current", "A_DC", "Mean_Current_A", "Current_A", "Current [A]", "Mean_Current"],
    "DC_Power_kW": ["DC Power", "P_DC", "Power_DC", "Power [kW]", "DC_Power"],
    "AC_Power_kW": ["AC Power", "P_AC", "Power_AC", "Active Power", "AC_Power"],
    "Irradiance_Wm2": ["Irradiance", "G_Hor", "Solar Radiation", "W/m2", "G_Global", "POA"],
    "Temperature_C": ["Temperature", "T_Amb", "Module Temp", "Temp", "Ambient Temperature"],
    "Inverter_ID": ["Serial Number", "S/N", "Device", "Inverter", "Inv. ID", "Inverter-ID", "Inverter ID", "Gerät"],
    "MPPT_ID": ["MPPT", "Channel", "Input", "String", "MPPT ID", "Kanal"],
}

OPTIONAL_COLUMNS = [
    "DC_Voltage_V", "DC_Current_A", "DC_Power_kW", "AC_Power_kW", 
    "Irradiance_Wm2", "Temperature_C"
]

def load_excel(file_obj) -> Tuple[pd.DataFrame, List[str]]:
    """Generic loader for Excel or CSV with auto-header detection."""
    warnings = []
    try:
        # Read a small chunk to find the header row
        header_row = 0
        if file_obj.name.endswith(".csv"):
            sample = pd.read_csv(file_obj, nrows=50, header=None)
            for i, row in sample.iterrows():
                row_str = " ".join([str(x) for x in row.values]).lower()
                # SMA files usually have Time/Timestamp and Voltage/Current nearby
                if any(t in row_str for t in ["time", "timestamp", "date"]) and \
                   any(m in row_str for m in ["voltage", "current", "power", "v", "i", "p"]):
                    header_row = i
                    break
            file_obj.seek(0)
            df = pd.read_csv(file_obj, skiprows=header_row)
        else:
            xl = pd.ExcelFile(file_obj)
            # Read first 50 rows of first sheet to find header
            sample = xl.parse(xl.sheet_names[0], nrows=50, header=None)
            for i, row in sample.iterrows():
                row_str = " ".join([str(x) for x in row.values]).lower()
                if any(t in row_str for t in ["time", "timestamp", "date"]) and \
                   any(m in row_str for m in ["voltage", "current", "power", "v", "i", "p"]):
                    header_row = i
                    break
            file_obj.seek(0)
            df = pd.read_excel(file_obj, skiprows=header_row)
            
        if header_row > 0:
            warnings.append(f"💡 Skipped {header_row} metadata rows to find the data header.")
            
    except Exception as e:
        return pd.DataFrame(), [f"Failed to read file: {e}"]

    df, map_warnings = normalize_schema(df)
    warnings.extend(map_warnings)
    
    return df, warnings

def load_file(file_obj):
    """Old alias for load_excel."""
    return load_excel(file_obj)

def normalize_schema(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """Map raw columns to internal canonical names."""
    warnings = []
    
    # 1. Strip whitespace from headers
    df.columns = [str(c).strip() for c in df.columns]
    
    # ─── 2. Handle SMA Sunny Portal Wide Format ─────────────────────────────
    # Column names like:
    #   "Inv A2 (62.5 kW) SMA STP Core-1 62US: DC Current Input 1 (Idc1) Amps"
    #   "Inv A25 (62.5 kW) SMA STP Core-1 62US: DC Voltage Input 6 (Udc6) Volts"
    # We extract: Inverter_ID=A2, metric=DC_Current_A, MPPT_ID=1
    
    sma_detail_pattern = re.compile(
        r'Inv\s+(\w+)\b'         # Inverter ID (e.g. A2, A25)
        r'.*?:\s*'               # Skip model info, match colon
        r'(DC\s+Current|DC\s+Voltage|DC\s+Power|AC\s+Power|AC\s+Current)'  # Metric
        r'(?:.*?Input\s+(\d+))?', # Optional MPPT input number
        re.I
    )
    
    # Map SMA metric keywords to our canonical column names
    SMA_METRIC_MAP = {
        'dc current':  'DC_Current_A',
        'dc voltage':  'DC_Voltage_V',
        'dc power':    'DC_Power_kW',
        'ac power':    'AC_Power_kW',
        'ac current':  'AC_Current_A',
    }
    
    sma_parsed = []
    for col in df.columns:
        m = sma_detail_pattern.match(col)
        if m:
            inv_id = m.group(1)                     # e.g. "A2", "A25"
            metric_key = m.group(2).lower().strip()  # e.g. "dc current"
            mppt_id = m.group(3) or "1"              # e.g. "1", "6"
            
            canonical = SMA_METRIC_MAP.get(metric_key)
            if canonical:
                sma_parsed.append({
                    'orig_col': col,
                    'Inverter_ID': inv_id,
                    'MPPT_ID': mppt_id,
                    'metric': canonical,
                })
    
    if sma_parsed:
        # This is an SMA Sunny Portal file — melt it properly
        sma_cols_set = {p['orig_col'] for p in sma_parsed}
        id_cols = [c for c in df.columns if c not in sma_cols_set]
        
        # Group by (Inverter_ID, MPPT_ID) → {canonical_metric: original_col_name}
        from collections import defaultdict
        groups = defaultdict(dict)
        for p in sma_parsed:
            key = (p['Inverter_ID'], p['MPPT_ID'])
            groups[key][p['metric']] = p['orig_col']
        
        melted_dfs = []
        for (inv_id, mppt_id), metric_cols in groups.items():
            cols_to_use = id_cols + list(metric_cols.values())
            m_df = df[cols_to_use].copy()
            # Rename SMA column names → canonical names (e.g. DC_Current_A)
            m_df = m_df.rename(columns={v: k for k, v in metric_cols.items()})
            m_df['Inverter_ID'] = inv_id
            m_df['MPPT_ID'] = str(mppt_id)
            melted_dfs.append(m_df)
        
        if melted_dfs:
            df = pd.concat(melted_dfs, ignore_index=True)
            inv_count = len(set(p['Inverter_ID'] for p in sma_parsed))
            channel_count = len(groups)
            warnings.append(
                f"✅ SMA format detected: {inv_count} inverters, "
                f"{channel_count} channels melted into long format."
            )
    else:
        # ─── 2b. Fallback: Simple Wide Format (e.g. "Voltage_A", "Voltage_B") ──
        mppt_suffix_pattern = re.compile(
            r"^(.*?)(?:[_ \-\.\[]?)(?:MPPT)?([A-I1-9])(?:\]?)$", re.I
        )
        
        wide_map = {}
        for col in df.columns:
            match = mppt_suffix_pattern.match(col)
            if match:
                base, mppt = match.groups()
                mppt = mppt.upper()
                found_metric = False
                for internal, aliases in COLUMN_MAP.items():
                    if any(alias.lower() in base.lower() for alias in aliases):
                        if mppt not in wide_map: wide_map[mppt] = {}
                        wide_map[mppt][col] = internal
                        found_metric = True
                        break
        
        if wide_map and len(wide_map) > 1:
            id_vars = [c for c in df.columns if c not in [c for m in wide_map.values() for c in m.keys()]]
            melted_dfs = []
            for mppt, col_rename in wide_map.items():
                m_df = df[id_vars + list(col_rename.keys())].copy()
                m_df = m_df.rename(columns=col_rename)
                m_df["MPPT_ID"] = mppt
                melted_dfs.append(m_df)
            
            if melted_dfs:
                df = pd.concat(melted_dfs, ignore_index=True)
                warnings.append(f"✅ Auto-detected wide format with {len(wide_map)} MPPTs ({', '.join(wide_map.keys())}).")

    # 3. Canonical Mapping (for single-column metrics or after melting)
    new_cols = {}
    for internal, aliases in COLUMN_MAP.items():
        if internal in df.columns:
            continue
        for alias in aliases:
            # Try exact match first
            matches = [c for c in df.columns if c.lower() == alias.lower()]
            if not matches:
                # Try fuzzy match (alias is part of the column name)
                matches = [c for c in df.columns if alias.lower() in c.lower()]
            
            if matches:
                new_cols[matches[0]] = internal
                break
    
    df = df.rename(columns=new_cols)

    df = df.copy() # De-fragment to avoid PerformanceWarning

    # 4. Defaults for required columns
    if "Timestamp" not in df.columns:
        # Fallback: assume first column is time
        df = df.rename(columns={df.columns[0]: "Timestamp"})
    
    defaults = {}
    if "Inverter_ID" not in df.columns: defaults["Inverter_ID"] = "Unknown"
    if "MPPT_ID" not in df.columns: defaults["MPPT_ID"] = "1"
    if "Site_ID" not in df.columns: defaults["Site_ID"] = "Site_1"
    
    if defaults:
        df = df.assign(**defaults)

    # 5. Cleanup types
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce").dt.round("1min")
    
    for col in ["Inverter_ID", "MPPT_ID", "Site_ID"]:
        df[col] = df[col].astype(str).str.strip().replace("nan", "Unknown")

    numeric_cols = [c for c in OPTIONAL_COLUMNS if c in df.columns]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 6. Auto-calculate DC Power if missing
    if "DC_Power_kW" not in df.columns and "DC_Voltage_V" in df.columns and "DC_Current_A" in df.columns:
        df["DC_Power_kW"] = (df["DC_Voltage_V"] * df["DC_Current_A"]) / 1000.0
    
    # 7. Final Sanity: Ensure all canonical columns exist (even if NaN) to prevent crashes
    new_cols_to_add = {col: np.nan for col in COLUMN_MAP.keys() if col not in df.columns}
    if new_cols_to_add:
        df = df.assign(**new_cols_to_add)
    
    if "Is_Daytime" not in df.columns:
        df["Hour"] = df["Timestamp"].dt.hour
        df["Is_Daytime"] = df["Hour"].between(8, 18)

    return df, warnings

def get_site_info(df: pd.DataFrame) -> dict:
    """Extract metadata for summary display."""
    if df.empty: return {}
    
    hi = df.get("Hour")
    return {
        "Site Name": df["Site_ID"].iloc[0] if "Site_ID" in df.columns else "Unknown",
        "Inverters": df["Inverter_ID"].nunique(),
        "MPPTs": df["MPPT_ID"].nunique(),
        "Rows": len(df),
        "Has Irradiance": df["Irradiance_Wm2"].notna().any() if "Irradiance_Wm2" in df.columns else False,
        "Time Range": f"{df['Timestamp'].min()} to {df['Timestamp'].max()}",
    }

def get_column_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Provides a health summary of the uploaded columns."""
    if df.empty: return pd.DataFrame()
    
    stats = []
    cols_to_check = list(COLUMN_MAP.keys()) + ["Site_ID"]
    for col in cols_to_check:
        if col in df.columns:
            stats.append({
                "Column": col,
                "Valid Rows": df[col].notna().sum(),
                "Min": df[col].min() if pd.api.types.is_numeric_dtype(df[col]) else np.nan,
                "Max": df[col].max() if pd.api.types.is_numeric_dtype(df[col]) else np.nan,
                "Status": "✅ Found"
            })
        else:
            is_optional = col in OPTIONAL_COLUMNS or col == "Site_ID"
            stats.append({
                "Column": col,
                "Valid Rows": 0,
                "Min": np.nan,
                "Max": np.nan,
                "Status": "❌ Missing" if not is_optional else "⚠️ Optional"
            })
    return pd.DataFrame(stats)

def validate_bounds(df: pd.DataFrame) -> List[str]:
    """Basic physical bound checks for solar data."""
    warnings = []
    if df.empty: return warnings
    
    if "DC_Voltage_V" in df.columns:
        if (df["DC_Voltage_V"] > 1500).any():
            warnings.append("⚠️ High voltage detected (>1500V). Check if units are in mV.")
        if (df["DC_Voltage_V"] < 0).any():
            warnings.append("⚠️ Negative voltage detected.")
            
    if "DC_Power_kW" in df.columns:
        if (df["DC_Power_kW"] > 5000).any():
             warnings.append("⚠️ Extremely high DC power detected (>5MW). Check units.")
             
    if "Irradiance_Wm2" in df.columns:
        if (df["Irradiance_Wm2"] > 1600).any():
            warnings.append("⚠️ Irradiance exceeds 1600 W/m². Check sensor calibration.")
            
    return warnings
