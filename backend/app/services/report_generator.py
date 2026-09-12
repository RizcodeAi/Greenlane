"""IMO DCS Annual Compliance Report Generator using ReportLab.

Generates official IMO Data Collection System (DCS) annual compliance reports
as PDF documents for a given organization and reporting year.
"""

import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table,
    TableStyle, KeepTogether, PageBreak,
)

from app.core.database import db

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports_storage")
os.makedirs(REPORTS_DIR, exist_ok=True)

# Brand colours
NAVY = colors.HexColor("#1A3A5C")
NAVY_LIGHT = colors.HexColor("#243b53")
NAVY_DARK = colors.HexColor("#102a43")
GREEN = colors.HexColor("#16A34A")
GREEN_LIGHT = colors.HexColor("#22C55E")
GREEN_DARK = colors.HexColor("#15803d")
GREY = colors.HexColor("#64748b")
GREY_LIGHT = colors.HexColor("#94a3b8")
RED = colors.HexColor("#EF4444")
WHITE = colors.white


def _styles():
    ss = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "Title", parent=ss["Normal"], fontName="Helvetica-Bold",
            fontSize=20, textColor=NAVY, leading=26, alignment=1,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle", parent=ss["Normal"], fontName="Helvetica",
            fontSize=11, textColor=GREY, leading=16, alignment=1,
        ),
        "h1": ParagraphStyle(
            "H1", parent=ss["Normal"], fontName="Helvetica-Bold",
            fontSize=14, textColor=NAVY, leading=18, spaceBefore=12, spaceAfter=6,
        ),
        "h2": ParagraphStyle(
            "H2", parent=ss["Normal"], fontName="Helvetica-Bold",
            fontSize=12, textColor=NAVY_LIGHT, leading=16, spaceBefore=8, spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "Body", parent=ss["Normal"], fontName="Helvetica",
            fontSize=9, textColor=colors.HexColor("#1e293b"), leading=13,
        ),
        "body_bold": ParagraphStyle(
            "BodyBold", parent=ss["Normal"], fontName="Helvetica-Bold",
            fontSize=9, textColor=colors.HexColor("#1e293b"), leading=13,
        ),
        "cell": ParagraphStyle(
            "Cell", parent=ss["Normal"], fontName="Helvetica",
            fontSize=8, textColor=colors.HexColor("#1e293b"), leading=11,
        ),
        "cell_bold": ParagraphStyle(
            "CellBold", parent=ss["Normal"], fontName="Helvetica-Bold",
            fontSize=8, textColor=colors.HexColor("#1e293b"), leading=11,
        ),
        "cell_center": ParagraphStyle(
            "CellCenter", parent=ss["Normal"], fontName="Helvetica",
            fontSize=8, textColor=colors.HexColor("#1e293b"), leading=11, alignment=1,
        ),
        "cell_bold_center": ParagraphStyle(
            "CellBoldCenter", parent=ss["Normal"], fontName="Helvetica-Bold",
            fontSize=8, textColor=colors.HexColor("#1e293b"), leading=11, alignment=1,
        ),
        "declaration": ParagraphStyle(
            "Declaration", parent=ss["Normal"], fontName="Helvetica",
            fontSize=9, textColor=colors.HexColor("#1e293b"), leading=14,
            leftIndent=10, rightIndent=10, spaceAfter=6,
        ),
        "sign_off": ParagraphStyle(
            "SignOff", parent=ss["Normal"], fontName="Helvetica",
            fontSize=9, textColor=NAVY, leading=14, spaceBefore=10,
        ),
    }


