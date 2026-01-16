# Production Run Guide

**Date:** 2025-10-05  
**Status:** Ready for Production  
**Expected Runtime:** 6-8 hours for 1,820 vehicles

---

## 🎯 **Quick Start**

### **For Full Production Run (1,820 vehicles):**

```bash
# 1. Activate virtual environment
.\.venv\Scripts\activate

# 2. Set production configuration in .env:
MAX_DOWNLOADS=9999
CONCURRENT_CONTEXTS=7
HEADLESS=true
BLOCK_RESOURCES=true

# 3. Run the production script
.\.venv\Scripts\python main_async.py
```

---

## ⚙️ **Configuration Guide**

### **Worker Count Recommendations**

| Scenario | Workers | Expected Time | Memory Usage | Risk Level |
|----------|---------|---------------|--------------|------------|
| **Conservative** | 3-5 | 8-10 hours | ~300-500MB | ✅ Low |
| **Recommended** | 7 | 6-7 hours | ~600-700MB | ✅ Low-Medium |
| **Aggressive** | 10 | 5-6 hours | ~800MB-1GB | ⚠️ Medium |
| **Maximum** | 12+ | 4-5 hours | >1GB | ❌ High (not recommended) |

### **Optimal Configuration (Recommended):**
```env
MAX_DOWNLOADS=9999           # Process all vehicles
CONCURRENT_CONTEXTS=7        # 7 workers (optimal balance)
HEADLESS=true                # No visible browser (faster)
BLOCK_RESOURCES=true         # Block CSS/images (30-50% faster)
```

### **Conservative Configuration (Most Stable):**
```env
MAX_DOWNLOADS=9999
CONCURRENT_CONTEXTS=5        # 5 workers (proven stable)
HEADLESS=true
BLOCK_RESOURCES=true
```

### **Testing Configuration:**
```env
MAX_DOWNLOADS=30
CONCURRENT_CONTEXTS=5
HEADLESS=false               # Visible for monitoring
BLOCK_RESOURCES=false        # Show styling for debugging
```

---

## 📊 **Performance Projections**

### **Based on Test Results:**
- **Average time per vehicle:** 21.75 seconds (with 2 workers)
- **With 7 workers:** ~12-15 seconds per vehicle (estimated)
- **Total for 1,820 vehicles:** ~6-7 hours

### **Throughput Estimates:**

| Workers | Time/Vehicle | Total Time | Vehicles/Hour |
|---------|--------------|------------|---------------|
| 2       | 22s          | 11.1h      | 165/h         |
| 5       | 15s          | 7.6h       | 240/h         |
| 7       | 12s          | 6.1h       | 300/h         |
| 10      | 10s          | 5.1h       | 360/h         |

---

## 🔍 **Monitoring During Production Run**

### **What to Watch:**

1. **Console Output:**
   - Worker progress messages
   - Watchdog status updates (every minute)
   - Task queue statistics
   - Error messages

2. **System Resources:**
   - Memory usage (should stay < 1GB)
   - CPU usage (should be low, mostly I/O wait)
   - Network activity (steady downloads)

3. **Download Folder:**
   - PDFs appearing in real-time
   - File sizes (should be 40-70KB each)
   - Correct naming (reference_number.pdf)

4. **Tracking Files:**
   - `tracking.json` - Updated after each PDF
   - `checkpoint.json` - Progress and success rate
   - `metrics.json` - Performance data

### **Progress Updates:**

The watchdog prints progress every minute:
```
[WATCHDOG] Progress: 150/1820 completed (98.7% success rate)
```

---

## 🛡️ **Robustness Features**

### **Automatic Recovery:**
- ✅ **Per-vehicle retry** (up to 2 attempts)
- ✅ **Timeout handling** (3 minutes per vehicle)
- ✅ **Stuck task recovery** (watchdog monitors)
- ✅ **Page recovery** (automatic navigation back to inventory)
- ✅ **Resume capability** (can stop and restart)

### **Checkpoint System:**
- Saves progress after each vehicle
- Tracks consecutive failures
- Enables safe restart from last position

### **Watchdog Monitor:**
- Checks for stuck tasks every minute
- Recovers tasks stuck > 5 minutes
- Reports progress regularly

