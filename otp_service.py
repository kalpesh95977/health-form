"""
Email OTP handling — no DLT / SMS provider needed.

Sends a 4-digit OTP to the customer's email using the same SMTP
settings configured for the final PDF delivery (SMTP_USER, SMTP_PASSWORD
in environment variables).

TEST_MODE (no SMTP_USER/SMTP_PASSWORD configured):
    - OTP is generated locally and printed to the server console/logs
      instead of actually being emailed, so you can test the full flow
      before SMTP is set up.
"""

import os
import random
import time
import smtplib
from email.message import EmailMessage

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

OTP_EXPIRY_SECONDS = 5 * 60  # 5 minutes

TEST_MODE = not (SMTP_USER and SMTP_PASSWORD)

# In-memory store: { email: {"otp": "1234", "expires_at": ts, "verified": bool} }
# NOTE: for production with multiple server workers, replace this with Redis
# or a DB table — an in-memory dict only works for a single-process deploy.
_otp_store = {}


def _generate_otp() -> str:
    return str(random.randint(1000, 9999))


def _send_email_otp(email: str, otp: str) -> bool:
    msg = EmailMessage()
    msg["Subject"] = "Your OTP for Health Insurance Declaration"
    msg["From"] = SMTP_USER
    msg["To"] = email
    msg.set_content(
        f"Your OTP for verifying your health insurance declaration form is: {otp}\n\n"
        f"This OTP is valid for 5 minutes. Do not share this with anyone.\n\n"
        f"— ICICI Lombard"
    )
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"[EMAIL OTP ERROR] {e}")
        return False


def send_otp(email: str) -> dict:
    email = email.strip().lower()
    if "@" not in email or "." not in email:
        return {"success": False, "message": "Sahi email address daalein."}

    otp = _generate_otp()
    _otp_store[email] = {
        "otp": otp,
        "expires_at": time.time() + OTP_EXPIRY_SECONDS,
        "verified": False,
    }

    if TEST_MODE:
        print(f"[TEST MODE] OTP for {email}: {otp}  (SMTP not configured — not actually emailed)")
        return {"success": True, "message": "OTP generated (test mode)."}

    sent = _send_email_otp(email, otp)
    if not sent:
        return {"success": False, "message": "Email bhejne mein error aayi, dobara try karein."}
    return {"success": True, "message": "OTP email par bhej diya gaya hai."}


def verify_otp(email: str, otp: str) -> dict:
    email = email.strip().lower()
    record = _otp_store.get(email)
    if not record:
        return {"success": False, "message": "Pehle OTP bhejna zaroori hai."}
    if time.time() > record["expires_at"]:
        return {"success": False, "message": "OTP expire ho gaya, dobara bhejwao."}
    if record["otp"] != otp:
        return {"success": False, "message": "Galat OTP."}
    record["verified"] = True
    return {"success": True, "message": "Verified."}


def is_email_verified(email: str) -> bool:
    """Server-side check: was this email actually OTP-verified in this session?"""
    email = email.strip().lower()
    record = _otp_store.get(email)
    return bool(record and record.get("verified") and time.time() <= record["expires_at"] + 600)
