"""
Generates the final Health Insurance Detail Declaration PDF —
form data + declaration text + OTP consent proof — using reportlab.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)

BUSINESS_NAME = "ICICI Lombard"
BUSINESS_TAGLINE = "General Insurance — Health Insurance Declaration"

styles = getSampleStyleSheet()
h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=16, spaceAfter=2)
h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=12, spaceBefore=10, spaceAfter=4,
                     textColor=colors.HexColor("#1a3c6e"))
small = ParagraphStyle("small", parent=styles["Normal"], fontSize=8, textColor=colors.grey)
body = ParagraphStyle("body", parent=styles["Normal"], fontSize=9.5, leading=13)
decl = ParagraphStyle("decl", parent=styles["Normal"], fontSize=9, leading=13,
                       borderPadding=8, backColor=colors.HexColor("#f5f7fb"))


def _kv_table(rows, col_widths=(55 * mm, 115 * mm)):
    data = [[Paragraph(f"<b>{k}</b>", body), Paragraph(str(v) if v else "-", body)] for k, v in rows]
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#dddddd")),
    ]))
    return t


def generate_declaration_pdf(data: dict, submission_id: str, submitted_at: str, output_path: str):
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=18 * mm, bottomMargin=15 * mm, leftMargin=18 * mm, rightMargin=18 * mm,
    )
    story = []

    # Header
    story.append(Paragraph(BUSINESS_NAME, h1))
    story.append(Paragraph(BUSINESS_TAGLINE, small))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a3c6e")))
    story.append(Spacer(1, 6))
    story.append(Paragraph("HEALTH INSURANCE — CUSTOMER DETAIL DECLARATION FORM", h1))
    story.append(Paragraph(f"Submission ID: {submission_id} &nbsp;|&nbsp; Submitted: {submitted_at}", small))
    story.append(Spacer(1, 8))

    # Proposer details
    story.append(Paragraph("1. Proposer Details", h2))
    story.append(_kv_table([
        ("Full Name", data["proposer_name"]),
        ("Date of Birth", data["proposer_dob"]),
        ("Gender", data["proposer_gender"]),
        ("Mobile Number", data["proposer_mobile"]),
        ("Email", data["proposer_email"]),
        ("Address", data["proposer_address"]),
        ("City / State / Pincode",
         f"{data['proposer_city']}, {data['proposer_state']} - {data['proposer_pincode']}"),
        ("PAN Number", data.get("proposer_pan")),
        ("Occupation", data.get("proposer_occupation")),
        ("Annual Income", data.get("proposer_annual_income")),
    ]))

    # Insured members
    story.append(Paragraph("2. Insured Member(s) — Medical Details", h2))
    for i, m in enumerate(data["insured_members"], start=1):
        story.append(Paragraph(f"Member {i}: {m['full_name']} ({m['relationship']})", body))
        story.append(_kv_table([
            ("Date of Birth", m["dob"]),
            ("Gender", m["gender"]),
            ("Height / Weight", f"{m.get('height_cm', '-')} cm / {m.get('weight_kg', '-')} kg"),
            ("Pre-existing Disease", "Yes — " + m["pre_existing_details"] if m.get("has_pre_existing_disease") else "No"),
            ("Past Hospitalization / Surgery",
             "Yes — " + m["hospitalization_details"] if m.get("has_past_hospitalization") else "No"),
            ("Tobacco / Alcohol Use", "Yes" if m.get("uses_tobacco_alcohol") else "No"),
            ("Family Medical History", m.get("family_medical_history") or "-"),
        ]))
        story.append(Spacer(1, 4))

    # Policy details
    story.append(Paragraph("3. Policy Details", h2))
    story.append(_kv_table([
        ("Sum Insured Required", data["sum_insured"]),
        ("Plan Type", data["plan_type"]),
        ("Existing Health Insurance",
         f"Yes — {data.get('existing_insurer_name', '-')} / Policy No. {data.get('existing_policy_number', '-')}"
         if data.get("has_existing_health_insurance") else "No"),
    ]))

    # Nominee
    story.append(Paragraph("4. Nominee Details", h2))
    story.append(_kv_table([
        ("Nominee Name", data["nominee_name"]),
        ("Relationship with Proposer", data["nominee_relationship"]),
        ("Nominee Date of Birth", data["nominee_dob"]),
    ]))

    # Declaration & consent
    story.append(Paragraph("5. Customer Declaration & Consent", h2))
    declaration_text = (
        f"I, <b>{data['proposer_name']}</b>, hereby declare that all the information and medical "
        "details furnished by me in this form are true, complete, and correct to the best of my "
        "knowledge and belief. I understand that any misrepresentation, suppression, or "
        "non-disclosure of material facts (including pre-existing diseases and medical history) "
        "may lead to rejection of claim or cancellation of the policy from its inception, as per "
        "the terms and conditions of the insurer. I confirm that I have voluntarily provided this "
        "consent after verifying my identity via a One-Time Password (OTP) sent to my registered "
        "email address, and I authorize ICICI Lombard to use these details for the "
        "purpose of processing my health insurance proposal."
    )
    story.append(Paragraph(declaration_text, decl))
    story.append(Spacer(1, 8))

    # OTP consent proof block
    story.append(Paragraph("OTP Consent Verification Proof", h2))
    story.append(_kv_table([
        ("Email Verified", data["otp_verified_email"]),
        ("Verification Method", "Email OTP"),
        ("Declaration Accepted By Customer", "Yes" if data["declaration_agreed"] else "No"),
        ("Timestamp", submitted_at),
        ("Submission ID", submission_id),
    ]))

    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "This is a system-generated declaration form. Customer consent was captured via email "
        "OTP verification at the time of submission.", small
    ))

    doc.build(story)
    return output_path
