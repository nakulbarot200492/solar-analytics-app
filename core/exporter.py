"""
core/exporter.py
----------------
Export analytics results to Excel (.xlsx) and CSV formats.
"""

import io
import pandas as pd


def to_excel_bytes(dataframes: dict) -> bytes:
    """
    Write multiple DataFrames to a single Excel workbook (one sheet each).
    Returns bytes suitable for st.download_button.

    Parameters
    ----------
    dataframes : dict of {sheet_name: DataFrame}
    """
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for sheet_name, df in dataframes.items():
            if df is not None and not df.empty:
                safe_name = sheet_name[:31]  # Excel sheet name limit
                df.to_excel(writer, sheet_name=safe_name, index=False)
    return buffer.getvalue()


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Return CSV bytes for a single DataFrame."""
    return df.to_csv(index=False).encode("utf-8")


def build_export_package(
    ranking_df: pd.DataFrame,
    anomaly_df: pd.DataFrame,
    rca_df: pd.DataFrame,
    mppt_summary_df: pd.DataFrame,
) -> bytes:
    """
    Build a single Excel file with 4 sheets matching the 4 PRD deliverables.
    """
    return to_excel_bytes({
        "Inverter_Ranking": ranking_df,
        "Anomaly_Log": anomaly_df,
        "RCA_Report": rca_df,
        "MPPT_Analysis": mppt_summary_df,
    })
