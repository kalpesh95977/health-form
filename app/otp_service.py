"""
SMS OTP handling via MSG91.

TEST_MODE (no MSG91 key configured):
    - OTP is generated locally and printed to the server console/logs
      instead of actually being sent, so you can test the full flow
      before your MSG91 + DLT registration is ready.

LIVE MODE (MSG91_AUTH_KEY set in environment):
    - Uses MSG91's OTP API (https://control.msg91.com/api/v5/otp) to
      actually send and verify SMS OTPs.

Swap to a different provider (Fast2SMS etc.) by editing _send_via_msg91
and _verify_via_msg91 only — the rest of the app doesn't need to change.
"""

import os
import random
import time
import requests

MSG91_AUTH_KEY = os.getenv("MSG91_AUTH_KEY", "")
MSG91_TEMPLATE_ID = os.getenv("MSG91_TEMPLATE_ID", "")
OTP_EXPIRY_SECONDS = 5 * 60  # 5 minutes

TEST_MODE = not MSG91_AUTH_KEY

# In-memory store: { mobile: {"otp": "1234", "expires_at": ts, "verified": bool} }
# NOTE: for production with multiple server workers, replace this with Redis
# or a DB table — an in-memory dict only works for a single-process deploy.
_otp_store = {}


def _generate_otp() -> str:
    return str(random.randint(1000, 9999))


def send_otp(mobile: str) -> dict:
    if len(mobile) != 10 or not mobile.isdigit():
        return {"success": False, "message": "Mobile number 10 digit ka hona chahiye."}

    if TEST_MODE:
        otp = _generate_otp()
        _otp_store[mobile] = {
            "otp": otp,
            "expires_at": time.time() + OTP_EXPIRY_SECONDS,
            "verified": False,
        }
        print(f"[TEST MODE] OTP for {mobile}: {otp}  (MSG91_AUTH_KEY not set — not actually sent via SMS)")
        return {"success": True, "message": "OTP generated (test mode)."}

    return _send_via_msg91(mobile)


def verify_otp(mobile: str, otp: str) -> dict:
    if TEST_MODE:
        record = _otp_store.get(mobile)
        if not record:
            return {"success": False, "message": "Pehle OTP bhejna zaroori hai."}
        if time.time() > record["expires_at"]:
            return {"success": False, "message": "OTP expire ho gaya, dobara bhejwao."}
        if record["otp"] != otp:
            return {"success": False, "message": "Galat OTP."}
        record["verified"] = True
        return {"success": True, "message": "Verified."}

    return _verify_via_msg91(mobile, otp)


def is_mobile_verified(mobile: str) -> bool:
    """Server-side check: was this mobile actually OTP-verified in this session?"""
    if TEST_MODE:
        record = _otp_store.get(mobile)
        return bool(record and record.get("verified") and time.time() <= record["expires_at"] + 600)

    # In live mode, MSG91 verify-OTP already confirmed it; we track it locally too
    record = _otp_store.get(mobile)
    return bool(record and record.get("verified"))


# ---------------------------------------------------------------------------
# MSG91 live integration
# ---------------------------------------------------------------------------

def _send_via_msg91(mobile: str) -> dict:
    url = "https://control.msg91.com/api/v5/otp"
    params = {
        "template_id": MSG91_TEMPLATE_ID,
        "mobile": f"91{mobile}",
        "authkey": MSG91_AUTH_KEY,
    }
    try:
        resp = requests.post(url, params=params, timeout=10)
        data = resp.json()
        if data.get("type") == "success":
            _otp_store[mobile] = {"verified": False, "expires_at": time.time() + OTP_EXPIRY_SECONDS}
            return {"success": True, "message": "OTP sent."}
        return {"success": False, "message": data.get("message", "OTP bhejne mein error aayi.")}
    except requests.RequestException as e:
        return {"success": False, "message": f"MSG91 se connect nahi ho paya: {e}"}


def _verify_via_msg91(mobile: str, otp: str) -> dict:
    url = "https://control.msg91.com/api/v5/otp/verify"
    params = {"otp": otp, "mobile": f"91{mobile}", "authkey": MSG91_AUTH_KEY}
    try:
        resp = requests.post(url, params=params, timeout=10)
        data = resp.json()
        if data.get("type") == "success":
            record = _otp_store.setdefault(mobile, {})
            record["verified"] = True
            return {"success": True, "message": "Verified."}
        return {"success": False, "message": data.get("message", "Galat ya expired OTP.")}
    except requests.RequestException as e:
        return {"success": False, "message": f"MSG91 se connect nahi ho paya: {e}"}
