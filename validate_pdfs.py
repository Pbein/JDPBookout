"""
PDF Validation Script

This script validates that all PDFs are:
1. Named correctly (reference number matches PDF content)
2. All PDFs from tracking.json are present
3. No duplicate or misnamed PDFs

Usage:
    python validate_pdfs.py <download_folder>
    
Example:
    python validate_pdfs.py "downloads/10-05-2025 (3)"
"""
import os
import sys
import json
import re
from pathlib import Path


def extract_reference_from_pdf_content(pdf_path: str) -> str:
    """
    Extract the reference number from the PDF content.
    Uses PyPDF2 to read the PDF and find the reference number.
    
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
                
                # Look for common patterns like "Stock #: XXXXXX" or "Reference: XXXXXX"
                # The reference numbers in this system appear to be 6-digit numbers or alphanumeric
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
                
                # If no pattern match, look for any 6-digit number that might be the reference
                # This is a fallback and may not be reliable
                matches = re.findall(r'\b(\d{6}[A-Z]?)\b', text)
                if matches:
                    # Return the first one found (might not be correct)
                    return matches[0]
        
        return None
        
    except ImportError:
        print("[ERROR] PyPDF2 not installed. Install it with: pip install PyPDF2")
        return None
    except Exception as e:
        print(f"[ERROR] Could not read PDF {pdf_path}: {e}")
        return None


def validate_pdfs(download_folder: str):
    """
    Validate all PDFs in the download folder.
    
    Args:
        download_folder: Path to the folder containing PDFs and tracking.json
    """
    print("="*70)
    print("PDF VALIDATION REPORT")
    print("="*70)
    print(f"\nFolder: {download_folder}\n")
    
    # Check if folder exists
    if not os.path.exists(download_folder):
        print(f"[ERROR] Folder not found: {download_folder}")
        return
    
    # Load tracking.json
    tracking_path = os.path.join(download_folder, "tracking.json")
    if not os.path.exists(tracking_path):
        print(f"[ERROR] tracking.json not found in {download_folder}")
        return
    
    with open(tracking_path, 'r') as f:
        tracking = json.load(f)
    
    print(f"Total reference numbers in tracking.json: {len(tracking)}")
    
    # Count downloaded PDFs
    downloaded = {ref: pdf for ref, pdf in tracking.items() if pdf is not None}
    pending = {ref: pdf for ref, pdf in tracking.items() if pdf is None}
    
    print(f"Downloaded: {len(downloaded)}")
    print(f"Pending: {len(pending)}")
    print()
    
    # Get list of PDF files in folder
    pdf_files = [f for f in os.listdir(download_folder) if f.endswith('.pdf')]
    print(f"PDF files found in folder: {len(pdf_files)}")
    print()
    
    # Validation checks
    print("="*70)
    print("VALIDATION CHECKS")
    print("="*70)
    print()
    
    mismatches = []
    missing_files = []
    unexpected_files = []
    
    # Check 1: All downloaded items in tracking have corresponding files
    print("[CHECK 1] Verifying all tracked PDFs exist...")
    for ref, pdf_name in downloaded.items():
        pdf_path = os.path.join(download_folder, pdf_name)
        if not os.path.exists(pdf_path):
            missing_files.append((ref, pdf_name))
    
    if missing_files:
        print(f"  [FAIL] {len(missing_files)} tracked PDFs are missing")
        for ref, pdf_name in missing_files[:10]:  # Show first 10
            print(f"    - {ref} -> {pdf_name}")
        if len(missing_files) > 10:
            print(f"    ... and {len(missing_files) - 10} more")
    else:
        print(f"  [PASS] All {len(downloaded)} tracked PDFs exist")
    print()
    
    # Check 2: All PDF files in folder are in tracking
    print("[CHECK 2] Verifying no unexpected PDFs...")
    expected_filenames = set(downloaded.values())
    for pdf_file in pdf_files:
        if pdf_file not in expected_filenames:
            unexpected_files.append(pdf_file)
    
    if unexpected_files:
        print(f"  [WARN] {len(unexpected_files)} unexpected PDFs found")
        for pdf_file in unexpected_files[:10]:
            print(f"    - {pdf_file}")
        if len(unexpected_files) > 10:
            print(f"    ... and {len(unexpected_files) - 10} more")
    else:
        print(f"  [PASS] No unexpected PDFs")
    print()
    
    # Check 3: Sample validation - check if PDF content matches filename
    print("[CHECK 3] Validating PDF content matches filename (sample of 20)...")
    print("  This requires PyPDF2. If not installed, this check will be skipped.")
    print()
    
    try:
        import PyPDF2
        
        # Sample 20 random PDFs
        import random
        sample_refs = random.sample(list(downloaded.keys()), min(20, len(downloaded)))
        
        for ref in sample_refs:
            pdf_name = downloaded[ref]
            pdf_path = os.path.join(download_folder, pdf_name)
            
            if not os.path.exists(pdf_path):
                continue
            
            # Extract reference from filename
            filename_ref = pdf_name.replace('.pdf', '')
            
            # Extract reference from PDF content
            content_ref = extract_reference_from_pdf_content(pdf_path)
            
            if content_ref and content_ref != filename_ref:
                mismatches.append((pdf_name, filename_ref, content_ref))
                print(f"  [MISMATCH] {pdf_name}")
                print(f"    Filename says: {filename_ref}")
                print(f"    PDF contains: {content_ref}")
        
        if not mismatches:
            print(f"  [PASS] All {len(sample_refs)} sampled PDFs match their filenames")
        else:
            print(f"  [FAIL] {len(mismatches)} mismatches found in sample!")
    
    except ImportError:
        print("  [SKIP] PyPDF2 not installed - cannot validate PDF content")
        print("  Install with: pip install PyPDF2")
    
    print()
    
    # Summary
    print("="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    print()
    print(f"Total references: {len(tracking)}")
    print(f"Downloaded: {len(downloaded)}")
    print(f"Pending: {len(pending)}")
    print(f"PDF files in folder: {len(pdf_files)}")
    print()
    print(f"Missing files: {len(missing_files)}")
    print(f"Unexpected files: {len(unexpected_files)}")
    print(f"Content mismatches (sample): {len(mismatches)}")
    print()
    
    if missing_files or mismatches:
        print("[FAIL] Validation failed - issues detected!")
        print()
        if mismatches:
            print("CRITICAL: PDF content mismatches detected!")
            print("This indicates PDFs are being saved with wrong reference numbers.")
            print("This is likely a race condition in parallel processing.")
    elif unexpected_files:
        print("[WARN] Validation passed with warnings")
    else:
        print("[PASS] All validation checks passed!")
    
    print("="*70)
    
    # Save detailed report
    report_path = os.path.join(download_folder, "validation_report.json")
    report = {
        "total_references": len(tracking),
        "downloaded": len(downloaded),
        "pending": len(pending),
        "pdf_files_found": len(pdf_files),
        "missing_files": [{"ref": ref, "filename": pdf} for ref, pdf in missing_files],
        "unexpected_files": unexpected_files,
        "content_mismatches": [
            {"filename": fn, "filename_ref": fr, "content_ref": cr} 
            for fn, fr, cr in mismatches
        ]
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_pdfs.py <download_folder>")
        print()
        print("Example:")
        print('  python validate_pdfs.py "downloads/10-05-2025 (3)"')
        sys.exit(1)
    
    download_folder = sys.argv[1]
    validate_pdfs(download_folder)

