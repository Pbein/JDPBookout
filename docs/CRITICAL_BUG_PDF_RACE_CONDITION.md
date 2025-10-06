# CRITICAL BUG: PDF Race Condition

**Status:** 🚨 CRITICAL - DO NOT USE PARALLEL PROCESSING UNTIL FIXED

**Discovered:** 2025-10-05

**Severity:** HIGH - 45% of PDFs have incorrect content

---

## Summary

When multiple workers (parallel processing) attempt to download PDFs simultaneously, there is a race condition that causes PDFs to be saved with the wrong reference number. 

**Example:**
- File named `165530.pdf` actually contains data for vehicle `165598`
- File named `165545.pdf` actually contains data for vehicle `165612`

**Validation Results:**
- Out of 20 sampled PDFs, 9 (45%) had mismatched content
- This makes the parallel processing system **UNUSABLE** for production

---

## Root Cause

All workers share the **same browser context**. When multiple workers click "Create PDF" at nearly the same time:

1. Worker A clicks "Create PDF" for reference `165530`
2. Worker B clicks "Create PDF" for reference `165598` simultaneously
3. Both workers execute `page.context.expect_page()` - waiting for ANY new page in the context
4. When a PDF tab opens, **either worker might grab it** (race condition)
5. Worker A might grab Worker B's PDF tab and vice versa
6. Each worker saves the PDF with its **own** reference number, not the actual content

### Code Location

`jdp_scraper/vehicle_async.py` lines 59-63:

```python
# Wait for new page/tab to open when clicking Create PDF
async with page.context.expect_page() as new_page_info:
    await create_pdf_button.click()

# Get the new page (PDF tab)
pdf_page = await new_page_info.value  # ⚠️ RACE CONDITION HERE
```

The problem: `page.context.expect_page()` listens to the **entire context**, not just the specific page/worker. So any worker can grab any PDF tab that opens in the context.

---

## Solutions

### Option 1: Sequential PDF Downloads (SIMPLE, SAFE)

**Pros:**
- Guaranteed correct PDFs
- No race conditions
- Simple to implement

**Cons:**
- Slower (but only for PDF download step, ~2 seconds per vehicle)
- Still allows parallel searching/navigation

**Implementation:**
- Use an `asyncio.Lock` around the PDF download section
- Workers can still search and navigate in parallel
- Only the "Click Create PDF → Download → Close Tab" section is serialized

```python
# Global lock for PDF downloads
pdf_download_lock = asyncio.Lock()

async def download_vehicle_pdf_async(...):
    # ... search and navigation code (parallel) ...
    
    # Serialize PDF download to prevent race condition
    async with pdf_download_lock:
        # Click Create PDF
        async with page.context.expect_page() as new_page_info:
            await create_pdf_button.click()
        
        # Get and download PDF
        pdf_page = await new_page_info.value
        # ... download logic ...
        await pdf_page.close()
    
    # ... continue with next vehicle (parallel) ...
```

### Option 2: Separate Browser Contexts per Worker (COMPLEX, FAST)

**Pros:**
- Maintains full parallelism
- No race conditions

**Cons:**
- Multiple logins required (may trigger "active session" errors)
- More memory usage
- More complex

**Implementation:**
- Each worker gets its own browser context
- Each context requires separate login
- May hit session limits on the server

### Option 3: URL-Based Validation (WORKAROUND, NOT RECOMMENDED)

**Pros:**
- Could detect mismatches

**Cons:**
- Doesn't prevent the race condition
- Adds complexity
- Still requires re-downloading incorrect PDFs

**Implementation:**
- Extract reference number from PDF URL before downloading
- Compare with expected reference number
- Retry if mismatch

---

## Recommended Solution

**Option 1: Sequential PDF Downloads with Lock**

This is the best balance of:
- **Safety:** Guaranteed correct PDFs
- **Performance:** Only ~2 seconds serialized per vehicle
- **Simplicity:** Single line change (add lock)

Expected performance:
- Current parallel: 121.3 vehicles/hour (BUT 45% WRONG!)
- With lock: ~100-110 vehicles/hour (estimated, ALL CORRECT ✅)
- Full inventory: ~16-18 hours vs ~15 hours (acceptable trade-off for correctness)

---

## Testing Plan

1. Implement Option 1 (lock-based solution)
2. Run 50-vehicle test with 7 workers
3. Validate ALL 50 PDFs using `validate_pdfs.py`
4. Verify 100% accuracy before full production run
5. Run full inventory (1,820 vehicles) with validation

---

## Action Items

- [ ] Implement `asyncio.Lock` around PDF download section
- [ ] Test with 50 vehicles
- [ ] Validate 100% accuracy
- [ ] Update documentation
- [ ] Run full production inventory

---

## References

- Validation script: `validate_pdfs.py`
- Validation report: `downloads/10-05-2025 (4)/validation_report.json`
- Affected code: `jdp_scraper/vehicle_async.py`

