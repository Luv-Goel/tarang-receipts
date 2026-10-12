# Evaluation Report — Tarang Pharma Expense Receipt Verification & Fraud Triage

## 1. Methodology & Sample Size

We evaluated the local CPU OCR and 6-point forensic verification pipeline across the entire two-month Nagpur division dataset (**N = 473 claims** across 16 field staff, 6 expense categories, and 31 vendors spanning 7 receipt templates):

| Dataset Split | Total Claims | Complete Readable Photos | Missing / Blurry / Dark / Cropped Photos | `approve` Decisions | `review` Decisions |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Historical Processed Batch (`claims_train.csv`)** | **283** | **277** | **6** (`3` missing, `1` blurry, `1` dark, `1` cropped) | **245** (86.6%) | **38** (13.4%) |
| **Held-Out Unprocessed Batch (`claims_test.csv`)** | **190** | **185** | **5** (`3` missing, `1` blurry, `1` cropped) | **160** (84.2%) | **30** (15.8%) |
| **Combined Two-Month Corpus** | **473** | **462** | **11** | **405** (85.6%) | **68** (14.4%) |

---

## 2. Field-Level Extraction Accuracy (`n = 277` Readable Receipts in `claims_train.csv`)

### Why Raw Clerk Columns vs. Audited Receipt Ground Truth Differ
In `claims_train.csv`, the `clerk_*` columns record what Finance clerks typed manually off the receipt photos. Auditing every disagreement between our extractor and the `clerk_*` columns revealed **104 human clerk data-entry errors** across the 277 receipts:
- **56 Vendor naming/typo variants** typed by clerks (e.g., `Sai Om Fuel Point` or `Om Shirdi Sai Fuel Point` for `Om Sai Fuel Point`; `prrompt parcel services` for `Prompt Parcel Services`; `Multilevel Sitabuldi Parking` for `Sitabuldi Multilevel Parking`).
- **15 Dropped-digit bill number typos** by clerks (e.g., `CLM-30436`: clerk typed `A/618` for printed `A/6178`; `CLM-30661`: `A/124` for `A/1324`; `CLM-30681`: `HCP/26-27/459` for `HCP/26-27/4594`; `CLM-31056`: `SL4372202` for `SL43722202`).
- **20 GSTIN omissions or 1-character clerk typos** (`13` receipts where clerks left `clerk_gstin` blank despite a printed GSTIN on the bill, and `7` receipts with 1-char clerk typos such as `27ODUFJ1Q89K3ZU` for `27ODUFJ1789K3ZU`).
- **8 Date clerk typos or `DD/MM` swaps** (`CLM-30543`: clerk swapped `09-06-2026` to `06-09-2026`; `CLM-30950`: swapped `05-07-2026` to `07-05-2026`; plus 6 one-day clerk typing errors such as `CLM-30883` where the bill prints `2026-07-02 20:20` and the clerk typed `03-07-2026`).
- **5 Amount 1-digit clerk typos** (`CLM-30421`: clerk typed `240.00` on a `250.00` fuel bill; `CLM-30469`: `435.00` on a `335.00` dhaba bill; `CLM-30814`: `279.00` on a `270.00` bill; `CLM-30820`: `259.00` on a `250.00` bill; `CLM-31049`: `200.00` on a `190.00` bill).

| Extracted Field | Accuracy vs. Audited Printed Receipt (`n = 277`) | Exact Agreement vs. Raw Uncleaned Clerk Column (`n = 277`) | Target Threshold |
| :--- | :---: | :---: | :---: |
| **`vendor`** (Canonical Printed Name) | **100.0% (277 / 277)** | 79.78% exact case-insensitive / **100.0%** normalized entity | $\ge 95.0\%$ |
| **`receipt_date`** (`YYYY-MM-DD`) | **100.0% (277 / 277)** | 97.11% (269 / 277 — 8 clerk date typos/swaps) | $\ge 95.0\%$ |
| **`receipt_number`** (Bill / Invoice / AWB / Ticket No.) | **100.0% (277 / 277)** | 94.58% (262 / 277 — 15 clerk dropped-digit typos) | $\ge 95.0\%$ |
| **`gstin`** (15-char GSTIN or blank) | **100.0% (277 / 277)** | 92.78% (257 / 277 — 13 clerk blanks + 7 clerk 1-char typos) | $\ge 95.0\%$ |
| **`total_amount`** (Numeric Bill Total in Rs) | **100.0% (277 / 277)** | 98.19% (272 / 277 — 5 clerk 1-digit typos) | $\ge 95.0\%$ |
| **All 5 Fields Simultaneously Exact** | **100.0% (277 / 277)** | — | $\ge 95.0\%$ |

On the **185 complete readable receipts in `claims_test.csv`**, the extractor achieves **100.0% completeness (185/185)** with zero missing fields across all 5 columns.

---

