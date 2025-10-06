"""
Quick test to verify PDF reference number extraction accuracy.
"""
import sys
import re
from PyPDF2 import PdfReader


def extract_reference_from_pdf(pdf_path: str):
    """Extract reference number from PDF and show details."""
    print(f"\n{'='*70}")
    print(f"Testing: {pdf_path}")
    print('='*70)
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PdfReader(file)
            
            print(f"Total pages: {len(pdf_reader.pages)}")
            print()
            
            # Check first 2 pages
            for page_num in range(min(2, len(pdf_reader.pages))):
                print(f"--- Page {page_num + 1} ---")
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                
                # Show first 500 characters of text
                print("First 500 characters of extracted text:")
                print(text[:500])
                print()
                
                # Try different patterns
                patterns = [
                    (r'Stock\s*#?\s*:?\s*(\d{6}[A-Z]?)', 'Stock # pattern'),
                    (r'Stock\s*Number\s*:?\s*(\d{6}[A-Z]?)', 'Stock Number pattern'),
                    (r'Reference\s*:?\s*(\d{6}[A-Z]?)', 'Reference pattern'),
                    (r'Ref\s*#?\s*:?\s*(\d{6}[A-Z]?)', 'Ref # pattern'),
                ]
                
                print("Pattern matching attempts:")
                for pattern, name in patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        print(f"  [MATCH] {name}: Found '{match.group(1)}'")
                    else:
                        print(f"  [NO MATCH] {name}: No match")
                
                print()
                
                # Fallback: all 6-digit numbers with optional letter
                matches = re.findall(r'\b(\d{6}[A-Z]?)\b', text)
                if matches:
                    print(f"All 6-digit numbers found on page {page_num + 1}:")
                    for i, match in enumerate(matches[:10], 1):  # Show first 10
                        print(f"  {i}. {match}")
                    if len(matches) > 10:
                        print(f"  ... and {len(matches) - 10} more")
                else:
                    print("No 6-digit numbers found")
                print()
            
            # Final determination
            print("="*70)
            print("FINAL DETERMINATION:")
            print("="*70)
            
            for page_num in range(min(2, len(pdf_reader.pages))):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                
                # Try patterns in order
                for pattern, name in patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        result = match.group(1)
                        print(f"[SUCCESS] Extracted Reference Number: {result}")
                        print(f"  Method: {name}")
                        print(f"  Page: {page_num + 1}")
                        return result
                
                # Fallback
                matches = re.findall(r'\b(\d{6}[A-Z]?)\b', text)
                if matches:
                    result = matches[0]
                    print(f"[SUCCESS] Extracted Reference Number: {result}")
                    print(f"  Method: Fallback (first 6-digit number)")
                    print(f"  Page: {page_num + 1}")
                    return result
            
            print("[FAILED] Could not extract reference number")
            return None
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Test specific files
    test_files = [
        "downloads/10-06-2025 (2)/165614.pdf",
        "downloads/10-06-2025 (2)/165574.pdf",
    ]
    
    print("="*70)
    print("PDF REFERENCE NUMBER EXTRACTION TEST")
    print("="*70)
    print()
    print("Testing the validation script's ability to extract reference numbers")
    print("from PDF content and compare against filenames.")
    print()
    
    results = {}
    
    for pdf_path in test_files:
        filename = pdf_path.split('/')[-1]
        expected_ref = filename.replace('.pdf', '')
        
        extracted_ref = extract_reference_from_pdf(pdf_path)
        
        if extracted_ref:
            match = extracted_ref == expected_ref
            results[filename] = {
                'expected': expected_ref,
                'extracted': extracted_ref,
                'match': match
            }
        else:
            results[filename] = {
                'expected': expected_ref,
                'extracted': None,
                'match': False
            }
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print()
    
    for filename, result in results.items():
        print(f"File: {filename}")
        print(f"  Expected:  {result['expected']}")
        print(f"  Extracted: {result['extracted']}")
        print(f"  Match:     {'[YES]' if result['match'] else '[NO]'}")
        print()
    
    # Final verdict
    all_match = all(r['match'] for r in results.values())
    
    if all_match:
        print("="*70)
        print("[SUCCESS] All PDFs extracted correctly!")
        print("="*70)
        print()
        print("The validation script is working accurately.")
        print("It can reliably detect mismatches if they occur.")
    else:
        print("="*70)
        print("[ISSUE] Some PDFs did not extract correctly")
        print("="*70)
        print()
        print("The validation script may need adjustment.")

