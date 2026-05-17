"""
core/pdf_exporter.py
--------------------
Generates a professional Solar SPV Analytics PDF report using ReportLab.
Pure Python — no system dependencies, works on Streamlit Cloud.
"""

import io
from datetime import datetime
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)

# ── Brand Colors ─────────────────────────────────────────────────────────────
GOLD       = colors.HexColor("#FFD700")
DARK_BG    = colors.HexColor("#131313")
SURFACE    = colors.HexColor("#201f1f")
TEXT_LIGHT = colors.HexColor("#E5E2E1")
TEXT_MUTED = colors.HexColor("#94A3B8")
GREEN      = colors.HexColor("#7BF29D")
RED        = colors.HexColor("#FFB4AB")
BLUE       = colors.HexColor("#4A8EFF")
HEADER_BG  = colors.HexColor("#1A1A1A")
ROW_ALT    = colors.HexColor("#1C1C1C")


def _styles():
    """Build custom paragraph styles."""
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "Title", parent=base["Title"],
            fontSize=22, textColor=GOLD, alignment=TA_LEFT,
            spaceAfter=4, fontName="Helvetica-Bold"
        ),
        "subtitle": ParagraphStyle(
            "Subtitle", parent=base["Normal"],
            fontSize=10, textColor=TEXT_MUTED, alignment=TA_LEFT,
            spaceAfter=12, fontName="Helvetica"
        ),
        "section": ParagraphStyle(
            "Section", parent=base["Heading2"],
            fontSize=13, textColor=GOLD, alignment=TA_LEFT,
            spaceBefore=16, spaceAfter=6, fontName="Helvetica-Bold"
        ),
        "body": ParagraphStyle(
            "Body", parent=base["Normal"],
            fontSize=9, textColor=TEXT_LIGHT, alignment=TA_LEFT,
            spaceAfter=4, fontName="Helvetica"
        ),
        "small": ParagraphStyle(
            "Small", parent=base["Normal"],
            fontSize=7.5, textColor=TEXT_MUTED, alignment=TA_CENTER,
            fontName="Helvetica"
        ),
    }


