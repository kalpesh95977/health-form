"""
Sends the generated declaration PDF to the business email via SMTP.

Configure via environment variables (see .env.example):
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, RECEIVER_EMAIL

For Gmail: use an "App Password" (not your normal Gmail password) —
Google Account > Security > 2-Step Verification > App Passwords.
"""

import os
import smtplib
from email.message import EmailMessage

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL", "")


def send_pdf_email(pdf_path: str, proposer_name: str, proposer_mobile: str, submission_id: str) -> bool:
    if not SMTP_USER or not SMTP_PASSWORD or not RECEIVER_EMAIL:
        print(f"[EMAIL SKIPPED] SMTP not configured. PDF saved locally at: {pdf_path}")
        return False

    msg = EmailMessage()
    msg["Subject"] = f"Health Declaration Form — {proposer_name} ({submission_id})"
    msg["From"] = SMTP_USER
    msg["To"] = RECEIVER_EMAIL
    msg.set_content(
        f"New health insurance declaration form submitted.\n\n"
        f"Proposer: {proposer_name}\n"
        f"Mobile: {proposer_mobile}\n"
        f"Submission ID: {submission_id}\n\n"
        f"Full details and OTP consent proof are in the attached PDF."
    )

    with open(pdf_path, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="pdf",
            filename=os.path.basename(pdf_path),
        )

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False