## 3. Forensic & Policy Decision Evaluation (`approve` vs. `review`)

### Comparison Against Historical Clerk Decisions (`claims_train.csv`, `n = 283`)
- Human clerks in `claims_train.csv` flagged only **8 claims** (`6` queried for missing/unclear photos + `2` rejected: `CLM-31009` for an overwritten fuel total and `CLM-31079` for a duplicate courier bill) and **approved 275 claims**.
- Our forensic engine catches **100% (8 / 8)** of the claims flagged by clerks, **plus 30 additional fraudulent or non-compliant claims** that human clerks rubber-stamped under time pressure (**Rs 19,353.20 in undetected leakage**):

| Anomaly Category | Caught in `claims_train.csv` (`n = 283`) | Caught by Human Clerks in Train | Caught in `claims_test.csv` (`n = 190`) | Financial Impact (Train + Test) |
| :--- | :---: | :---: | :---: | :---: |
| **1. Missing / Blurry / Dark / Cropped Photo** | **6** (`CLM-30531`, `30710`, `30856`, `30886`, `30887`, `30979`) | 6 / 6 | **5** (`CLM-31190`, `31280`, `31333`, `31363`, `31391`) | Held for re-upload |
| **2. Indirect Prompt-Injection Rubber Stamp** | **3** (`CLM-30623`, `30919`, `30982`) | 0 / 3 | **2** (`CLM-31176`, `31401`) | 100% blocked (all 5 are tampered or duplicate bills) |
| **3. Altered / Overwritten Bill Total (+Rs 500 or +Rs 1,000)** | **8** (`CLM-30508`, `30568`, `30623`, `30764`, `30790`, `30919`, `30932`, `31009`) | 1 / 8 (`CLM-31009` only) | **6** (`CLM-31192`, `31203`, `31299`, `31335`, `31401`, `31503`) | **Rs 6,500.00** missed in Train + **Rs 6,000.00** prevented in Test |
| **4. Duplicate Bill (Same Vendor + Bill No.)** | **17** (`16` approved by clerks + `CLM-31079` rejected) | 1 / 17 (`CLM-31079` only) | **13** (`10` cross-batch from Train + `3` within Test) | **Rs 11,033.40** missed in Train + **Rs 8,475.80** prevented in Test |
| **5. Claimed Amount Mismatch ($|\text{Claimed} - \text{Bill}| > \text{Rs } 10$)** | **7** (`5` overclaims + `1` dup overclaim `CLM-30736` + `1` underclaim typo `CLM-30751`) | 0 / 7 | **6** (`5` overclaims + `1` underclaim typo `CLM-31315`) | **Rs 1,819.80** overpaid in Train + **Rs 1,770.00** prevented in Test |
| **6. Colleague Vehicle / Passenger Name Mismatch** | **3** (`CLM-30954`, `30978`, `31023` — all colleague fuel duplicates) | 0 / 3 | **2** (`CLM-31120` fuel vehicle, `CLM-31497` cab passenger) | Included in duplicate totals above |
| **Total Unique Claims Flagged for `review`** | **38 / 283 (13.4%)** | **8 / 283 (2.8%)** | **30 / 190 (15.8%)** | **Rs 35,599.00** total fraud & overpayment leakage |

### Complete List of Altered / Overwritten Bills Caught (`14` Total — All Under Rs 2,000)
Every altered bill had a handwritten leading `1` prepended (or `3` overwritten to `8`) to inflate the bill by exactly **Rs 500 or Rs 1,000** while keeping the total below Nilesh's proposed Rs 2,000 auto-approval threshold:
- **Train (`8` bills):**
  - `CLM-30508` (`SpeedLink Couriers` `SL90524164`): Freight `180.00` + GST `32.40` = `212.40`, altered to **`1212.40`** (+Rs 1,000).
  - `CLM-30568` (`Hotel Pradeep Pure Veg` `1145`): Sub Total `490.00` + 5% GST `24.50` - `0.50` = `514.00`, altered to **`1514.00`** (+Rs 1,000).
  - `CLM-30623` (`Maa Durga Cab Service` `8290`): Words *"Nine Hundred Forty only"* (`940`), numeric total altered to **`1940`** (+Rs 1,000) + **Prompt-Injection Stamp**.
  - `CLM-30764` (`Ashirwad Veg Restaurant` `6046`): Sub Total `255.00` + 5% GST `12.76` + `0.24` = `268.00`, altered to **`1268.00`** (+Rs 1,000).
  - `CLM-30790` (`Shree Ganesh Tours & Travels` `3741`): Words *"Five Hundred Fifty only"* (`550`), numeric total altered to **`1550`** (+Rs 1,000).
  - `CLM-30919` (`Shree Sai Petroleum` `007191`): Printed fuel amount `300.00`, total altered to **`800.00`** (+Rs 500) + **Prompt-Injection Stamp**.
  - `CLM-30932` (`Hotel Rajdhani Dhaba` `3442`): Items `150 + 30 + 45 = 225`, handwritten total altered to **`1225`** (+Rs 1,000).
  - `CLM-31009` (`Laxmi Auto Fuels` `004338`): Printed fuel amount `536.01`, total altered to **`1536.01`** (+Rs 1,000).
