# Pre-Flight Checklist for Full Inventory Run (2,000 Vehicles)

## ✅ Critical Items Before Running

### 1. **Environment Configuration**
- [ ] `.env` file exists with valid credentials
  ```
  JD_USER=your_actual_username
  JD_PASS=your_actual_password
  HEADLESS=false  (or true for background mode)
  MAX_DOWNLOADS=9999  (or omit to process all)
  ```
- [ ] Credentials are correct and tested (login works)
- [ ] Virtual environment is activated (`.venv`)

### 2. **Dependencies**
- [ ] All packages installed: `pip install -r requirements.txt`
- [ ] Playwright browsers installed: `playwright install chromium`
- [ ] Python 3.10+ is being used

### 3. **Disk Space**
- [ ] **Minimum 2 GB free space** for ~2,000 PDFs
  - Average PDF: ~50-70 KB
  - 2,000 PDFs × 70 KB = ~140 MB
  - Plus CSV, tracking, metrics: ~50 MB
  - **Recommended: 500 MB - 1 GB free**
- [ ] Check: `Get-PSDrive C | Select-Object Used,Free`

### 4. **Network & System**
- [ ] Stable internet connection (will run 10+ hours)
- [ ] Computer won't sleep/hibernate during run
  - Windows: Settings → Power → Screen and sleep → Never
- [ ] No scheduled restarts or updates
- [ ] Consider: Run on a dedicated machine or server

### 5. **Session Management**
- [ ] Only one instance of the program running
- [ ] No manual logins to JD Power site (avoid session conflicts)
- [ ] Browser is not already open to the site

---

## 🚀 How to Run for Full Inventory

### **Option 1: Process All Vehicles (Recommended)**
```bash
# Activate virtual environment
.\.venv\Scripts\activate

# Run the program (will process all pending vehicles)
python main.py
```

### **Option 2: Process in Batches**
```bash
# Set batch size in .env
MAX_DOWNLOADS=200

# Run multiple times until complete
python main.py  # Run 1: 200 vehicles
python main.py  # Run 2: next 200 vehicles
# ... continue until all done
```

### **Option 3: Headless Mode (Background)**
```bash
# Set in .env
HEADLESS=true

# Run in background
python main.py
```

---

## 📊 Expected Performance

Based on testing with 50 vehicles:

| Metric | Value |
|--------|-------|
| Average per vehicle | ~17-60 seconds |
| Throughput | ~60 vehicles/hour |
| **Estimated for 2,000 vehicles** | **~32-35 hours** |
| Success rate | 94-98% |

### **Time Estimates:**
- **200 vehicles**: ~3-4 hours
- **500 vehicles**: ~8-9 hours
- **1,000 vehicles**: ~16-18 hours
- **2,000 vehicles**: ~32-35 hours

---

## 🔄 Resume Capability

The program automatically resumes from where it left off:

1. **If program crashes or is stopped:**
   - Restart: `python main.py`
   - Loads `checkpoint.json` and `tracking.json`
   - Skips already-downloaded PDFs
   - Continues from last position

2. **If browser gets stuck:**
   - After 5 consecutive failures
   - Automatically restarts browser
   - Re-logs in and continues

3. **If you need to stop:**
   - Press `Ctrl+C` (or close terminal)
   - Restart later with `python main.py`
   - Progress is saved after each vehicle

---

## 🛡️ Built-in Safety Features

✅ **Checkpoint System**
- Saves progress after every vehicle
- Tracks consecutive failures
- Auto-restarts browser if stuck

✅ **Retry Logic**
- 2 retries per vehicle
- 3-second delay between retries
- Closes stuck tabs automatically

✅ **Error Recovery**
- Browser restart after 5 consecutive failures
- Automatic re-login
- Returns to inventory page

✅ **Folder Management**
- Creates numbered folders for multiple runs
- Never overwrites existing data
- Reuses empty folders

✅ **Progress Tracking**
- `tracking.json` - Which PDFs are downloaded
- `checkpoint.json` - Current run state
- `metrics.json` - Performance data

---

## 📁 Output Structure

After completion, you'll have:

```
downloads/10-05-2025/
├── checkpoint.json      # Resume state
├── tracking.json        # Downloaded PDFs list
├── metrics.json         # Performance data
├── inventory.csv        # Full inventory export
├── 165549.pdf          # Vehicle PDFs (2,000 files)
├── 165550.pdf
├── ...
└── 167549.pdf
```

---

## ⚠️ Troubleshooting

### **If the program stops:**
1. Check error message in console
2. Restart: `python main.py`
3. Program will resume automatically

### **If too many failures:**
1. Check internet connection
2. Verify credentials in `.env`
3. Check JD Power site is accessible
4. Review `metrics.json` for error patterns

### **If disk space runs out:**
1. Free up space
2. Restart: `python main.py`
3. Program will skip already-downloaded PDFs

### **If session timeout:**
- Program automatically logs out and back in
- Browser restarts every 5 consecutive failures
- No manual intervention needed

---

## 📞 Monitoring the Run

### **Console Output:**
- Shows current vehicle being processed
- Progress: X/Y completed successfully
- Checkpoint status every 10 vehicles
- Final report at the end

### **Files to Monitor:**
- `checkpoint.json` - Updated after each vehicle
- `tracking.json` - Shows which PDFs exist
- Watch folder size grow: `Get-ChildItem downloads\10-05-2025\*.pdf | Measure-Object`

### **Estimated Completion:**
- Check console for "Estimated time for 2,000 PDFs"
- Updates based on actual performance
- Typically 30-35 hours for full inventory

---

## ✅ Final Checklist Before Starting

- [ ] `.env` configured with valid credentials
- [ ] Virtual environment activated
- [ ] At least 1 GB free disk space
- [ ] Stable internet connection
- [ ] Computer won't sleep
- [ ] No other instances running
- [ ] Ready to let it run for 30+ hours

### **Start Command:**
```bash
.\.venv\Scripts\python main.py
```

---

## 🎯 Success Criteria

After completion, you should see:

```
======================================================================
                    📊 FINAL RUN REPORT
======================================================================

📈 PROCESSING RESULTS
  Attempted this run  : 2000
  ✓ Succeeded         : 1950+ (97%+)
  ✗ Failed            : <50 (<3%)
  Remaining           : 0

💡 RECOMMENDATIONS
  ✓ All vehicles processed!
```

**If any vehicles failed:**
- Review error breakdown in final report
- Re-run: `python main.py`
- Program will only process failed vehicles

---

## 📝 Notes

- **First run will take longest** (needs to export CSV, build tracking)
- **Subsequent runs are faster** (resume from checkpoint)
- **Browser restarts are normal** (happens after stuck states)
- **1-second delay between vehicles** (prevents rate limiting)
- **All data is preserved** (never overwrites existing PDFs)

**Ready to go!** 🚀
