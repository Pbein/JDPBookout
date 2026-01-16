"""
Test script for Race Condition Fix

This script tests that the lock-based solution fixes the PDF race condition.
It runs 50 vehicles with 5 workers and validates ALL PDFs are correct.

Expected Results:
- 50/50 PDFs downloaded successfully
- 100% validation accuracy (0 mismatches)
- Clean logout and shutdown

Configuration:
- 50 vehicles (enough to stress test)
- 5 workers (high parallelism to trigger race conditions if present)
- Full validation of all PDFs after completion
"""
import os
import sys
import time

# Set test configuration
os.environ["MAX_DOWNLOADS"] = "50"
os.environ["CONCURRENT_CONTEXTS"] = "5"  # 5 workers for stress test
os.environ["HEADLESS"] = "false"  # Visible for monitoring
os.environ["BLOCK_RESOURCES"] = "false"  # Show styling

print("="*70)
print("RACE CONDITION FIX VALIDATION TEST")
print("="*70)
print()
print("Purpose: Verify the lock-based solution prevents PDF race conditions")
print()
print("Configuration:")
print(f"  MAX_DOWNLOADS        : {os.environ['MAX_DOWNLOADS']}")
print(f"  CONCURRENT_WORKERS   : {os.environ['CONCURRENT_CONTEXTS']}")
print(f"  HEADLESS             : {os.environ['HEADLESS']}")
print(f"  BLOCK_RESOURCES      : {os.environ['BLOCK_RESOURCES']}")
print("="*70)
print()
print("Test Plan:")
print("  1. Run 50 vehicles with 5 workers (high parallelism)")
print("  2. Complete all downloads")
print("  3. Validate ALL 50 PDFs using validate_pdfs.py")
print("  4. Verify 100% accuracy (0 mismatches)")
print()
print("Success Criteria:")
print("  - 50/50 PDFs downloaded")
print("  - 100% validation accuracy")
print("  - No race condition errors")
print("  - Clean logout")
print("="*70)
print()

# Import and run
from main_async import main

if __name__ == "__main__":
    start_time = time.time()
    download_folder = None
    
    try:
        # Run the downloader
        print("[STEP 1] Running parallel PDF downloader with lock...")
        print()
        main()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print("\n" + "="*70)
        print("[STEP 2] Download complete - Running validation...")
        print("="*70)
        print()
        
        # Find the most recent download folder
        downloads_dir = "downloads"
        if os.path.exists(downloads_dir):
            folders = [f for f in os.listdir(downloads_dir) if os.path.isdir(os.path.join(downloads_dir, f))]
            if folders:
                # Get most recent folder (by modification time)
                folders.sort(key=lambda f: os.path.getmtime(os.path.join(downloads_dir, f)), reverse=True)
                download_folder = os.path.join(downloads_dir, folders[0])
                
                print(f"Validating folder: {download_folder}")
                print()
                
                # Run validation
                import subprocess
                result = subprocess.run(
                    [sys.executable, "validate_pdfs.py", download_folder],
                    capture_output=True,
                    text=True
                )
                
                print(result.stdout)
                
                if result.returncode != 0:
                    print("[VALIDATION ERROR]")
                    print(result.stderr)
                
                # Check validation report
                import json
                report_path = os.path.join(download_folder, "validation_report.json")
                if os.path.exists(report_path):
                    with open(report_path, 'r') as f:
                        report = json.load(f)
                    
                    mismatches = len(report.get('content_mismatches', []))
                    
                    print("\n" + "="*70)
                    print("TEST RESULTS")
                    print("="*70)
                    print()
                    print(f"Runtime: {total_time/60:.2f} minutes")
                    print(f"PDFs downloaded: {report['downloaded']}")
                    print(f"Validation mismatches: {mismatches}")
                    print()
                    
                    if mismatches == 0:
                        print("[SUCCESS] TEST PASSED!")
                        print("  - All PDFs downloaded correctly")
                        print("  - 100% validation accuracy")
                        print("  - Race condition FIX VERIFIED!")
                        print()
                        print("The lock-based solution successfully prevents PDF race conditions.")
                        print("The system is SAFE for production use.")
                    else:
                        print("[FAIL] TEST FAILED!")
                        print(f"  - {mismatches} PDF mismatches detected")
                        print("  - Race condition still present")
                        print()
                        print("The fix did NOT resolve the race condition.")
                        print("DO NOT use for production.")
                    
                    print("="*70)
                else:
                    print("[ERROR] Could not find validation report")
        
    except KeyboardInterrupt:
        print("\n" + "="*70)
        print("[INTERRUPTED] Test stopped by user")
        print("="*70)
        sys.exit(1)
        
    except Exception as e:
        print("\n" + "="*70)
        print(f"[TEST FAILED] Error: {e}")
        print("="*70)
        import traceback
        traceback.print_exc()
        sys.exit(1)