---

## 🚨 **What to Do If Issues Occur**

### **Issue: High Failure Rate (>10%)**
**Solution:**
1. Stop the program (Ctrl+C)
2. Reduce worker count in `.env` (e.g., from 7 to 5)
3. Restart: `.\.venv\Scripts\python main_async.py`
4. Program will resume from checkpoint

### **Issue: Memory Usage Too High (>1.5GB)**
**Solution:**
1. Stop the program
2. Reduce workers to 5 or fewer
3. Set `BLOCK_RESOURCES=true` if not already
4. Restart

### **Issue: Stuck/Frozen**
**Solution:**
1. Wait 5 minutes - watchdog may recover automatically
2. If still stuck, press Ctrl+C to stop
3. Check `checkpoint.json` for last successful vehicle
4. Restart - will resume automatically

### **Issue: Wrong PDFs Downloaded**
**This should NOT happen with the current implementation!**
- Task queue prevents page interference
- If it does occur, report as a bug

---

## 📝 **Pre-Flight Checklist**

Before starting production run:

- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Playwright browsers installed (`playwright install chromium`)
- [ ] `.env` file configured with production settings
- [ ] Sufficient disk space (>2GB for 1,820 PDFs)
- [ ] Stable internet connection
- [ ] System has adequate memory (>2GB free)
- [ ] No other resource-intensive programs running
- [ ] Backup of existing downloads (if any)

---

## 🎯 **Expected Results**

### **Success Criteria:**
- ✅ 1,640+ PDFs downloaded (90%+ success rate)
- ✅ All PDFs named correctly (reference_number.pdf)
- ✅ No duplicate downloads
- ✅ Complete in 6-8 hours
- ✅ Clean shutdown with final report

### **Final Report Will Show:**
- Total runtime
- Success/failure counts
- Average time per vehicle
- Performance metrics
- Checkpoint status
- Recommendations

---

## 🔄 **Resuming After Interruption**

If the program is stopped (Ctrl+C, crash, or system issue):

1. **Check checkpoint status:**
   ```bash
   # Look at checkpoint.json
   cat downloads/[DATE]/checkpoint.json
   ```

2. **Simply restart:**
   ```bash
   .\.venv\Scripts\python main_async.py
   ```

3. **The program will:**
   - Load `tracking.json`
   - Skip already-downloaded PDFs
   - Continue from where it left off
   - Maintain all statistics

---

## 📈 **Post-Run Analysis**

After completion, review:

1. **`metrics.json`** - Detailed performance data
2. **`checkpoint.json`** - Final success rate and statistics
3. **`tracking.json`** - Which PDFs were downloaded
4. **Console output** - Final report with recommendations

### **Verify Results:**
```bash
# Count downloaded PDFs
ls downloads/[DATE]/*.pdf | wc -l

# Should be close to 1,820 (90%+ success rate)
```

---

## 🚀 **Optimization Tips**

### **For Maximum Speed:**
1. Set `CONCURRENT_CONTEXTS=10` (if system can handle it)
2. Set `HEADLESS=true` (no visual overhead)
3. Set `BLOCK_RESOURCES=true` (30-50% faster)
4. Close other programs
5. Use wired internet connection (not WiFi)

### **For Maximum Stability:**
1. Set `CONCURRENT_CONTEXTS=5` (proven stable)
2. Set `HEADLESS=true`
3. Set `BLOCK_RESOURCES=true`
4. Run overnight when system is idle
5. Monitor first 30 minutes to ensure stability

---

## 📞 **Support**

### **Common Questions:**

**Q: Can I run multiple times per day?**  
A: Yes! The system automatically creates numbered folders (e.g., `10-05-2025 (2)`)

**Q: What if I need to stop mid-run?**  
A: Press Ctrl+C. The program will save progress and you can resume later.

**Q: How do I know if it's working?**  
A: Watch for PDFs appearing in the download folder and console progress messages.

**Q: What's the best worker count?**  
A: **7 workers** for optimal balance of speed and stability.

---

**Ready to run!** 🚀

**Recommended command:**
```bash
.\.venv\Scripts\python main_async.py
```

**For testing first:**
```bash
.\.venv\Scripts\python test_parallel_30.py
```
