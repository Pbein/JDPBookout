"""Vehicle page interactions.

Responsibilities:
- Wait for vehicle page ready (Print available)
- Open Print/Email Reports modal
- Click Create PDF and download
- Handle new tab with PDF
"""
from playwright.sync_api import Page, expect
from jdp_scraper import selectors
import time
import os


def download_vehicle_pdf(page: Page, reference_number: str, save_directory: str = None) -> str:
    """
    Download the PDF for a vehicle from the vehicle details page.
    
    Args:
        page: Playwright Page object (on vehicle page)
        reference_number: Reference number for naming the PDF
        save_directory: Directory to save PDF (default: from config)
        
    Returns:
        Path to the downloaded PDF, or empty string on failure
    """
    try:
        from jdp_scraper import config
        
        if save_directory is None:
            save_directory = config.PDF_DIR
        
        os.makedirs(save_directory, exist_ok=True)
        
        print(f"\nDownloading PDF for reference: {reference_number}")
        
        # Step 1: Wait for Print/Email Reports button to be available
        print("Waiting for Print/Email Reports button...")
        print_button = page.locator(selectors.PRINT_EMAIL_BUTTON)
        print_button.wait_for(state="visible", timeout=20000)
        
        # Step 2: Click Print/Email Reports button
        print("Clicking 'Print/Email Reports' button...")
        print_button.click()
        time.sleep(1)
        
        # Step 3: Wait for modal and click Create PDF button
        print("Waiting for Create PDF button in modal...")
        create_pdf_button = page.locator(selectors.CREATE_PDF_BUTTON)
        create_pdf_button.wait_for(state="visible", timeout=10000)
        
        print("Clicking 'Create PDF' button...")
        
        # Wait for new page/tab to open when clicking Create PDF
        with page.context.expect_page() as new_page_info:
            create_pdf_button.click()
        
        # Get the new page (PDF tab)
        pdf_page = new_page_info.value
        pdf_url = pdf_page.url
        print(f"New tab opened: {pdf_url}")
        
        # Wait for PDF to load
        print("Waiting for PDF to load...")
        pdf_page.wait_for_load_state("load", timeout=30000)
        time.sleep(2)  # Extra wait for PDF to fully load
        
        # Download the PDF file directly from the URL
        pdf_filename = f"{reference_number}.pdf"
        pdf_path = os.path.join(save_directory, pdf_filename)
        
        print(f"Downloading PDF from URL to: {pdf_path}")
        
        # Use the page context to download the PDF
        import requests
        from playwright.sync_api import Browser
        
        # Get cookies from the browser context for authenticated download
        cookies = pdf_page.context.cookies()
        
        # Build cookie dict for requests
        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        
        # Download the PDF using requests with the browser's session
        response = requests.get(pdf_url, cookies=cookie_dict, stream=True)
        
        if response.status_code == 200:
            with open(pdf_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"PDF file downloaded successfully: {os.path.getsize(pdf_path)} bytes")
        else:
            print(f"[WARNING] HTTP {response.status_code} when downloading PDF")
        
        # Close the PDF tab
        print("Closing PDF tab...")
        pdf_page.close()
        
        print(f"[SUCCESS] PDF downloaded: {pdf_path}")
        return pdf_path
        
    except Exception as e:
        print(f"[ERROR] Failed to download PDF: {e}")
        return ""

