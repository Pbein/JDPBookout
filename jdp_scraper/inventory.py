"""Inventory page interactions.

Responsibilities:
- Navigate to inventory page
- Clear active filters
- Export inventory CSV
- Filter by Reference Number
- Open vehicle by clicking Book icon in the row
"""
from playwright.sync_api import Page
from jdp_scraper import selectors
import time


def clear_filters(page: Page) -> bool:
    """
    Clear any active filters on the inventory table.
    
    Args:
        page: Playwright Page object
        
    Returns:
        True if filters were cleared or no filters present, False on error
    """
    try:
        print("\nChecking for active filters...")
        
        # Check if the Clear button exists
        clear_button = page.locator(selectors.CLEAR_FILTERS_BUTTON)
        create_filter_button = page.locator(selectors.CREATE_FILTER_BUTTON)
        
        # Wait a moment for the page to fully load
        time.sleep(1)
        
        if clear_button.is_visible(timeout=3000):
            print("Clear button found. Filters are active. Clicking Clear...")
            clear_button.click()
            
            # Wait for the grid to refresh
            print("Waiting for grid to refresh...")
            time.sleep(2)
            page.wait_for_load_state("networkidle", timeout=10000)
            
            print("[SUCCESS] Filters cleared!")
            return True
        elif create_filter_button.is_visible(timeout=3000):
            print("No active filters found (Create Filter button present).")
            return True
        else:
            print("Filter controls not found - page may still be loading.")
            return True
            
    except Exception as e:
        print(f"[WARNING] Could not check/clear filters: {e}")
        # Not a critical error - continue anyway
        return True


def navigate_to_inventory(page: Page) -> bool:
    """
    Navigate to the inventory page.
    
    Args:
        page: Playwright Page object
        
    Returns:
        True if navigation successful, False otherwise
    """
    try:
        print("\nNavigating to Inventory page...")
        
        # Look for the inventory link
        inventory_link = page.locator(selectors.INVENTORY_LINK)
        
        if inventory_link.is_visible(timeout=5000):
            # Click the inventory link
            inventory_link.click()
            
            # Wait for navigation
            page.wait_for_load_state("networkidle")
            
            print(f"[SUCCESS] Navigated to Inventory page")
            print(f"Current URL: {page.url}")
            print(f"Current Page Title: {page.title()}")
            return True
        else:
            print("[ERROR] Inventory link not found")
            return False
            
    except Exception as e:
        print(f"[ERROR] Failed to navigate to inventory: {e}")
        return False


def export_inventory_csv(page: Page, download_path: str = None) -> str:
    """
    Export the inventory table to CSV.
    
    Args:
        page: Playwright Page object
        download_path: Directory to save the CSV (default: from config.DATA_DIR)
        
    Returns:
        Path to the downloaded CSV file, or empty string on failure
    """
    try:
        print("\nExporting inventory to CSV...")
        
        # Set up download handling
        import os
        from jdp_scraper import config
        
        # Use config directory if not specified
        if download_path is None:
            download_path = config.DATA_DIR
        
        os.makedirs(download_path, exist_ok=True)
        print(f"Saving to folder: {download_path}")
        
        # Start waiting for download before clicking
        with page.expect_download() as download_info:
            # Step 1: Click the Export menu button
            print("Clicking Export menu...")
            export_button = page.locator(selectors.EXPORT_MENU_BUTTON)
            export_button.click()
            time.sleep(0.5)
            
            # Step 2: Click "Export All Columns"
            print("Clicking 'Export All Columns'...")
            export_all = page.locator(selectors.EXPORT_ALL_COLUMNS)
            export_all.click()
            time.sleep(0.5)
            
            # Step 3: Click "Export to CSV"
            print("Clicking 'Export to CSV'...")
            export_csv = page.locator(selectors.EXPORT_TO_CSV)
            export_csv.click()
        
        # Wait for the download to complete
        download = download_info.value
        
        # Save the file with a simple name (inventory.csv)
        csv_filename = "inventory.csv"
        csv_path = os.path.join(download_path, csv_filename)
        
        download.save_as(csv_path)
        
        print(f"[SUCCESS] CSV exported to: {csv_path}")
        return csv_path
        
    except Exception as e:
        print(f"[ERROR] Failed to export CSV: {e}")
        return ""


def filter_by_reference_number(page: Page, reference_number: str) -> bool:
    """
    Filter the inventory table by reference number (stock number).
    
    Args:
        page: Playwright Page object
        reference_number: Reference number to filter by
        
    Returns:
        True if filter applied successfully, False otherwise
    """
    try:
        print(f"\nFiltering by reference number: {reference_number}")
        
        # Find the stock number input
        stock_input = page.locator(selectors.STOCK_NUMBER_INPUT)
        
        if stock_input.is_visible(timeout=5000):
            # Clear any existing value
            stock_input.fill("")
            time.sleep(0.3)
            
            # Fill in the reference number
            stock_input.fill(reference_number)
            
            # Wait for the table to refresh
            print("Waiting for table to refresh...")
            time.sleep(2)
            page.wait_for_load_state("networkidle", timeout=10000)
            
            print(f"[SUCCESS] Filtered table by reference number: {reference_number}")
            return True
        else:
            print("[ERROR] Stock number input not found")
            return False
            
    except Exception as e:
        print(f"[ERROR] Could not filter by reference number: {e}")
        return False


def click_bookout_for_vehicle(page: Page, reference_number: str) -> bool:
    """
    Click the Bookout link to open the vehicle details page.
    
    Args:
        page: Playwright Page object
        reference_number: Reference number (for logging)
        
    Returns:
        True if clicked successfully, False otherwise
    """
    try:
        print(f"Looking for Bookout link for reference: {reference_number}...")
        
        # Wait a moment for the table to fully render
        time.sleep(1)
        
        # Find the bookout link using ID pattern or image
        bookout_link = page.locator(selectors.BOOKOUT_LINK).first
        
        # Wait for it to be visible
        if not bookout_link.is_visible(timeout=3000):
            # Try alternative: find by the image
            print("Trying image selector...")
            bookout_img = page.locator(selectors.BOOKOUT_IMAGE).first
            if not bookout_img.is_visible(timeout=3000):
                print(f"[ERROR] Bookout link/image not found for reference: {reference_number}")
                print("Checking what's on the page...")
                row_count = page.locator("tr[id*='DXDataRow']").count()
                print(f"Found {row_count} data rows in table")
                return False
            # Click the parent link
            bookout_link = bookout_img.locator("xpath=..")
        
        print("Found Bookout link. Clicking...")
        
        # Click and wait for navigation (may take time to load)
        try:
            with page.expect_navigation(timeout=20000, wait_until="load"):
                bookout_link.click()
        except:
            # Navigation might not trigger an event, just wait a bit
            bookout_link.click()
            time.sleep(2)
        
        # Wait for page to be fully loaded
        print("Waiting for vehicle page to load...")
        page.wait_for_load_state("networkidle", timeout=15000)
        
        print(f"[SUCCESS] Opened vehicle page for reference: {reference_number}")
        print(f"Current URL: {page.url}")
        return True
            
    except Exception as e:
        print(f"[ERROR] Could not click bookout link: {e}")
        import traceback
        traceback.print_exc()
        return False

