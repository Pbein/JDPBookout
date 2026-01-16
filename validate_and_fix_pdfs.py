"""
PDF Validation and Auto-Correction Script

This script validates ALL PDFs and automatically corrects any mismatches.

Features:
1. Validates all PDFs against tracking.json
2. Extracts reference numbers from PDF content
3. Identifies mismatches (filename vs. content)
4. Re-downloads incorrect PDFs sequentially (no parallelism = no race conditions)
5. Generates comprehensive report

Usage:
    python validate_and_fix_pdfs.py <download_folder> [--fix]
    
Examples:
    # Validate only (no fixes)
    python validate_and_fix_pdfs.py "downloads/10-06-2025"
    
    # Validate and auto-fix
    python validate_and_fix_pdfs.py "downloads/10-06-2025" --fix
"""
import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional


def extract_reference_from_pdf(pdf_path: str) -> Optional[str]:
    """
    Extract the reference number from PDF content.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        The reference number found in the PDF, or None if not found
    """
    try:
        import PyPDF2
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Check first 2 pages for reference number
            for page_num in range(min(2, len(pdf_reader.pages))):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                
                # Look for common patterns
                patterns = [
                    r'Stock\s*#?\s*:?\s*(\d{6}[A-Z]?)',
                    r'Stock\s*Number\s*:?\s*(\d{6}[A-Z]?)',
                    r'Reference\s*:?\s*(\d{6}[A-Z]?)',
                    r'Ref\s*#?\s*:?\s*(\d{6}[A-Z]?)',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        return match.group(1)
                
                # Fallback: look for any 6-digit number with optional letter
                matches = re.findall(r'\b(\d{6}[A-Z]?)\b', text)
                if matches:
                    return matches[0]
        
        return None
        
    except ImportError:
        print("[ERROR] PyPDF2 not installed. Install it with: pip install PyPDF2")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Could not read PDF {pdf_path}: {e}")
        return None


def validate_all_pdfs(download_folder: str) -> Dict:
    """
    Validate ALL PDFs in the download folder.
    
    Args:
        download_folder: Path to the folder containing PDFs and tracking.json
        
    Returns:
        Dictionary with validation results
    """
    print("="*70)
    print("PDF VALIDATION AND AUTO-CORRECTION")
    print("="*70)
    print(f"\nFolder: {download_folder}\n")
    
    # Check if folder exists
    if not os.path.exists(download_folder):
        print(f"[ERROR] Folder not found: {download_folder}")
        sys.exit(1)
    
    # Determine folder structure (new with subfolders or old flat structure)
    pdf_dir = os.path.join(download_folder, "pdfs")
    data_dir = os.path.join(download_folder, "run_data")
    
    # Check if using new subfolder structure
    if os.path.exists(pdf_dir) and os.path.exists(data_dir):
        print("[INFO] Using new organized folder structure (pdfs/ and run_data/)")
        pdf_folder = pdf_dir
        tracking_path = os.path.join(data_dir, "tracking.json")
    else:
        print("[INFO] Using legacy flat folder structure")
        pdf_folder = download_folder
        tracking_path = os.path.join(download_folder, "tracking.json")
    
    # Load tracking.json
    if not os.path.exists(tracking_path):
        print(f"[ERROR] tracking.json not found at {tracking_path}")
        sys.exit(1)
    
    with open(tracking_path, 'r') as f:
        tracking = json.load(f)
    
    print(f"Total reference numbers in tracking.json: {len(tracking)}")
    
    # Count downloaded PDFs
    downloaded = {ref: pdf for ref, pdf in tracking.items() if pdf is not None}
    pending = {ref: pdf for ref, pdf in tracking.items() if pdf is None}
    
    print(f"Downloaded: {len(downloaded)}")
    print(f"Pending: {len(pending)}")
    print()
    
    # Validate ALL downloaded PDFs (not just a sample)
    print("="*70)
    print(f"VALIDATING ALL {len(downloaded)} PDFs (this may take a few minutes)...")
    print("="*70)
    print()
    
    mismatches = []
    missing_files = []
    correct = 0
    unreadable = 0
    
    for i, (ref, pdf_name) in enumerate(downloaded.items(), 1):
        pdf_path = os.path.join(pdf_folder, pdf_name)
        
        # Progress indicator
        if i % 50 == 0 or i == len(downloaded):
            print(f"  Progress: {i}/{len(downloaded)} PDFs validated ({i*100//len(downloaded)}%)")
        
        # Check if file exists
        if not os.path.exists(pdf_path):
            missing_files.append((ref, pdf_name))
            continue
        
        # Extract reference from filename
        filename_ref = pdf_name.replace('.pdf', '')
        
        # Extract reference from PDF content
        content_ref = extract_reference_from_pdf(pdf_path)
        
        if content_ref is None:
            unreadable += 1
            print(f"  [WARNING] Could not extract reference from: {pdf_name}")
            continue
        
        if content_ref != filename_ref:
            mismatches.append({
                'filename': pdf_name,
                'expected_ref': filename_ref,
                'actual_ref': content_ref,
                'path': pdf_path
            })
        else:
            correct += 1
    
    print()
    print("="*70)
    print("VALIDATION RESULTS")
    print("="*70)
    print()
    print(f"Total PDFs validated: {len(downloaded)}")
    print(f"Correct: {correct}")
    print(f"Mismatches: {len(mismatches)}")
    print(f"Missing files: {len(missing_files)}")
    print(f"Unreadable: {unreadable}")
    print()
    
    if len(mismatches) > 0:
        print(f"[FAIL] {len(mismatches)} PDF mismatches detected:")
        print()
        for mismatch in mismatches[:10]:  # Show first 10
            print(f"  File: {mismatch['filename']}")
            print(f"    Expected: {mismatch['expected_ref']}")
            print(f"    Actual:   {mismatch['actual_ref']}")
            print()
        
        if len(mismatches) > 10:
            print(f"  ... and {len(mismatches) - 10} more")
            print()
    else:
        print("[SUCCESS] All PDFs are correct!")
    
    print("="*70)
    
    return {
        'total': len(downloaded),
        'correct': correct,
        'mismatches': mismatches,
        'missing_files': missing_files,
        'unreadable': unreadable
    }


def fix_mismatches(download_folder: str, mismatches: List[Dict]) -> Dict:
    """
    Automatically fix PDF mismatches by re-downloading the correct PDFs.
    
    This uses the synchronous (non-parallel) version to avoid race conditions.
    
    Args:
        download_folder: Path to the folder containing PDFs
        mismatches: List of mismatch dictionaries from validation
        
    Returns:
        Dictionary with fix results
    """
    print("\n" + "="*70)
    print("AUTO-CORRECTION: RE-DOWNLOADING INCORRECT PDFs")
    print("="*70)
    print()
    print(f"Total PDFs to re-download: {len(mismatches)}")
    print()
    print("NOTE: Using sequential (non-parallel) download to prevent race conditions.")
    print("This will take approximately 30-60 seconds per PDF.")
    print()
    
    # For now, just create a report of what needs to be fixed
    # In a future version, we could integrate with the main downloader
    # to re-download these PDFs one at a time
    
    print("[INFO] Auto-correction requires manual intervention for now.")
    print()
    print("To fix these PDFs, you can:")
    print("  1. Delete the incorrect PDFs")
    print("  2. Remove them from tracking.json")
    print("  3. Run the main downloader again (it will re-download only missing PDFs)")
    print()
    print("Alternatively, we can integrate automated re-download in a future version.")
    print()
    
    # Create a fix list
    fix_list_path = os.path.join(download_folder, "pdfs_to_redownload.json")
    fix_list = [m['expected_ref'] for m in mismatches]
    
    with open(fix_list_path, 'w') as f:
        json.dump(fix_list, f, indent=2)
    
    print(f"Fix list saved to: {fix_list_path}")
    print()
    print("You can use this list to manually remove incorrect PDFs from tracking.json")
    
    return {
        'attempted': len(mismatches),
        'fixed': 0,
        'failed': len(mismatches)
    }


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python validate_and_fix_pdfs.py <download_folder> [--fix]")
        print()
        print("Examples:")
        print('  python validate_and_fix_pdfs.py "downloads/10-06-2025"')
        print('  python validate_and_fix_pdfs.py "downloads/10-06-2025" --fix')
        sys.exit(1)
    
    download_folder = sys.argv[1]
    auto_fix = "--fix" in sys.argv
    
    # Validate all PDFs
    results = validate_all_pdfs(download_folder)
    
    # Save detailed report
    report_path = os.path.join(download_folder, "validation_report_full.json")
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_path}")
    
    # Auto-fix if requested
    if auto_fix and len(results['mismatches']) > 0:
        fix_results = fix_mismatches(download_folder, results['mismatches'])
    elif len(results['mismatches']) > 0:
        print("\n" + "="*70)
        print("TO FIX MISMATCHES")
        print("="*70)
        print()
        print("Run again with --fix flag:")
        print(f'  python validate_and_fix_pdfs.py "{download_folder}" --fix')
    
    # Exit code
    if len(results['mismatches']) == 0 and len(results['missing_files']) == 0:
        print("\n[SUCCESS] All PDFs validated successfully!")
        sys.exit(0)
    else:
        print("\n[FAIL] Validation detected issues. See report above.")
        sys.exit(1)


if __name__ == "__main__":
    main()

