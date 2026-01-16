"""Configuration: URLs, flags, timeouts, retries.

Environment:
- JD_USER, JD_PASS, HEADLESS from .env
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# URLs
BASE_URL = "https://extapps.jdpowervalues.com/ValuesOnline/Home/LicenseAgreement?ReturnUrl=/ValuesOnline/"
LOGIN_URL = BASE_URL  # Login is on the same page
INVENTORY_URL = "https://extapps.jdpowervalues.com/ValuesOnline/vehicle/"

# Credentials from environment
JD_USER = os.getenv("JD_USER", "")
JD_PASS = os.getenv("JD_PASS", "")

# Browser settings
HEADLESS = os.getenv("HEADLESS", "false").lower() in ("true", "1", "yes")
BLOCK_RESOURCES = os.getenv("BLOCK_RESOURCES", "true").lower() in ("true", "1", "yes")  # Block CSS/images for speed

# Batch processing settings
MAX_DOWNLOADS_PER_RUN = int(os.getenv("MAX_DOWNLOADS", "9999"))  # Default: process all pending

# Timeouts (in milliseconds for Playwright)
DEFAULT_TIMEOUT = 30000  # 30 seconds
NAVIGATION_TIMEOUT = 90000  # 90 seconds
DOWNLOAD_TIMEOUT = 120000  # 2 minutes

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Download directory naming
from datetime import datetime

# Cache for run directory to prevent multiple numbered folders
_run_directory_cache = None

def reset_run_directory_cache():
    """Reset the run directory cache to force re-evaluation."""
    global _run_directory_cache
    _run_directory_cache = None

def get_run_directory():
    """
    Get the run directory for today, creating a numbered folder if needed.
    
    Format: {DOWNLOAD_BASE}/MM-DD-YYYY or {DOWNLOAD_BASE}/MM-DD-YYYY (2), etc.
    
    Returns:
        str: Path to the run directory
    """
    global _run_directory_cache
    
    # Return cached directory if available
    if _run_directory_cache is not None:
        return _run_directory_cache
    
    # Get download base folder from environment variable, default to 'downloads'
    download_base = os.getenv("DOWNLOAD_FOLDER", "downloads")
    print(f"[CONFIG] Using DOWNLOAD_FOLDER: '{download_base}'")
    
    base_date = datetime.now().strftime('%m-%d-%Y')
    base_path = f"{download_base}/{base_date}"
    
    # Check if base path exists and has content
    if not os.path.exists(base_path):
        # First run of the day
        _run_directory_cache = base_path
        return base_path
    
    # Check if there are any PDFs or tracking.json in the base path
    # (Check both old structure and new subfolder structure)
    has_content = False
    if os.path.exists(base_path):
        # Check for old structure (files in root)
        files = os.listdir(base_path)
        has_content = any(
            f.endswith('.pdf') or f == 'tracking.json' 
            for f in files
        )
        
        # Also check for new structure (subfolders with content)
        if not has_content:
            pdf_dir = os.path.join(base_path, 'pdfs')
            data_dir = os.path.join(base_path, 'run_data')
            if os.path.exists(pdf_dir) and os.listdir(pdf_dir):
                has_content = True
            elif os.path.exists(data_dir) and os.listdir(data_dir):
                has_content = True
    
    if not has_content:
        # Folder exists but is empty, use it
        _run_directory_cache = base_path
        return base_path
    
    # Folder has content, need to create a numbered folder
    counter = 2
    while True:
        numbered_path = f"{download_base}/{base_date} ({counter})"
        if not os.path.exists(numbered_path):
            _run_directory_cache = numbered_path
            return numbered_path
        
        # Check if this numbered folder has content (both old and new structure)
        files = os.listdir(numbered_path)
        has_content = any(
            f.endswith('.pdf') or f == 'tracking.json' 
            for f in files
        )
        
        # Also check new subfolder structure
        if not has_content:
            pdf_dir = os.path.join(numbered_path, 'pdfs')
            data_dir = os.path.join(numbered_path, 'run_data')
            if os.path.exists(pdf_dir) and os.listdir(pdf_dir):
                has_content = True
            elif os.path.exists(data_dir) and os.listdir(data_dir):
                has_content = True
        
        if not has_content:
            # Found an empty numbered folder, use it
            _run_directory_cache = numbered_path
            return numbered_path
        
        counter += 1
        
        # Safety check to prevent infinite loop
        if counter > 100:
            raise RuntimeError("Too many runs for today (>100). Please check downloads folder.")

# Format: MM-DD-YYYY (e.g., 10-01-2025)
TODAY_FOLDER = datetime.now().strftime('%m-%d-%Y')
RUN_DIR = get_run_directory()  # Main folder for today's run (may be numbered)

# Organized subfolders - these are now functions to avoid recursion issues
def DATA_DIR():
    """Get the data directory path and ensure it exists."""
    data_dir = os.path.join(get_run_directory(), "run_data")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

def PDF_DIR():
    """Get the PDF directory path and ensure it exists."""
    pdf_dir = os.path.join(get_run_directory(), "pdfs")
    os.makedirs(pdf_dir, exist_ok=True)
    return pdf_dir

