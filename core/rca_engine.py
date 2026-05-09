"""
core/rca_engine.py
------------------
Rule-based Root Cause Analysis (RCA) engine.
Maps detected anomaly types to probable root causes and recommended actions.
"""

import pandas as pd

# ── RCA lookup table (from PRD) ───────────────────────────────────────────────
RCA_MAP = [
    {
        "Anomaly_Type": "Zero Generation (Daytime)",
        "Symptom": "Zero AC output, DC present",
        "Root_Cause": "Inverter fault / protection triggered",
        "Recommended_Action": "Check inverter error log; restart or escalate to OEM",
        "Priority": "Immediate",
    },
    {
        "Anomaly_Type": "Zero Generation (Daytime)",
        "Symptom": "Zero output (DC + AC)",
        "Root_Cause": "Grid outage or breaker trip",
        "Recommended_Action": "Verify grid voltage; check AC breakers & protection relays",
        "Priority": "Immediate",
    },
    {
        "Anomaly_Type": "Sudden Power Drop",
        "Symptom": "Sudden power drop, irradiance stable",
        "Root_Cause": "Inverter internal fault",
        "Recommended_Action": "Check temperature sensors; verify cooling system",
        "Priority": "High",
    },
    {
        "Anomaly_Type": "MPPT Current Mismatch",
        "Symptom": "MPPT current mismatch (1 MPPT)",
        "Root_Cause": "Partial string failure or bypass diode failure",
        "Recommended_Action": "IV curve trace on affected string; replace module if needed",
        "Priority": "High",
    },
    {
        "Anomaly_Type": "MPPT Current Mismatch",
        "Symptom": "Low DC current on specific MPPT(s)",
        "Root_Cause": "Soiling / shading on connected strings",
        "Recommended_Action": "Schedule panel cleaning; inspect for obstructions",
        "Priority": "Medium",
    },
    {
        "Anomaly_Type": "Flatline Current",
        "Symptom": "Flatline current on MPPT",
        "Root_Cause": "String open-circuit / disconnection",
        "Recommended_Action": "Inspect string fuses & connectors; check MC4 joints",
        "Priority": "High",
    },
    {
        "Anomaly_Type": "Voltage-Current Mismatch",
        "Symptom": "V×I deviates from reported DC_Power_kW",
        "Root_Cause": "Sensor calibration drift or wiring fault",
        "Recommended_Action": "Recalibrate sensors; verify wiring integrity",
        "Priority": "Medium",
    },
    {
        "Anomaly_Type": "Voltage Imbalance",
        "Symptom": "Voltage imbalance across MPPTs",
        "Root_Cause": "Module degradation / mismatch",
        "Recommended_Action": "Thermal imaging scan; check module Voc values",
        "Priority": "Low",
    },
    {
        "Anomaly_Type": "Clipping Event",
        "Symptom": "Clipping at high irradiance",
        "Root_Cause": "Oversized DC array / inverter undersized",
        "Recommended_Action": "Review DC:AC ratio; consider inverter upgrade",
        "Priority": "Low",
    },
    {
        "Anomaly_Type": "Night-time Generation",
        "Symptom": "Non-zero power between 20:00–06:00",
        "Root_Cause": "Sensor ghost signal or meter error",
        "Recommended_Action": "Inspect monitoring system; verify CT/PT calibration",
        "Priority": "Low",
    },
    {
        "Anomaly_Type": "Major MPPT Underperformance",
        "Symptom": "One MPPT significantly lower current/power than others",
        "Root_Cause": "MPPT board failure, string fuse blown, or massive shading",
        "Recommended_Action": "Verify string voltages at inverter DC inputs; check internal fuses",
        "Priority": "High",
    },
]

RCA_DF = pd.DataFrame(RCA_MAP)


def apply_rca(anomaly_df: pd.DataFrame) -> pd.DataFrame:
    if anomaly_df.empty:
        return anomaly_df

    # Deduplicate RCA map
    rca_dedup = RCA_DF.drop_duplicates(subset="Anomaly_Type", keep="first")[
        ["Anomaly_Type", "Root_Cause", "Recommended_Action", "Priority"]
    ]

    # Ensure we don't lose rows: use left merge
    enriched = anomaly_df.merge(rca_dedup, on="Anomaly_Type", how="left")
    
    # Fill defaults for rows without an RCA match
    enriched["Root_Cause"] = enriched["Root_Cause"].fillna("Unknown / Multi-factor")
    enriched["Recommended_Action"] = enriched["Recommended_Action"].fillna("Review raw DC electrical data; verify string continuity.")
    enriched["Priority"] = enriched["Priority"].fillna("Low")
    
    return enriched


def get_rca_summary(rca_df: pd.DataFrame) -> pd.DataFrame:
    """Group RCA results by root cause category with event count and total kWh loss."""
    if rca_df.empty:
        return pd.DataFrame(columns=["Root_Cause", "Priority", "Recommended_Action", "Event_Count", "Inverters_Affected", "Total_kWh_Loss"])
    return (
        rca_df.groupby(["Root_Cause", "Priority", "Recommended_Action"])
        .agg(
            Event_Count=("Anomaly_Type", "count"),
            Inverters_Affected=("Inverter_ID", "nunique"),
            Total_kWh_Loss=("kWh_Loss_Est", "sum"),
        )
        .reset_index()
        .sort_values(["Priority", "Event_Count"], ascending=[True, False])
    )


def get_full_rca_reference() -> pd.DataFrame:
    """Return the complete RCA reference table."""
    return RCA_DF.copy()