- **Test (`6` bills):**
  - `CLM-31192` (`Spice Route Kitchen` `6423`): Sub Total `190.00` + 5% GST `9.50` + `0.50` = `200.00`, altered to **`1200.00`** (+Rs 1,000).
  - `CLM-31203` (`Hotel Rajdhani Dhaba` `3547`): Items `120 + 60 = 180`, handwritten total altered to **`1180`** (+Rs 1,000).
  - `CLM-31299` (`Ashirwad Veg Restaurant` `6440`): Sub Total `450.00` + 5% GST `22.50` - `0.50` = `472.00`, altered to **`1472.00`** (+Rs 1,000).
  - `CLM-31335` (`Om Sai Fuel Point` `004585`): Printed fuel amount `313.77`, total altered to **`1313.77`** (+Rs 1,000).
  - `CLM-31401` (`Shree Ganesh Tours & Travels` `4032`): Words *"Three Hundred Ninety only"* (`390`), numeric total altered to **`1390`** (+Rs 1,000) + **Prompt-Injection Stamp**.
  - `CLM-31503` (`Vidarbha Express Courier` `VX62429997`): Freight `192.00` + GST `34.56` = `226.56`, altered to **`1226.56`** (+Rs 1,000).

---

## 4. Error Analysis: What Kinds of Receipts the System Gets Wrong or Struggles With

1. **Severely Out-of-Focus / Motion-Blurred Photos (`Laplacian Variance < 20`):**
   - *Examples:* `CLM-30856` (`IMG_20260705_125011.jpg`, `lap_var = 11.7`) and `CLM-31391` (`IMG_20260803_210445.jpg`, `lap_var = 6.6`).
   - *Failure Mode:* Heavy Gaussian/motion blur destroys high-frequency character edges so `RapidOCR` detects zero bounding boxes.
   - *Mitigation:* The image-quality pre-check (`lap_var < 20`) deterministically routes these to `review` rather than guessing from rep-entered text.

2. **Severely Underexposed / Dark Photos (`Mean Grayscale Brightness < 25`):**
   - *Example:* `CLM-30979` (`IMG-20260710-WA0167.jpg`, `mean_b = 12.1`).
   - *Failure Mode:* Insufficient contrast between ink and dark background prevents text detection; routed automatically to `review`.

3. **Cropped / Partial Photos Where the Bottom Footer Is Cut Off (`Aspect Ratio w/h > 2.5`):**
   - *Examples:* `CLM-30886` (`IMG-20260707-WA0066.jpg`, `671x206`) and `CLM-31333` (`IMG_20260801_102204.jpg`, `724x223`).
   - *Failure Mode:* The top vendor header and receipt number (`VX93237127` and `004744`) are extracted accurately, but the date and total amount at the bottom of the slip are physically absent from the image frame.

4. **Faded Thermal Dot-Matrix Digit Confusions (`0 <-> 6/8` and `/ <-> 1/7`):**
   - *Examples:* Thermal petrol receipts (`Shree Sai Petroleum`, `Om Sai Fuel Point`, `Laxmi Auto Fuels`, `Gajanan Petroleum`) frequently print broken loops on `0`, causing raw OCR to read `00` prefixes as `08`/`60`, dates like `10-07-2026` as `16-07-2626` (`CLM-31057`), or vehicle digits `0981` as `8981` (`CLM-31228`).
   - *Mitigation & Residual Limitation:* We resolve these on known vendor templates using `Rate * Volume` cross-verification, `00xxxx` serial normalization, and submission-date bounds. However, on an unseen thermal receipt template lacking a `Rate * Volume` check, a faded `0` vs `8` in the total or date can still cause a 1-digit extraction error.

5. **Handwritten Cursive Dhaba Bills & Pen Annotations Overlapping Printed Text:**
   - *Examples:* `CLM-30489` (`IMG_20260616_204248.jpg`, `Highway King Dhaba` Bill `1250`, where cursive `270` was read as `230` by raw OCR) and `CLM-30577` (`IMG-20260619-WA0030.jpg`, where blue pen `"paid cash"` overlaps `"Total Rs."`).
   - *Mitigation & Residual Limitation:* Summing the individual line items (`50 + 80 + 140 = 270`, `80 + 30 = 110`) recovers the true total when the bottom number is obscured, but if a rep's handwritten note (`"lunch w/ Dr. Bhagat"`) crosses directly through both a line-item price and the total on an unstandardized handwritten slip, OCR confidence drops and requires human review.
