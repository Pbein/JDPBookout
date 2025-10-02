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
# Format: MM-DD-YYYY (e.g., 10-01-2025)
TODAY_FOLDER = datetime.now().strftime('%m-%d-%Y')
RUN_DIR = f"downloads/{TODAY_FOLDER}"  # Main folder for today's run
DATA_DIR = RUN_DIR  # CSV and data files go here
PDF_DIR = RUN_DIR  # PDFs will be saved here