def _make_table(df: pd.DataFrame, max_rows: int = 50) -> Table:
    """Convert a DataFrame to a styled ReportLab table."""
    if df.empty:
        return Paragraph("No data available.", _styles()["body"])

    df_display = df.head(max_rows).copy()
    # Truncate long strings
    for col in df_display.select_dtypes(include="object").columns:
        df_display[col] = df_display[col].astype(str).str[:35]

    # Round floats
    for col in df_display.select_dtypes(include="float").columns:
        df_display[col] = df_display[col].round(2)

    headers = list(df_display.columns)
    data = [headers] + df_display.values.tolist()

    col_width = (A4[0] - 40*mm) / max(len(headers), 1)
    col_widths = [col_width] * len(headers)

    table = Table(data, colWidths=col_widths, repeatRows=1)

    style = TableStyle([
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), DARK_BG),
        ("TEXTCOLOR",  (0, 0), (-1, 0), GOLD),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, 0), 8),
        ("ALIGN",      (0, 0), (-1, 0), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING",    (0, 0), (-1, 0), 6),
        # Data rows
        ("FONTNAME",   (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",   (0, 1), (-1, -1), 7.5),
        ("TEXTCOLOR",  (0, 1), (-1, -1), TEXT_LIGHT),
        ("ALIGN",      (0, 1), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [SURFACE, ROW_ALT]),
        ("GRID",       (0, 0), (-1, -1), 0.3, colors.HexColor("#2A2A2A")),
        ("TOPPADDING",    (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
    ])

    # Color performance tiers if present
    if "Performance_Tier" in headers:
        tier_col = headers.index("Performance_Tier")
        for i, row in enumerate(df_display.itertuples(), start=1):
            tier = getattr(row, "Performance_Tier", "")
            if tier == "Top 10%":
                style.add("BACKGROUND", (tier_col, i), (tier_col, i), colors.HexColor("#064e3b"))
                style.add("TEXTCOLOR",  (tier_col, i), (tier_col, i), GREEN)
            elif tier == "Bottom 10%":
                style.add("BACKGROUND", (tier_col, i), (tier_col, i), colors.HexColor("#7f1d1d"))
                style.add("TEXTCOLOR",  (tier_col, i), (tier_col, i), RED)

    # Color severity if present
    if "Severity" in headers:
        sev_col = headers.index("Severity")
        for i, row in enumerate(df_display.itertuples(), start=1):
            sev = getattr(row, "Severity", "")
            if sev == "HIGH":
                style.add("TEXTCOLOR", (sev_col, i), (sev_col, i), RED)
                style.add("FONTNAME",  (sev_col, i), (sev_col, i), "Helvetica-Bold")
            elif sev == "MEDIUM":
                style.add("TEXTCOLOR", (sev_col, i), (sev_col, i), GOLD)
            elif sev == "LOW":
                style.add("TEXTCOLOR", (sev_col, i), (sev_col, i), GREEN)

    table.setStyle(style)
    return table


def _header_footer(canvas, doc):
    """Draw branded header and footer on every page."""
    canvas.saveState()
    w, h = A4

    # Top bar
    canvas.setFillColor(DARK_BG)
    canvas.rect(0, h - 18*mm, w, 18*mm, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(20*mm, h - 11*mm, "☀ Solar SPV Analytics Platform")
    canvas.setFillColor(TEXT_MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(w - 20*mm, h - 11*mm, f"Generated: {datetime.now().strftime('%d %b %Y, %H:%M')}")

    # Gold accent line
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(1.2)
    canvas.line(0, h - 18*mm, w, h - 18*mm)

    # Bottom footer
    canvas.setFillColor(DARK_BG)
    canvas.rect(0, 0, w, 10*mm, fill=1, stroke=0)
    canvas.setFillColor(TEXT_MUTED)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(20*mm, 3.5*mm, "Solar SPV Analytics Platform v3.0  |  Built for O&M Engineers")
    canvas.drawRightString(w - 20*mm, 3.5*mm, f"Page {doc.page}")

    canvas.restoreState()


def build_pdf_report(
    ranking_df: pd.DataFrame,
    anomaly_df: pd.DataFrame,
    rca_df: pd.DataFrame,
    mppt_summary_df: pd.DataFrame,
    site_name: str = "Site_1"
) -> bytes:
    """
    Build a professional PDF report and return it as bytes.
    All DataFrames are optional — missing ones will show a placeholder message.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=22*mm, bottomMargin=14*mm,
        title="Solar SPV Analytics Report",
        author="Solar Analytics Platform v3.0"
    )

    S = _styles()
    story = []

    # ── Cover Block ──────────────────────────────────────────────────────────
    story.append(Spacer(1, 8*mm))
    story.append(Paragraph("Solar SPV Analytics", S["title"]))
    story.append(Paragraph(
        f"Comprehensive O&M Report  ·  Site: {site_name}  ·  {datetime.now().strftime('%d %B %Y')}",
        S["subtitle"]
    ))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GOLD, spaceAfter=12))

    # ── Executive Summary ────────────────────────────────────────────────────
    story.append(Paragraph("Executive Summary", S["section"]))

    n_inverters = ranking_df["Inverter_ID"].nunique() if not ranking_df.empty and "Inverter_ID" in ranking_df.columns else "N/A"
    mean_pr = f"{ranking_df['PR_%'].mean():.1f}%" if not ranking_df.empty and "PR_%" in ranking_df.columns else "N/A"
    n_anomalies = len(anomaly_df) if not anomaly_df.empty else 0
    n_high = len(anomaly_df[anomaly_df["Severity"] == "HIGH"]) if not anomaly_df.empty and "Severity" in anomaly_df.columns else 0
    total_loss = anomaly_df["kWh_Loss_Est"].sum() if not anomaly_df.empty and "kWh_Loss_Est" in anomaly_df.columns else 0

    summary_data = [
        ["Metric", "Value"],
        ["Total Inverters Analyzed", str(n_inverters)],
        ["Fleet Average PR (%)", mean_pr],
        ["Total Anomalies Detected", str(n_anomalies)],
        ["High-Severity Anomalies", str(n_high)],
        ["Estimated Energy Loss (kWh)", f"{total_loss:.2f}"],
        ["Report Date", datetime.now().strftime("%d %b %Y %H:%M")],
    ]

    summary_table = Table(summary_data, colWidths=[90*mm, 80*mm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK_BG),
        ("TEXTCOLOR",  (0, 0), (-1, 0), GOLD),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, 0), 9),
        ("FONTNAME",   (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",   (0, 1), (-1, -1), 9),
        ("TEXTCOLOR",  (0, 1), (0, -1), TEXT_MUTED),
        ("TEXTCOLOR",  (1, 1), (1, -1), TEXT_LIGHT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [SURFACE, ROW_ALT]),
        ("GRID",       (0, 0), (-1, -1), 0.3, colors.HexColor("#2A2A2A")),
        ("ALIGN",      (0, 0), (-1, -1), "LEFT"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
    ]))
    story.append(summary_table)

    # ── Inverter Ranking ─────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("Inverter Performance Ranking", S["section"]))
    story.append(Paragraph(
        "Inverters ranked by composite score: 60% Performance + 40% MPPT Health.",
        S["body"]
    ))
    story.append(Spacer(1, 4))

    if not ranking_df.empty:
        cols = [c for c in ["Rank", "Inverter_ID", "Energy_kWh", "PR_%",
                             "Availability_%", "MPPT_Health", "Performance_Tier",
                             "Composite_Score"] if c in ranking_df.columns]
        story.append(_make_table(ranking_df[cols].sort_values("Rank") if "Rank" in cols else ranking_df[cols]))
    else:
        story.append(Paragraph("No ranking data available.", S["body"]))

    # ── Anomaly Detection ────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("Anomaly Detection Log", S["section"]))
    story.append(Paragraph(
        "Rule-based detection of 8 failure modes. Rows limited to top 50 by severity.",
        S["body"]
    ))
    story.append(Spacer(1, 4))

    if not anomaly_df.empty:
        cols = [c for c in ["Timestamp", "Inverter_ID", "MPPT_ID", "Anomaly_Type",
                             "Severity", "Detail", "kWh_Loss_Est"] if c in anomaly_df.columns]
        sorted_df = anomaly_df.sort_values("Severity", ascending=True) if "Severity" in anomaly_df.columns else anomaly_df
        story.append(_make_table(sorted_df[cols]))
    else:
        story.append(Paragraph("No anomalies detected — system operating normally. ✅", S["body"]))

    # ── RCA Report ───────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("Root Cause Analysis (RCA) Report", S["section"]))
    story.append(Paragraph(
        "Maps detected anomalies to probable root causes with O&M action recommendations.",
        S["body"]
    ))
    story.append(Spacer(1, 4))

    if not rca_df.empty:
        story.append(_make_table(rca_df))
    else:
        story.append(Paragraph("No RCA data available.", S["body"]))

    # ── MPPT Summary ─────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("MPPT Channel Summary", S["section"]))
    story.append(Paragraph(
        "Per-MPPT mean current and voltage statistics for each inverter.",
        S["body"]
    ))
    story.append(Spacer(1, 4))

    if not mppt_summary_df.empty:
        story.append(_make_table(mppt_summary_df))
    else:
        story.append(Paragraph("No MPPT summary data available.", S["body"]))

    # ── Disclaimer ───────────────────────────────────────────────────────────
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=0.4, color=TEXT_MUTED))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "This report was automatically generated by the Solar SPV Analytics Platform v3.0. "
        "All analysis is based on uploaded SMA inverter data. Verify findings with on-site inspection before taking corrective action.",
        S["small"]
    ))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buffer.getvalue()
