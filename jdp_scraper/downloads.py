"""Download folder and tracking for reference numbers and PDFs.

Responsibilities:
- Read CSV and extract reference numbers
- Track processed reference numbers (which have PDFs downloaded)
- Resolve PDF save path as <ReferenceNumber>.pdf
- Check if PDF already exists for a reference number
"""
import os
import csv
import json
from typing import Dict, List, Optional
from jdp_scraper import config


def read_reference_numbers_from_csv(csv_path: str) -> List[str]:
    """
    Read the inventory CSV and extract all reference numbers.
    
    Args:
        csv_path: Path to the inventory CSV file
        
    Returns:
        List of reference numbers
    """
    try:
        reference_numbers = []
        
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                ref_num = row.get('Reference Number', '').strip()
                if ref_num:
                    reference_numbers.append(ref_num)
        
        print(f"[SUCCESS] Extracted {len(reference_numbers)} reference numbers from CSV")
        return reference_numbers
        
    except Exception as e:
        print(f"[ERROR] Failed to read CSV: {e}")
        return []


def get_pdf_path(reference_number: str, directory: str = None) -> str:
    """
    Get the full path for a PDF file based on reference number.
    
    Args:
        reference_number: The reference number
        directory: Directory to save PDF (default: from config.PDF_DIR)
        
    Returns:
        Full path to the PDF file
    """
    if directory is None:
        directory = config.PDF_DIR()
    
    return os.path.join(directory, f"{reference_number}.pdf")


def check_pdf_exists(reference_number: str, directory: str = None) -> bool:
    """
    Check if a PDF already exists for a reference number.
    
    Args:
        reference_number: The reference number
        directory: Directory to check (default: from config.PDF_DIR)
        
    Returns:
        True if PDF exists, False otherwise
    """
    pdf_path = get_pdf_path(reference_number, directory)
    return os.path.exists(pdf_path)


def build_reference_tracking(csv_path: str, directory: str = None) -> Dict[str, Optional[str]]:
    """
    Build a tracking dictionary of reference numbers and their PDF status.
    
    Args:
        csv_path: Path to the inventory CSV file
        directory: Directory to check for PDFs (default: from config.PDF_DIR)
        
    Returns:
        Dictionary mapping reference_number -> pdf_filename (or None if not downloaded)
    """
    try:
        if directory is None:
            directory = config.PDF_DIR()
        
        # Read all reference numbers from CSV
        reference_numbers = read_reference_numbers_from_csv(csv_path)
        
        # Build tracking dictionary
        tracking = {}
        downloaded_count = 0
        
        for ref_num in reference_numbers:
            if check_pdf_exists(ref_num, directory):
                tracking[ref_num] = f"{ref_num}.pdf"
                downloaded_count += 1
            else:
                tracking[ref_num] = None
        
        print(f"\n=== Reference Tracking Summary ===")
        print(f"Total reference numbers: {len(reference_numbers)}")
        print(f"Already downloaded: {downloaded_count}")
        print(f"Need to download: {len(reference_numbers) - downloaded_count}")
        print(f"==================================\n")
        
        return tracking
        
    except Exception as e:
        print(f"[ERROR] Failed to build tracking: {e}")
        return {}


def save_tracking_to_json(tracking: Dict[str, Optional[str]], directory: str = None) -> str:
    """
    Save the tracking dictionary to a JSON file for resume capability.
    
    Args:
        tracking: Dictionary of reference numbers and PDF status
        directory: Directory to save the JSON (default: from config.RUN_DIR)
        
    Returns:
        Path to the saved JSON file
    """
    try:
        if directory is None:
            directory = config.DATA_DIR()  # Use DATA_DIR for JSON files
        
        os.makedirs(directory, exist_ok=True)
        json_path = os.path.join(directory, "tracking.json")
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(tracking, f, indent=2)
        
        print(f"[SUCCESS] Tracking saved to: {json_path}")
        return json_path
        
    except Exception as e:
        print(f"[ERROR] Failed to save tracking: {e}")
        return ""


def load_tracking_from_json(directory: str = None) -> Dict[str, Optional[str]]:
    """
    Load tracking dictionary from JSON file if it exists.
    
    Args:
        directory: Directory to load the JSON from (default: from config.RUN_DIR)
        
    Returns:
        Dictionary of reference numbers and PDF status, or empty dict if not found
    """
    try:
        if directory is None:
            directory = config.DATA_DIR()  # Use DATA_DIR for JSON files
        
        json_path = os.path.join(directory, "tracking.json")
        
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                tracking = json.load(f)
            print(f"[SUCCESS] Loaded tracking from: {json_path}")
            return tracking
        else:
            print("No existing tracking file found. Will create new one.")
            return {}
            
    except Exception as e:
        print(f"[ERROR] Failed to load tracking: {e}")
        return {}


def update_tracking(tracking: Dict[str, Optional[str]], reference_number: str, pdf_filename: str, directory: str = None) -> bool:
    """
    Update tracking for a reference number and save to JSON.
    
    Args:
        tracking: Tracking dictionary
        reference_number: Reference number that was processed
        pdf_filename: Name of the PDF file (e.g., "165199.pdf")
        directory: Directory to save JSON (default: from config.RUN_DIR)
        
    Returns:
        True if updated successfully, False otherwise
    """
    try:
        # Update the tracking dict
        tracking[reference_number] = pdf_filename
        
        # Save to JSON
        save_tracking_to_json(tracking, directory)
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to update tracking: {e}")
        return False

