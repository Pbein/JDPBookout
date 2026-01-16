"""Inventory page interactions (async version).

Responsibilities:
- Navigate to inventory page
- Clear active filters
- Export inventory CSV
- Filter by Reference Number
- Open vehicle by clicking Book icon in the row
"""
import asyncio
from playwright.async_api import Page
from jdp_scraper import selectors, config


async def clear_filters_async(page: Page) -> bool:
    """
    Clear any active filters on the inventory table (async version).
    
    Args:
        page: Playwright Page object (async)
        
    Returns:
        True if filters were cleared or no filters present, False on error
    """
    try:
        print("\nChecking for active filters...")
        
        # Check if the Clear button exists
        clear_button = page.locator(selectors.CLEAR_FILTERS_BUTTON)
        create_filter_button = page.locator(selectors.CREATE_FILTER_BUTTON)
        
        # Wait a moment for the page to fully load
        await asyncio.sleep(1)
        
        if await clear_button.is_visible(timeout=3000):
            print("Clear button found. Filters are active. Clicking Clear...")
            await clear_button.click()
            
            # Wait for the grid to refresh
            print("Waiting for grid to refresh...")
            await asyncio.sleep(2)
            await page.wait_for_load_state("networkidle", timeout=10000)
            
            print("[SUCCESS] Filters cleared!")
            return True
        elif await create_filter_button.is_visible(timeout=3000):
            print("No active filters found (Create Filter button present).")
            return True
        else:
            print("Filter controls not found - page may still be loading.")
            return True
            
    except Exception as e:
        print(f"[WARNING] Could not check/clear filters: {e}")
        # Not a critical error - continue anyway
        return True


async def navigate_to_inventory_async(page: Page) -> bool:
    """
    Navigate to the inventory page (async version).
    
    Args:
        page: Playwright Page object (async)
        
    Returns:
        True if navigation successful, False otherwise
    """
    try:
        print("\nNavigating to Inventory page...")
        
        # Look for the inventory link
        inventory_link = page.locator(selectors.INVENTORY_LINK)
        
        if await inventory_link.is_visible(timeout=5000):
            # Click the inventory link
            await inventory_link.click()
            
            # Wait for navigation
            await page.wait_for_load_state("networkidle")
            
            print(f"[SUCCESS] Navigated to Inventory page")
            print(f"Current URL: {page.url}")
            print(f"Current Page Title: {await page.title()}")
            return True
        else:
            print("[ERROR] Inventory link not found")
            return False
            
    except Exception as e:
        print(f"[ERROR] Failed to navigate to inventory: {e}")
        return False


async def export_inventory_csv_async(page: Page, download_path: str = None) -> str:
    """
    Export the inventory table to CSV (async version).
    
    Args:
        page: Playwright Page object (async)
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
            download_path = config.DATA_DIR()
        
        os.makedirs(download_path, exist_ok=True)
        print(f"Saving to folder: {download_path}")
        
        # Start waiting for download before clicking
        async with page.expect_download() as download_info:
            # Step 1: Click the Export menu button
            print("Clicking Export menu...")
            export_button = page.locator(selectors.EXPORT_MENU_BUTTON)
            await export_button.click()
            await asyncio.sleep(0.5)
            
            # Step 2: Click "Export All Columns"
            print("Clicking 'Export All Columns'...")
            export_all = page.locator(selectors.EXPORT_ALL_COLUMNS)
            await export_all.click()
            await asyncio.sleep(0.5)
            
            # Step 3: Click "Export to CSV"
            print("Clicking 'Export to CSV'...")
            export_csv = page.locator(selectors.EXPORT_TO_CSV)
            await export_csv.click()
        
        # Wait for the download to complete
        download = await download_info.value
        
        # Save the file with a simple name (inventory.csv)
        csv_filename = "inventory.csv"
        csv_path = os.path.join(download_path, csv_filename)
        
        await download.save_as(csv_path)
        
        print(f"[SUCCESS] CSV exported to: {csv_path}")
        return csv_path
        
    except Exception as e:
        print(f"[ERROR] Failed to export CSV: {e}")
        return ""


async def filter_by_reference_number_async(page: Page, reference_number: str) -> bool:
    """
    Filter the inventory table by reference number (stock number) - async version.
    Properly clears previous value and triggers the filter.
    
    Args:
        page: Playwright Page object (async)
        reference_number: Reference number to filter by
        
    Returns:
        True if filter applied successfully, False otherwise
    """
    try:
        print(f"\nFiltering by reference number: {reference_number}")
        
        # Find the stock number input
        stock_input = page.locator(selectors.STOCK_NUMBER_INPUT)
        
        if await stock_input.is_visible(timeout=5000):
            # Method 1: Clear using triple-click + delete
            print("Clearing previous value...")
            await stock_input.click(click_count=3)  # Triple-click to select all
            await page.keyboard.press("Backspace")  # Delete the selected text
            await asyncio.sleep(0.5)
            
            # Method 2: Fill with empty string to ensure it's clear
            await stock_input.fill("")
            await asyncio.sleep(0.3)
            
            # Now fill in the new reference number
            print(f"Entering new reference number: {reference_number}")
            await stock_input.fill(reference_number)
            
            # Trigger the onchange event using JavaScript to ensure filter is applied
            await page.evaluate(f"vehicleGridViewFilterChanged('StockNumber')")
            
            # Wait for the table to refresh
            print("Waiting for table to refresh...")
            await asyncio.sleep(3)  # Increased wait time
            await page.wait_for_load_state("networkidle", timeout=15000)
            
            # Verify the input has the correct value
            current_value = await stock_input.input_value()
            print(f"Stock input now contains: '{current_value}'")
            
            if current_value == reference_number:
                print(f"[SUCCESS] Filtered table by reference number: {reference_number}")
                return True
            else:
                print(f"[WARNING] Input value mismatch. Expected '{reference_number}', got '{current_value}'")
                return False
        else:
            print("[ERROR] Stock number input not found")
            return False
            
    except Exception as e:
        print(f"[ERROR] Could not filter by reference number: {e}")
        import traceback
        traceback.print_exc()
        return False


async def click_bookout_for_vehicle_async(page: Page, reference_number: str) -> bool:
    """
    Click the Bookout link to open the vehicle details page (async version).
    Uses JavaScript click via page.evaluate for reliability.
    
    Args:
        page: Playwright Page object (async)
        reference_number: Reference number (for logging)
        
    Returns:
        True if clicked successfully, False otherwise
    """
    try:
        print(f"Looking for Bookout link for reference: {reference_number}...")
        
        # Wait a moment for the table to fully render
        await asyncio.sleep(2)
        
        # Check if bookout image exists
        bookout_img = page.locator(selectors.BOOKOUT_IMAGE).first
        
        if not await bookout_img.is_visible(timeout=5000):
            print(f"[ERROR] No bookout image found for reference: {reference_number}")
            print("This reference number might not have a vehicle in the filtered results.")
            return False
        
        # Use JavaScript to click the bookout image's parent link
        # This is more reliable than Playwright's click for this specific site
        print("Clicking Bookout link via JavaScript...")
        await page.evaluate("document.querySelector('img[title=\"Bookout\"]').parentElement.click()")
        
        # Wait for navigation to complete
        await asyncio.sleep(3)
        await page.wait_for_load_state("networkidle", timeout=config.NAVIGATION_TIMEOUT)
        
        print(f"[SUCCESS] Opened vehicle page for reference: {reference_number}")
        print(f"Current URL: {page.url}")
        return True
            
    except Exception as e:
        print(f"[ERROR] Could not click bookout link: {e}")
        import traceback
        traceback.print_exc()
        return False