def _build_header(canvas, doc, org_name: str, report_id: str, year: int):
    """Draw the page header on every page."""
    canvas.saveState()
    width, height = landscape(A4) if doc.pagesize == landscape(A4) else A4
    # Top navy bar
    canvas.setFillColor(NAVY)
    canvas.rect(0, height - 25, width, 25, fill=1, stroke=0)
    canvas.setFillColor(GREEN)
    canvas.rect(0, height - 28, width, 3, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(30, height - 17, "GREENLANE MARITIME")
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(width - 30, height - 17, f"IMO DCS Annual Compliance Report – {year}")
    # Bottom thin line
    canvas.setStrokeColor(GREY_LIGHT)
    canvas.setLineWidth(0.5)
    canvas.line(30, 25, width - 30, 25)
    canvas.setFillColor(GREY)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(30, 15, f"GreenLane Maritime MVP – Confidential Regulatory Document")
    canvas.drawRightString(width - 30, 15, f"Report ID: {report_id}  |  Page {doc.page}")
    canvas.restoreState()


def _build_landscape_header(canvas, doc, org_name: str, report_id: str, year: int):
    """Landscape page header."""
    canvas.saveState()
    width, height = landscape(A4)
    canvas.setFillColor(NAVY)
    canvas.rect(0, height - 22, width, 22, fill=1, stroke=0)
    canvas.setFillColor(GREEN)
    canvas.rect(0, height - 25, width, 3, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(30, height - 15, "GREENLANE MARITIME")
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(width - 30, height - 15, f"IMO DCS Annual Compliance Report – {year}")
    canvas.setStrokeColor(GREY_LIGHT)
    canvas.setLineWidth(0.5)
    canvas.line(30, 20, width - 30, 20)
    canvas.setFillColor(GREY)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(30, 11, f"GreenLane Maritime MVP – Confidential Regulatory Document")
    canvas.drawRightString(width - 30, 11, f"Report ID: {report_id}  |  Page {doc.page}")
    canvas.restoreState()


class IMDCSReportDoc(BaseDocTemplate):
    """Custom document template with branded header/footer."""

    def __init__(self, filename, org_name, report_id, year, **kw):
        self.org_name = org_name
        self.report_id = report_id
        self.year = year
        # Landscape pages for tables, portrait for summary
        BaseDocTemplate.__init__(self, filename, pagesize=A4, **kw)
        # Portrait frame
        portrait_frame = Frame(
            40, 40, A4[0] - 80, A4[1] - 100,
            leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id="portrait",
        )
        # Landscape frame for wide tables
        landscape_frame = Frame(
            30, 35, landscape(A4)[0] - 60, landscape(A4)[1] - 90,
            leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id="landscape",
        )
        self.addPageTemplates([
            PageTemplate(
                id="portrait", frames=[portrait_frame],
                onPage=lambda c, d: _build_header(c, d, org_name, report_id, year),
            ),
            PageTemplate(
                id="landscape", frames=[landscape_frame],
                onPage=lambda c, d: _build_landscape_header(c, d, org_name, report_id, year),
                pagesize=landscape(A4),
            ),
        ])


def generate_imo_dcs_report(
    org_id: str,
    org_name: str,
    year: int,
    ships: list[dict],
    emissions_records: list[dict],
    voyages: list[dict],
) -> str:
    """Generate a full IMO DCS Annual Compliance Report PDF.

    Args:
        org_id: Organization ID
        org_name: Organization name for branding
        year: Reporting year
        ships: List of ship dicts (with IMO, name, flag, type, GT, DWT, fuel_type)
        emissions_records: List of emissions records for the year
        voyages: List of voyage dicts

    Returns:
        Absolute path to the generated PDF file.
    """
    report_id = f"DCS-{org_id[:8].upper()}-{year}-{uuid.uuid4().hex[:6].upper()}"
    filename = os.path.join(REPORTS_DIR, f"{report_id}.pdf")
    filename = os.path.abspath(filename)

    styles = _styles()

    # Aggregate data
    total_ships = len(ships)
    total_fuel_mt = sum(
        rec.get("fuel_consumed_mt", 0) for rec in emissions_records
    )
    total_co2 = sum(
        rec.get("emissions", {}).get("co2", 0) for rec in emissions_records
    )
    total_transport_work = sum(
        rec.get("fuel_consumed_mt", 0) * 0 for rec in emissions_records
    )
    # Recompute transport work from voyages
    total_transport_work = sum(
        v.get("distance_nm", 0) * v.get("cargo_mt", 0)
        for v in voyages if v.get("cargo_mt") and v.get("distance_nm")
    )

    # Fleet average EEOI
    eeoi_values = []
    for rec in emissions_records:
        voyage = next((v for v in voyages if v["id"] == rec["voyage_id"]), None)
        if voyage and voyage.get("cargo_mt") and voyage.get("distance_nm") and voyage["cargo_mt"] > 0:
            eeoi = (rec["emissions"]["co2"] * 1e6) / (voyage["cargo_mt"] * voyage["distance_nm"])
            eeoi_values.append(eeoi)
    fleet_avg_eefi = round(sum(eeoi_values) / len(eeoi_values), 4) if eeoi_values else None

    # Fuel breakdown
    fuel_breakdown: dict = {}
    for rec in emissions_records:
        ft = rec["fuel_type"]
        if ft not in fuel_breakdown:
            fuel_breakdown[ft] = {"fuel_mt": 0, "co2": 0, "voyage_count": 0}
        fuel_breakdown[ft]["fuel_mt"] += rec["fuel_consumed_mt"]
        fuel_breakdown[ft]["co2"] += rec["emissions"]["co2"]
        fuel_breakdown[ft]["voyage_count"] += 1

    # Group emissions by ship
    emissions_by_ship: dict = {}
    for rec in emissions_records:
        aid = rec["asset_id"]
        if aid not in emissions_by_ship:
            emissions_by_ship[aid] = {"fuel_mt": 0, "co2": 0, "voyages": 0}
        emissions_by_ship[aid]["fuel_mt"] += rec["fuel_consumed_mt"]
        emissions_by_ship[aid]["co2"] += rec["emissions"]["co2"]
        emissions_by_ship[aid]["voyages"] += 1

    # Build the story
    story = []

    # ---- Title Page ----
    story.append(Spacer(1, 2.2 * inch))
    story.append(Paragraph("GREENLANE MARITIME", styles["title"]))
    story.append(Paragraph("IMO Data Collection System (DCS)", ParagraphStyle(
        "sub2", parent=styles["subtitle"], fontSize=14, textColor=GREEN,
    )))
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph("Annual Compliance Report", ParagraphStyle(
        "sub3", parent=styles["subtitle"], fontSize=16, textColor=NAVY,
    )))
    story.append(Spacer(1, 0.4 * inch))

    # Report details table (portrait)
    detail_data = [
        ["Report ID", report_id],
        ["Organization", org_name],
        ["Reporting Year", str(year)],
        ["Generation Date", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")],
        ["Report Type", "IMO DCS Annual Compliance Report"],
        ["Fleet Ships", str(total_ships)],
    ]
    detail_table = Table(detail_data, colWidths=[2.2 * inch, 3.8 * inch])
    detail_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (0, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), NAVY),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (1, 0), (1, -1), 9),
        ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#1e293b")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f4f8")),
        ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#fafbfc")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(detail_table)
    story.append(PageBreak())

    # ---- Page 2: Summary Section (portrait) ----
    story.append(Paragraph(f"Annual Compliance Report – {year}", styles["h1"]))
    story.append(Paragraph(
        f"Organization: <b>{org_name}</b> &nbsp;|&nbsp; "
        f"Report ID: <b>{report_id}</b> &nbsp;|&nbsp; "
        f"Generated: <b>{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</b>",
        ParagraphStyle("meta", parent=styles["body"], fontSize=8, textColor=GREY, leading=11,
    )))
    story.append(Spacer(1, 8))

    # Summary stat cards as a table
    summary_labels = [
        ("Total Fleet Ships", str(total_ships)),
        ("Total Fuel Consumed (MT)", f"{total_fuel_mt:,.2f}"),
        ("Total CO2 Emissions (tonnes)", f"{total_co2:,.2f}"),
        ("Total Transport Work (tonne-miles)", f"{total_transport_work:,.2f}"),
        ("Fleet Average EEOI", f"{fleet_avg_eefi:.4f}" if fleet_avg_eefi else "N/A"),
    ]
    summary_data = [["Metric", "Value"]] + [[a, b] for a, b in summary_labels]
    summary_table = Table(summary_data, colWidths=[3.5 * inch, 2.5 * inch])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (0, -1), 9),
        ("FONTNAME", (1, 1), (1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (1, 1), (1, -1), 9),
        ("TEXTCOLOR", (1, 1), (1, -1), GREEN_DARK),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("ALIGN", (1, 1), (1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 12))

    # Fuel breakdown summary
    story.append(Paragraph("Fuel Breakdown Summary", styles["h2"]))
    if fuel_breakdown:
        fb_data = [["Fuel Type", "Quantity (MT)", "CO2 (tonnes)", "Voyages"]]
        for ft in sorted(fuel_breakdown.keys()):
            fb = fuel_breakdown[ft]
            fb_data.append([ft, f"{fb['fuel_mt']:,.2f}", f"{fb['co2']:,.2f}", str(fb["voyage_count"])])
        fb_data.append(["TOTAL", f"{total_fuel_mt:,.2f}", f"{total_co2:,.2f}", str(len(emissions_records))])
        fb_table = Table(fb_data, colWidths=[1.5 * inch, 1.8 * inch, 1.8 * inch, 1.2 * inch])
        fb_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY_LIGHT),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e2e8f0")),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(fb_table)
    else:
        story.append(Paragraph("No fuel data available for the selected year.", styles["body"]))

    story.append(PageBreak())

    # ---- Page 3: Ship Compliance Table (landscape) ----
    story.append(Paragraph("Ship Compliance Table", ParagraphStyle(
        "ltitle", parent=styles["h1"], alignment=0,
    )))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        f"IMO Number | Ship Name | Vessel Type | Flag State | Gross Tonnage | DWT | Main Fuel Type | "
        f"Total Fuel (MT) | Total CO2 (tonnes) | EEOI",
        ParagraphStyle("guide", parent=styles["body"], fontSize=7, textColor=GREY, leading=10,
    )))

    ship_data = [["IMO Number", "Ship Name", "Vessel Type", "Flag", "GT", "DWT", "Fuel", "Fuel MT", "CO2 t", "EEOI"]]
    for ship in ships:
        ship_em = emissions_by_ship.get(ship["id"], {})
        imo = ship.get("imo_number", "N/A")
        name = ship.get("name", "N/A")
        vtype = ship.get("vessel_type", "N/A")
        flag = ship.get("flag_state", "N/A")
        gt = f"{ship.get('gross_tonnage', 0):,.1f}"
        dwt = f"{ship.get('dwt', 0):,.1f}"
        fuel = ship.get("fuel_type", "N/A")
        fuel_mt = f"{ship_em.get('fuel_mt', 0):,.2f}"
        co2 = f"{ship_em.get('co2', 0):,.2f}"
        # Find EEOI for this ship
        ship_eeoi = "N/A"
        for rec in emissions_records:
            if rec["asset_id"] == ship["id"]:
                voyage = next((v for v in voyages if v["id"] == rec["voyage_id"]), None)
                if voyage and voyage.get("cargo_mt") and voyage.get("distance_nm") and voyage["cargo_mt"] > 0:
                    ship_eeoi = f"{(rec['emissions']['co2'] * 1e6) / (voyage['cargo_mt'] * voyage['distance_nm']):.4f}"
                    break
        ship_data.append([imo, name, vtype, flag, gt, dwt, fuel, fuel_mt, co2, ship_eeoi])

    col_widths = [0.8 * inch, 1.2 * inch, 1.1 * inch, 0.7 * inch, 0.6 * inch, 0.6 * inch,
                  0.6 * inch, 0.65 * inch, 0.6 * inch, 0.6 * inch]
    ship_table = Table(ship_data, colWidths=col_widths, repeatRows=1)
    ship_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 7),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 7),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(ship_table)
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        f"Total: {total_ships} ships | Total Fuel: {total_fuel_mt:,.2f} MT | Total CO2: {total_co2:,.2f} tonnes | Fleet Average EEOI: {fleet_avg_eefi:.4f}" if fleet_avg_eefi else
        f"Total: {total_ships} ships | Total Fuel: {total_fuel_mt:,.2f} MT | Total CO2: {total_co2:,.2f} tonnes",
        ParagraphStyle("ship_total", parent=styles["body_bold"], fontSize=9, textColor=NAVY, leading=12,
    )))
    story.append(PageBreak())

    # ---- Page 4: Fuel Breakdown Table (landscape) ----
    story.append(Paragraph("Fuel Breakdown by Type", ParagraphStyle(
        "ftitle", parent=styles["h1"], alignment=0,
    )))
    story.append(Spacer(1, 6))

    if fuel_breakdown:
        fb_full_data = [["Fuel Type", "Quantity Consumed (MT)", "CO2 Generated (tonnes)", "Voyages", "Emission Factor (t-CO2/t)"]]
        imo_factors = {"HFO": 3.114, "MGO": 3.206, "LNG": 2.750, "Methanol": 1.375}
        for ft in sorted(fuel_breakdown.keys()):
            fb = fuel_breakdown[ft]
            factor = imo_factors.get(ft, "N/A")
            factor_str = f"{factor:.3f}" if isinstance(factor, float) else factor
            fb_full_data.append([ft, f"{fb['fuel_mt']:,.2f}", f"{fb['co2']:,.2f}", str(fb["voyage_count"]), factor_str])
        fb_full_data.append(["TOTAL", f"{total_fuel_mt:,.2f}", f"{total_co2:,.2f}", str(len(emissions_records)), "—"])
        fb_full_table = Table(fb_full_data, colWidths=[1.5 * inch, 2.0 * inch, 2.2 * inch, 1.2 * inch, 2.0 * inch])
        fb_full_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY_LIGHT),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e2e8f0")),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(fb_full_table)
    else:
        story.append(Paragraph("No fuel breakdown data available for the selected year.", styles["body"]))

    story.append(Spacer(1, 12))
    story.append(Paragraph("Fuel Type Description", styles["h2"]))
    fuel_desc = {
        "HFO": "Heavy Fuel Oil – High sulfur residual fuel, most commonly used in large ocean-going vessels.",
        "MGO": "Marine Gas Oil – Low sulfur distillate fuel, compliant with IMO 2020 sulphur cap.",
        "LNG": "Liquefied Natural Gas – Cleanest burning fossil fuel, near-zero SOx/NOx emissions.",
        "Methanol": "Methanol – Emerging alternative fuel with significant CO2 reduction potential.",
    }
    for ft in sorted(fuel_breakdown.keys()):
        desc = fuel_desc.get(ft, "")
        if desc:
            story.append(Paragraph(f"<b>{ft}:</b> {desc}", ParagraphStyle(
                "fdesc", parent=styles["body"], fontSize=8, leading=11, spaceAfter=4, leftIndent=5,
            )))

    story.append(PageBreak())

    # ---- Page 5: Regulatory Declaration / Sign-off ----
    story.append(Paragraph("Official Regulatory Declaration", styles["h1"]))
    story.append(Spacer(1, 12))

    declaration_text = (
        f"I, the undersigned, acting on behalf of <b>{org_name}</b> "
        f"(Organization ID: {org_id}), hereby declare that all information contained in this "
        f"IMO Data Collection System (DCS) Annual Compliance Report for the reporting year "
        f"<b>{year}</b> is true, accurate, and complete to the best of our knowledge and belief. "
        f"This report has been prepared in accordance with the IMO Data Collection System "
        f"requirements (MEPC.1/Circ.1229 and subsequent amendments) and reflects the fleet's "
        f"operational data, fuel consumption, and greenhouse gas emissions for the specified period."
    )
    story.append(Paragraph(declaration_text, styles["declaration"]))
    story.append(Spacer(1, 8))

    # Additional declarations
    story.append(Paragraph(
        "I further confirm that:",
        ParagraphStyle("confirm_head", parent=styles["body_bold"], fontSize=9, leading=12, spaceAfter=4),
    ))
    confirmations = [
        "All vessel data, fuel consumption records, and voyage information have been verified against internal records.",
        "The methodologies used for emissions calculations comply with the IMO MEPC.2/Circ.848 guidelines.",
        "Fuel types and quantities are reported in metric tonnes (MT) as per the DCS format.",
        "CO2 emissions have been calculated using IMO-approved emission factors for each fuel type.",
        "This report is submitted voluntarily and does not constitute a certification of regulatory compliance.",
    ]
    for i, conf in enumerate(confirmations, 1):
        story.append(Paragraph(f"{i}. {conf}", ParagraphStyle(
            "conf", parent=styles["body"], fontSize=9, leading=13, leftIndent=10, spaceAfter=4,
        )))
    story.append(Spacer(1, 12))

    # Sign-off section
    story.append(Paragraph("Sign-Off", styles["h2"]))
    signoff_data = [
        ["", "Name / Title", "Signature", "Date"],
        ["Authorized Representative", "", "", ""],
        ["Fleet Manager", "", "", ""],
        ["Compliance Officer", "", "", ""],
    ]
    signoff_table = Table(signoff_data, colWidths=[2.0 * inch, 2.0 * inch, 1.5 * inch, 1.2 * inch])
    signoff_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(signoff_table)
    story.append(Spacer(1, 16))

    # Final note
    story.append(Paragraph(
        f"Report generated by GreenLane Maritime MVP on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}. "
        f"Report ID: {report_id}. "
        f"This document is confidential and intended for regulatory reporting purposes only.",
        ParagraphStyle("footer_note", parent=styles["body"], fontSize=7, textColor=GREY, leading=10, alignment=1,
    )))

    # Build the PDF
    doc = IMDCSReportDoc(
        filename,
        org_name=org_name,
        report_id=report_id,
        year=year,
        title=f"IMO DCS Annual Compliance Report {year}",
        author=org_name,
        subject=f"IMO DCS Annual Compliance Report for {year}",
    )
    doc.build(story)

    return filename


def get_report_pdf_path(report_id: str) -> Optional[str]:
    """Retrieve the absolute path of a stored PDF by report ID prefix."""
    for fname in os.listdir(REPORTS_DIR):
        if fname.startswith(report_id) and fname.endswith(".pdf"):
            return os.path.abspath(os.path.join(REPORTS_DIR, fname))
    return None


def get_all_report_files() -> list[dict]:
    """List all stored report files with metadata."""
    reports = []
    if not os.path.exists(REPORTS_DIR):
        return reports
    for fname in sorted(os.listdir(REPORTS_DIR)):
        if fname.endswith(".pdf"):
            fpath = os.path.abspath(os.path.join(REPORTS_DIR, fname))
            # Parse report ID from filename (without .pdf)
            rid = fname.replace(".pdf", "")
            reports.append({"report_id": rid, "filename": fname, "path": fpath})
    return reports
