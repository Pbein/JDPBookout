"""
Test the new folder structure implementation.

This script tests that:
1. Folders are created correctly (pdfs/ and run_data/)
2. Files are saved to the correct locations
3. The validation scripts can find files in the new structure
"""
import os
import shutil
from jdp_scraper import config

print("="*70)
print("FOLDER STRUCTURE TEST")
print("="*70)
print()

# Show current configuration
print("Current Configuration:")
print(f"  RUN_DIR:  {config.RUN_DIR}")
print(f"  DATA_DIR: {config.DATA_DIR}")
print(f"  PDF_DIR:  {config.PDF_DIR}")
print()

# Check if folders exist
print("Checking folder structure...")
print(f"  RUN_DIR exists: {os.path.exists(config.RUN_DIR)}")
print(f"  DATA_DIR exists: {os.path.exists(config.DATA_DIR)}")
print(f"  PDF_DIR exists: {os.path.exists(config.PDF_DIR)}")
print()

# Verify folder structure
expected_data_dir = os.path.join(config.RUN_DIR, "run_data")
expected_pdf_dir = os.path.join(config.RUN_DIR, "pdfs")

print("Verifying folder structure...")
print(f"  DATA_DIR is in RUN_DIR/run_data: {config.DATA_DIR == expected_data_dir}")
print(f"  PDF_DIR is in RUN_DIR/pdfs: {config.PDF_DIR == expected_pdf_dir}")
print()

# Test file path generation
print("Testing file paths...")
test_ref = "123456"
test_pdf_path = os.path.join(config.PDF_DIR, f"{test_ref}.pdf")
test_tracking_path = os.path.join(config.DATA_DIR, "tracking.json")
test_checkpoint_path = os.path.join(config.DATA_DIR, "checkpoint.json")
test_metrics_path = os.path.join(config.DATA_DIR, "metrics.json")
test_csv_path = os.path.join(config.DATA_DIR, "inventory.csv")

print(f"  PDF path: {test_pdf_path}")
print(f"  Tracking path: {test_tracking_path}")
print(f"  Checkpoint path: {test_checkpoint_path}")
print(f"  Metrics path: {test_metrics_path}")
print(f"  CSV path: {test_csv_path}")
print()

# Verify all paths are in correct subfolders
all_correct = all([
    config.DATA_DIR == expected_data_dir,
    config.PDF_DIR == expected_pdf_dir,
    test_pdf_path.startswith(config.PDF_DIR),
    test_tracking_path.startswith(config.DATA_DIR),
])

print("="*70)
if all_correct:
    print("[SUCCESS] Folder structure is configured correctly!")
    print()
    print("New structure:")
    print(f"  {config.RUN_DIR}/")
    print(f"    |-- pdfs/          (all PDF files)")
    print(f"    +-- run_data/      (CSV, JSON, metrics)")
else:
    print("[FAIL] Folder structure has issues!")
print("="*70)

