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
INVENTORY_URL = "https://extapps.jdpowervalues.com/ValuesOnline/Inventory"

# Credentials from environment
JD_USER = os.getenv("JD_USER", "")
JD_PASS = os.getenv("JD_PASS", "")

# Browser settings
HEADLESS = os.getenv("HEADLESS", "false").lower() in ("true", "1", "yes")

# Timeouts (in milliseconds for Playwright)
DEFAULT_TIMEOUT = 30000  # 30 seconds
NAVIGATION_TIMEOUT = 60000  # 60 seconds
DOWNLOAD_TIMEOUT = 120000  # 2 minutes

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Download directory naming
from datetime import datetime

def get_run_directory():
    """
    Get the run directory for today, creating a numbered folder if needed.
    
    Format: downloads/MM-DD-YYYY or downloads/MM-DD-YYYY (2), etc.
    
    Returns:
        str: Path to the run directory
    """
    base_date = datetime.now().strftime('%m-%d-%Y')
    base_path = f"downloads/{base_date}"
    
    # Check if base path exists and has content
    if not os.path.exists(base_path):
        # First run of the day
        return base_path
    
    # Check if there are any PDFs or tracking.json in the base path
    has_content = False
    if os.path.exists(base_path):
        files = os.listdir(base_path)
        # Check for PDFs or tracking.json (signs of a previous run)
        has_content = any(
            f.endswith('.pdf') or f == 'tracking.json' 
            for f in files
        )
    
    if not has_content:
        # Folder exists but is empty, use it
        return base_path
    
    # Folder has content, need to create a numbered folder
    counter = 2
    while True:
        numbered_path = f"downloads/{base_date} ({counter})"
        if not os.path.exists(numbered_path):
            return numbered_path
        
        # Check if this numbered folder has content
        files = os.listdir(numbered_path)
        has_content = any(
            f.endswith('.pdf') or f == 'tracking.json' 
            for f in files
        )
        
        if not has_content:
            # Found an empty numbered folder, use it
            return numbered_path
        
        counter += 1
        
        # Safety check to prevent infinite loop
        if counter > 100:
            raise RuntimeError("Too many runs for today (>100). Please check downloads folder.")

# Format: MM-DD-YYYY (e.g., 10-01-2025)
TODAY_FOLDER = datetime.now().strftime('%m-%d-%Y')
RUN_DIR = get_run_directory()  # Main folder for today's run (may be numbered)
DATA_DIR = RUN_DIR  # CSV and data files go here
PDF_DIR = RUN_DIR  # PDFs will be saved here

