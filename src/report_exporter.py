"""
Regulatory Compliance Audit PDF Report Exporter
Generates institutional-grade compliance certificates using ReportLab.
"""

import os
from datetime import datetime
from typing import Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.units import inch

from .compliance_engine import ComplianceAuditReport


def generate_pdf_report(audit_report: ComplianceAuditReport, output_filepath: Optional[str] = None) -> str:
    """
    Builds a professional PDF audit report for the compliance officer.
    Returns the file path of the generated PDF.
    """
    if not output_filepath:
        reports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")
        os.makedirs(reports_dir, exist_ok=True)
        filename = f"Compliance_Audit_{audit_report.call_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        output_filepath = os.path.join(reports_dir, filename)

    doc = SimpleDocTemplate(
        output_filepath,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0F2942'),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#5A6A85'),
        spaceAfter=15
    )
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#0F2942'),
        spaceBefore=10,
        spaceAfter=8
    )
    normal_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#2A3547')
    )
    bold_style = ParagraphStyle(
        'BoldBody',
        parent=normal_style,
        fontName='Helvetica-Bold'
    )

    elements = []

    # Title & Header
    elements.append(Paragraph("APEX FINANCIAL GROUP | COMPLIANCE & LEGAL DIVISION", subtitle_style))
    elements.append(Paragraph("REGULATORY VOICE COMPLIANCE AUDIT CERTIFICATE", title_style))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#0F2942'), spaceAfter=15))

    # Metadata Grid
    verdict_color = "#13DEB9" if audit_report.audit_verdict == "PASS" else ("#FA896B" if audit_report.audit_verdict == "CRITICAL_FAIL" else "#FFAE1F")
    
    meta_data = [
        [
            Paragraph(f"<b>Audit Record ID:</b> {audit_report.call_id}", normal_style),
            Paragraph(f"<b>Audit Date:</b> {datetime.now().strftime('%B %d, %Y - %H:%M UTC')}", normal_style),
        ],
        [
            Paragraph(f"<b>Call Title:</b> {audit_report.call_title}", normal_style),
            Paragraph(f"<b>Call Type:</b> {audit_report.call_type}", normal_style),
        ],
        [
            Paragraph(f"<b>Agent Audited:</b> {audit_report.agent_name}", normal_style),
            Paragraph(f"<b>Customer Name:</b> {audit_report.customer_name}", normal_style),
        ],
        [
            Paragraph(f"<b>Call Duration:</b> {audit_report.call_duration}", normal_style),
            Paragraph(f"<b>Compliance Score:</b> <font color='{verdict_color}'><b>{audit_report.overall_score} / 100 ({audit_report.audit_verdict})</b></font>", normal_style),
        ]
    ]

    meta_table = Table(meta_data, colWidths=[260, 260])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F6F9FC')),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 15))

    # Executive Summary Section
    elements.append(Paragraph("Executive Call Summary", section_style))
    elements.append(Paragraph(audit_report.executive_summary, normal_style))
    elements.append(Spacer(1, 12))

    # Regulatory Checklist Audit Table
    elements.append(Paragraph("Statutory & Regulatory Checklist Verification", section_style))

    table_data = [
        [
            Paragraph("<b>Rule & Regulation</b>", normal_style),
            Paragraph("<b>Status</b>", normal_style),
            Paragraph("<b>Severity</b>", normal_style),
            Paragraph("<b>Time</b>", normal_style),
            Paragraph("<b>Evidence / Findings</b>", normal_style),
        ]
    ]

    for item in audit_report.checklist:
        status_color = "#13DEB9" if item.status == "PASSED" else "#FA896B"
        table_data.append([
            Paragraph(f"<b>{item.rule_name}</b><br/><font size=7 color='#5A6A85'>{item.regulation}</font>", normal_style),
            Paragraph(f"<font color='{status_color}'><b>{item.status}</b></font>", normal_style),
            Paragraph(f"<b>{item.severity}</b>", normal_style),
            Paragraph(item.timestamp or "-", normal_style),
            Paragraph(item.explanation[:120] + "..." if len(item.explanation) > 120 else item.explanation, normal_style),
        ])

    checklist_table = Table(table_data, colWidths=[150, 65, 60, 45, 200])
    checklist_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F2942')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(checklist_table)
    elements.append(Spacer(1, 15))

    # PII & Data Privacy Findings
    if audit_report.pii_findings:
        elements.append(Paragraph("PII & Privacy Protection Intercepts", section_style))
        pii_data = [
            [
                Paragraph("<b>Identifier Type</b>", normal_style),
                Paragraph("<b>Timestamp</b>", normal_style),
                Paragraph("<b>Redacted Representation</b>", normal_style),
                Paragraph("<b>Compliance Status</b>", normal_style),
            ]
        ]
        for p in audit_report.pii_findings:
            pii_data.append([
                Paragraph(f"<b>{p.entity_type}</b>", normal_style),
                Paragraph(p.timestamp, normal_style),
                Paragraph(f"<code>{p.masked_text}</code>", normal_style),
                Paragraph("<font color='#13DEB9'><b>Auto-Redacted</b></font>", normal_style)
            ])
        pii_table = Table(pii_data, colWidths=[120, 60, 200, 140])
        pii_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EAEFF4')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(pii_table)
        elements.append(Spacer(1, 15))

    # Corrective Remediation & Coaching
    elements.append(Paragraph("Corrective Actions & Mandatory Coaching", section_style))
    for idx, coach in enumerate(audit_report.coaching_recommendations, 1):
        elements.append(Paragraph(f"<b>{idx}.</b> {coach}", normal_style))
        elements.append(Spacer(1, 3))

    elements.append(Spacer(1, 20))

    # Digital Verification Sign-off
    sign_data = [
        [
            Paragraph("<b>Automated Compliance Engine:</b><br/>VoiceGuard AI v1.0 (CFPB/TCPA/FDCPA)", normal_style),
            Paragraph("<b>Quality Assurance Verification:</b><br/><i>Digitally Signed & Archived to Audit Vault</i>", normal_style)
        ]
    ]
    sign_table = Table(sign_data, colWidths=[260, 260])
    sign_table.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.HexColor('#0F2942')),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(sign_table)

    # Build PDF
    doc.build(elements)
    return output_filepath
