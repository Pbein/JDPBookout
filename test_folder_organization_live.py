"""
Live test of folder organization with actual PDF downloads.

This will:
1. Download 3 PDFs using the async system
2. Verify files are in correct subfolders
3. Run validation to ensure everything works
"""
import os
import sys

# Set test configuration
os.environ["MAX_DOWNLOADS"] = "3"
os.environ["CONCURRENT_CONTEXTS"] = "2"
os.environ["HEADLESS"] = "false"
os.environ["BLOCK_RESOURCES"] = "false"

print("="*70)
print("FOLDER ORGANIZATION - LIVE TEST")
print("="*70)
print()
print("Configuration:")
print("  Vehicles: 3")
print("  Workers: 2")
print("  Headless: false")
print()
print("This test will:")
print("  1. Download 3 PDFs")
print("  2. Verify folder structure (pdfs/ and run_data/)")
print("  3. Verify files are in correct locations")
print("  4. Run validation script")
print()
print("="*70)
print()

# Import config to see paths
from jdp_scraper import config

print("Expected folder structure:")
print(f"  RUN_DIR:  {config.RUN_DIR}")
print(f"  PDF_DIR:  {config.PDF_DIR}")
print(f"  DATA_DIR: {config.DATA_DIR}")
print()
print("="*70)
print()

# Run the downloader
print("[STEP 1] Running PDF downloader...")
print()

from main_async import main

try:
    main()
    
    print()
    print("="*70)
    print("[STEP 2] Verifying folder structure...")
    print("="*70)
    print()
    
    # Check folders exist
    pdf_dir_exists = os.path.exists(config.PDF_DIR)
    data_dir_exists = os.path.exists(config.DATA_DIR)
    
    print(f"PDF folder exists: {pdf_dir_exists}")
    print(f"Data folder exists: {data_dir_exists}")
    print()
    
    if not pdf_dir_exists or not data_dir_exists:
        print("[FAIL] Required folders do not exist!")
        sys.exit(1)
    
    # Check for PDFs in pdfs/
    pdf_files = [f for f in os.listdir(config.PDF_DIR) if f.endswith('.pdf')]
    print(f"PDFs in pdfs/ folder: {len(pdf_files)}")
    for pdf in pdf_files:
        print(f"  - {pdf}")
    print()
    
    # Check for data files in run_data/
    data_files = os.listdir(config.DATA_DIR)
    print(f"Files in run_data/ folder: {len(data_files)}")
    for file in data_files:
        print(f"  - {file}")
    print()
    
    # Verify expected files
    expected_data_files = ['tracking.json', 'checkpoint.json', 'metrics.json', 'inventory.csv']
    missing_data = [f for f in expected_data_files if f not in data_files]
    
    if missing_data:
        print(f"[WARNING] Missing expected data files: {missing_data}")
    else:
        print("[SUCCESS] All expected data files present!")
    print()
    
    # Verify no PDFs in root
    root_pdfs = [f for f in os.listdir(config.RUN_DIR) if f.endswith('.pdf')]
    if root_pdfs:
        print(f"[WARNING] Found {len(root_pdfs)} PDFs in root folder (should be in pdfs/)")
    else:
        print("[SUCCESS] No PDFs in root folder (correct!)")
    print()
    
    print("="*70)
    print("[STEP 3] Running validation...")
    print("="*70)
    print()
    
    # Run validation
    import subprocess
    result = subprocess.run(
        [sys.executable, "validate_pdfs.py", config.RUN_DIR],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    
    if result.returncode == 0:
        print()
        print("="*70)
        print("[SUCCESS] All tests passed!")
        print("="*70)
        print()
        print("Folder organization is working correctly:")
        print(f"  {config.RUN_DIR}/")
        print(f"    |-- pdfs/       ({len(pdf_files)} PDFs)")
        print(f"    +-- run_data/   ({len(data_files)} files)")
        print()
    else:
        print()
        print("="*70)
        print("[FAIL] Validation failed")
        print("="*70)
        sys.exit(1)
        
except KeyboardInterrupt:
    print()
    print("[INTERRUPTED] Test stopped by user")
    sys.exit(1)
    
except Exception as e:
    print()
    print("="*70)
    print(f"[ERROR] Test failed: {e}")
    print("="*70)
    import traceback
    traceback.print_exc()
    sys.exit(1)

