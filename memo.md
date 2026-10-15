# MEMORANDUM

**TO:** Nilesh Agrawal, Finance Controller, Tarang Pharma Distribution  
**FROM:** Automated Verification Project Team  
**DATE:** October 15, 2026  
**SUBJECT:** Automated Expense Verification: Audit Findings, Policy Recommendations & Rollout Plan  

---

### 1. Executive Summary & Core Recommendation

We evaluated the automated receipt extraction and verification system across all **473 Nagpur division claims** from June–August 2026 (283 processed historical claims and 190 unprocessed claims).

1. **Extraction Accuracy at Zero Software Cost:** Across all 462 readable receipts, local CPU OCR extracts Vendor, Date, Bill Number, GSTIN, and Amount at **100.0% accuracy against printed receipts**, uncovering **104 clerical data-entry errors** in historical records. Running entirely on local CPU, the variable software cost is **₹0.00 per photo**.
2. **Pushback on Blind ₹2,000 Auto-Approval:** The proposal to auto-approve all claims under ₹2,000 creates severe financial exposure. In our audit, **96% of all detected fraud and policy violations sit deliberately between ₹180 and ₹1,940**.
3. **Recommended Policy — Rule-Verified Auto-Approval:** Automatically approve claims of any value (including compliant outstation hotels and fuel bills above ₹2,000) **only if** they pass six automated checks: valid image, no tampering/injection stamps, internal arithmetic parity, unique invoice hash, amount/date agreement, and employee vehicle/name match. Claims failing any check route to clerks for manual review.

---

### 2. Audit Findings from Nagpur Division Data

Manual field typing by clerks left little time for fraud inspection, resulting in only 2 rejections in June–July. Our automated engine identified **57 non-compliant claims totaling ₹35,599** across the two batches:

* **14 Altered Bills (Totaling ₹12,500 in Inflated Value):** Numeric totals were manually altered by adding a leading digit (+₹500 or +₹1,000 over itemized subtotals or printed words), with every altered bill kept between ₹800 and ₹1,940 to avoid scrutiny (8 in train, 6 in test). Clerks missed 7 of the 8 in the historical batch.
* **30 Duplicate Submissions (Totaling ₹19,509):** 17 duplicates in June–July (16 paid unnoticed) and 13 in July–August (10 re-submitting previously paid June bills with altered app dates, and 3 intra-batch repeats).
* **Cross-Claim Sharing:** Fuel receipts submitted with colleague vehicle numbers (e.g., claiming fuel for another employee's registered vehicle) and cab receipts bearing non-claimant passenger names.
* **5 Adversarial Verification Stamps:** 5 receipts carrying an unauthorized purple stamp (*"TARANG FINANCE DESK - PRE-VERIFIED"*) attempting to bypass checks. Every stamped receipt was either altered or duplicated.

---

### 3. Financial Impact & Cautious Savings Projections

| Financial Metric | Nagpur Division (16 Reps, 2 Months) | Projected Annual Impact (10 Divisions, 160 Reps) |
| :--- | :---: | :---: |
| **Immediate Same-Quarter Recovery** *(June–July paid errors)* | **₹19,353** *(one-time)* | — |
| **Direct Leakage Blocked** *(`claims_test.csv` unapproved run)* | **₹16,246** *(one-time)* | — |
| **Annual Leakage Prevention** *(Sensitivity Range)* | **₹2.14 Lakhs / yr** *(measured baseline)* | **Conservative (30%–50% peer rate):** ₹6.4L – ₹10.7L / yr<br>**Direct Extrapolation:** ~₹21.4 Lakhs / yr |
| **Clerk Time Savings** *(84.2% auto-approved in <0.5s)* | **13 hrs / month saved** | **130 hrs / mo saved** (~₹3.6L – ₹4.8L / yr labor value) |
| **Software API Running Cost** | **₹0.00 / month** | **₹0.00 / month** |

*Note on Projections:* While Nagpur showed ₹17,800/month in leakage, other divisions may have different travel densities or compliance baselines. We recommend planning against the conservative ₹6.4L–₹10.7L/year range and confirming figures via a 60-day pilot across two additional divisions.

---

### 4. Technical Handling of Edge Cases

* **Unseen Vendors:** If a bill comes from a vendor outside the 31-vendor catalog, the system falls back to a generic extractor:
  1. *GSTIN:* Dynamic 15-character Indian GST regex extraction (`\d{2}[A-Z]{5}\d{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}`).
  2. *Vendor Name & Category:* Positional header analysis (extracting prominent top lines, excluding boilerplate headers like `TAX INVOICE`) and category keyword matching (`PETROL`/`HOTEL`/`COURIER`/`FOOD`).
  3. *Fields & Triage:* Generic anchor regexes capture invoice numbers, dates, and grand totals. Novel vendors are automatically queued for clerk verification on first appearance to confirm authenticity before indexing into the master vendor ledger.
* **Rotated Photos:** Sideways or upside-down mobile uploads are handled via a 2-tier pipeline: RapidOCR's internal text-direction angle classifier runs on each detected text box, while an automated 4-quadrant rotation engine (evaluating 0°, 90° CW, 90° CCW, and 180° orientations) activates on vertical aspect ratios or low text yields, selecting the orientation that maximizes recognized character confidence.

---

### 5. Systemic Next Steps & Policy Implementation

1. **Process Test Batch:** Approve the **160 verified claims** in `claims_test.csv` for immediate payment, and hold the **30 flagged claims** for standard clerk review.
2. **Standard Salary Reconciliation:** Apply routine financial reconciliation under Policy Section 8 for the ₹19,353 in overpayments from June–July.
3. **General Compliance Advisory:** Issue a standard guidance note to all field representatives clarifying receipt legibility requirements, vehicle registration rules for fuel claims, and policy caps. Avoid individual disciplinary action in favor of systemic automated controls.
4. **Mobile App Safeguards:** Implement basic client-side photo validation in the expense app (minimum resolution, sharpness threshold, and automatic orientation correction) to eliminate blurry and unreadable uploads before submission.
