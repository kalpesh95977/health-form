"""
Vidhi Financial Services — Health Insurance Detail Declaration Form
FastAPI backend: serves the form, handles SMS OTP verification, generates
a declaration PDF on submit, and emails it to the business inbox.
"""

import os
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import List, Optional

from otp_service import send_otp, verify_otp, is_mobile_verified
from pdf_generator import generate_declaration_pdf
from email_service import send_pdf_email

BASE_DIR = Path(__file__).resolve().parent
PDF_DIR = BASE_DIR / "generated_pdfs"
PDF_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Vidhi Financial Services — Health Declaration Form")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static"), check_dir=False), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

class InsuredMember(BaseModel):
    relationship: str
    full_name: str
    dob: str
    gender: str
    height_cm: Optional[str] = ""
    weight_kg: Optional[str] = ""
    has_pre_existing_disease: bool = False
    pre_existing_details: Optional[str] = ""
    has_past_hospitalization: bool = False
    hospitalization_details: Optional[str] = ""
    uses_tobacco_alcohol: bool = False
    family_medical_history: Optional[str] = ""


class SendOtpRequest(BaseModel):
    mobile: str = Field(..., min_length=10, max_length=10)


class VerifyOtpRequest(BaseModel):
    mobile: str
    otp: str


class FormSubmission(BaseModel):
    # Proposer details
    proposer_name: str
    proposer_dob: str
    proposer_gender: str
    proposer_mobile: str
    proposer_email: str
    proposer_address: str
    proposer_city: str
    proposer_state: str
    proposer_pincode: str
    proposer_pan: Optional[str] = ""
    proposer_occupation: Optional[str] = ""
    proposer_annual_income: Optional[str] = ""

    # Insured members (self / spouse / kids / parents etc.)
    insured_members: List[InsuredMember]

    # Policy details
    sum_insured: str
    plan_type: str  # Individual / Family Floater
    has_existing_health_insurance: bool = False
    existing_insurer_name: Optional[str] = ""
    existing_policy_number: Optional[str] = ""

    # Nominee
    nominee_name: str
    nominee_relationship: str
    nominee_dob: str

    # Consent
    declaration_agreed: bool
    otp_verified_mobile: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def serve_root(request: Request):
    return templates.TemplateResponse("form.html", {"request": request, "lang": "en"})


@app.get("/en", response_class=HTMLResponse)
async def serve_form_en(request: Request):
    return templates.TemplateResponse("form.html", {"request": request, "lang": "en"})


@app.get("/gu", response_class=HTMLResponse)
async def serve_form_gu(request: Request):
    return templates.TemplateResponse("form.html", {"request": request, "lang": "gu"})


@app.post("/api/send-otp")
async def api_send_otp(payload: SendOtpRequest):
    result = send_otp(payload.mobile)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return {"success": True, "message": "OTP bhej diya gaya hai."}


@app.post("/api/verify-otp")
async def api_verify_otp(payload: VerifyOtpRequest):
    result = verify_otp(payload.mobile, payload.otp)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return {"success": True, "message": "Mobile number verify ho gaya."}


@app.post("/api/submit-form")
async def api_submit_form(payload: FormSubmission):
    if not payload.declaration_agreed:
        raise HTTPException(status_code=400, detail="Declaration accept karna zaroori hai.")

    if payload.otp_verified_mobile != payload.proposer_mobile:
        raise HTTPException(
            status_code=400,
            detail="OTP verify kiya gaya number aur proposer ka mobile number match nahi karta.",
        )

    # Re-confirm OTP was actually verified for this session (server-side truth,
    # not just trusting the value the browser sent back)
    if not is_mobile_verified(payload.otp_verified_mobile):
        raise HTTPException(status_code=400, detail="OTP verification expire ho gaya, dobara verify karein.")

    submission_id = str(uuid.uuid4())[:8]
    submitted_at = datetime.now().strftime("%d-%b-%Y %I:%M %p")

    pdf_path = PDF_DIR / f"health_declaration_{submission_id}.pdf"
    generate_declaration_pdf(
        data=payload.model_dump(),
        submission_id=submission_id,
        submitted_at=submitted_at,
        output_path=str(pdf_path),
    )

    email_sent = send_pdf_email(
        pdf_path=str(pdf_path),
        proposer_name=payload.proposer_name,
        proposer_mobile=payload.proposer_mobile,
        submission_id=submission_id,
    )

    return JSONResponse(
        {
            "success": True,
            "submission_id": submission_id,
            "email_sent": email_sent,
            "message": "Form successfully submit ho gaya. Dhanyavaad!",
        }
    )


@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
