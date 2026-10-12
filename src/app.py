import json
import os
from typing import Optional
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from src.engine import ClaimVerificationEngine
from src.extractor import run_live_ocr_on_image_bytes

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
EXTERNAL_IMAGES_DIR = os.path.join(os.path.dirname(BASE_DIR), "task2_data", "images")
SAMPLE_IMAGES_DIR = os.path.join(DATA_DIR, "sample_images")

app = FastAPI(
    title="Tarang Pharma — Automated Expense Receipt Verification API",
    description="Local CPU OCR + 6-Point Forensic & Policy Verification Engine for Field Expense Claims",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = ClaimVerificationEngine(DATA_DIR)

SHOWCASE_IDS = [
    ("CLM-31086", "Clean Fuel Claim (Approve — Rs 300.00)"),
    ("CLM-31148", "Outstation GST Hotel Invoice (Approve — Rs 2,352.00)"),
    ("CLM-31401", "Prompt Injection Stamp + Altered Cab Bill (+Rs 1,000)"),
    ("CLM-31176", "Prompt Injection Stamp + Cross-Batch Duplicate Tea Bill"),
    ("CLM-31120", "Colleague's Fuel Bill + Vehicle Mismatch (MH31 FA 2290)"),
    ("CLM-31192", "Altered Restaurant Bill (Rs 200 -> Rs 1,200)"),
    ("CLM-31503", "Altered Courier Receipt (Rs 226.56 -> Rs 1,226.56)"),
    ("CLM-31288", "Overclaimed Hotel Bill (Claimed Rs 2,852 vs Bill Rs 2,352)"),
    ("CLM-31497", "Colleague Cab Bill + Passenger Name & Date Mismatch"),
    ("CLM-31333", "Cropped Receipt Photo (Bottom Date & Total Cut Off)"),
]

@app.get("/", response_class=HTMLResponse)
async def index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/api/employees")
async def list_employees():
    records = []
    for emp_id, r in engine.emps_df.iterrows():
        records.append({
            "emp_id": emp_id,
            "name": str(r["name"]),
            "designation": str(r["designation"]),
            "headquarter": str(r["headquarter"]),
            "vehicle_no": str(r["vehicle_no"]),
            "grade": str(r["grade"]),
        })
    return {"employees": records}

@app.get("/api/samples")
async def list_samples():
    samples = []
    test_indexed = engine.test_df.set_index("claim_id")
    for cid, label in SHOWCASE_IDS:
        if cid not in test_indexed.index:
            continue
        r = test_indexed.loc[cid]
        fn = engine.resolve_image_filename(r.get("image_file"))
        emp_id = str(r["emp_id"])
        emp_row = engine.emps_df.loc[emp_id]
        samples.append({
            "claim_id": cid,
            "label": label,
            "emp_id": emp_id,
            "emp_name": str(emp_row["name"]),
            "emp_hq": str(emp_row["headquarter"]),
            "emp_vehicle": str(emp_row["vehicle_no"]),
            "emp_grade": str(emp_row["grade"]),
            "submitted_on": str(r["submitted_on"]),
            "expense_date": str(r["expense_date"]),
            "category": str(r["category"]),
            "vendor": str(r["vendor"]),
            "amount_claimed": str(r["amount_claimed"]),
            "rep_comment": str(r["rep_comment"]) if str(r["rep_comment"]) != "nan" else "",
            "image_file": fn or "",
            "image_url": f"/api/sample-image/{fn}" if fn else "",
        })
    return {"samples": samples}

@app.get("/api/sample-image/{filename}")
async def get_sample_image(filename: str):
    safe_name = os.path.basename(filename)
    for folder in [SAMPLE_IMAGES_DIR, EXTERNAL_IMAGES_DIR]:
        cand = os.path.join(folder, safe_name)
        if os.path.exists(cand):
            return FileResponse(cand)
    raise HTTPException(status_code=404, detail="Sample image not found")

@app.get("/api/metrics")
async def get_metrics():
    metrics_path = os.path.join(REPORTS_DIR, "evaluation_metrics.json")
    if os.path.exists(metrics_path):
        with open(metrics_path, "r", encoding="utf-8") as f:
            return JSONResponse(content=json.load(f))
    return JSONResponse(content={})

@app.post("/api/verify")
async def verify_receipt_endpoint(
    claim_id: str = Form("LIVE-001"),
    emp_id: str = Form("TPD-0412"),
    submitted_on: str = Form("2026-08-05"),
    expense_date: str = Form("2026-08-04"),
    category: str = Form("Fuel"),
    vendor: str = Form(""),
    amount_claimed: str = Form("0"),
    rep_comment: str = Form(""),
    image_file: str = Form(""),
    image: Optional[UploadFile] = File(None),
):
    """
    Verify a receipt photo against the claim as entered by the field rep.
    Accepts either an uploaded image file (`image`) or a known `image_file` name.
    Runs local CPU RapidOCR when a new image is uploaded (no paid API key required).
    """
    ocr_entry = None
    used_filename = image_file

    if image is not None and image.filename:
        raw_bytes = await image.read()
        if raw_bytes:
            # Check if the uploaded file matches a cached receipt filename for fast deterministic lookup,
            # otherwise run live RapidOCR on the uploaded bytes.
            resolved = engine.resolve_image_filename(image.filename)
            if resolved and resolved in engine.ocr_cache:
                ocr_entry = engine.ocr_cache[resolved]
                used_filename = resolved
            else:
                ocr_entry = run_live_ocr_on_image_bytes(raw_bytes)
                used_filename = image.filename

    claim_payload = {
        "claim_id": claim_id,
        "emp_id": emp_id,
        "submitted_on": submitted_on,
        "expense_date": expense_date,
        "category": category,
        "vendor": vendor,
        "amount_claimed": amount_claimed,
        "rep_comment": rep_comment,
        "image_file": used_filename,
    }

    result = engine.verify_claim(claim_payload, ocr_entry=ocr_entry)
    return JSONResponse(content=result)
