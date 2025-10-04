"""High-level orchestration for end-to-end flow.

Flow:
1. Load env/config
2. Launch Playwright browser (headless flag)
3. Login and accept license if needed
4. Navigate to inventory, clear filters, export CSV
5. Read reference numbers from CSV
6. Build todo list of numbers to process vs done
7. For each number: filter inventory, open vehicle, print/download PDF
8. Save PDF to today's folder as <ReferenceNumber>.pdf
9. Mark number as done and resume if interrupted
10. Logout at the end (ALWAYS)
"""
from playwright.sync_api import sync_playwright, Page
from jdp_scraper import config, selectors
from jdp_scraper.auth import login
from jdp_scraper.license_page import accept_license
from jdp_scraper.inventory import navigate_to_inventory, clear_filters, export_inventory_csv, filter_by_reference_number, click_bookout_for_vehicle
from jdp_scraper.vehicle import download_vehicle_pdf
from jdp_scraper.downloads import build_reference_tracking, save_tracking_to_json, update_tracking


def logout(page: Page) -> bool:
    """
    Logout from the JD Power site.
    This should ALWAYS be called at the end to avoid session lockout.
    
    Args:
        page: Playwright Page object
        
    Returns:
        True if logout successful, False otherwise
    """
    try:
        print("\nLogging out...")
        
        # Check if logout button is present
        logout_btn = page.locator(selectors.LOGOUT_BUTTON)
        
        if logout_btn.is_visible(timeout=5000):
            logout_btn.click()
            print("[SUCCESS] Logged out successfully!")
            page.wait_for_load_state("networkidle", timeout=10000)
            return True
        else:
            print("Logout button not found (may already be logged out).")
            return True
            
    except Exception as e:
        print(f"[WARNING] Logout encountered an issue: {e}")
        return False


def process_single_vehicle(page: Page, ref_num: str, tracking: dict) -> bool:
    """
    Process a single vehicle: filter, open, download PDF, return to inventory.
    
    Args:
        page: Playwright Page object
        ref_num: Reference number to process
        tracking: Tracking dictionary to update
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Filter inventory by reference number
        if not filter_by_reference_number(page, ref_num):
            print(f"[ERROR] Could not filter by reference number: {ref_num}")
            return False
        
        # Click bookout to open vehicle page
        if not click_bookout_for_vehicle(page, ref_num):
            print(f"[ERROR] Could not click bookout for: {ref_num}")
            return False
        
        # Download the PDF
        pdf_path = download_vehicle_pdf(page, ref_num)
        
        if not pdf_path:
            print(f"[ERROR] Could not download PDF for: {ref_num}")
            # Still navigate back even if download failed
            navigate_to_inventory(page)
            return False
        
        # Update tracking
        pdf_filename = f"{ref_num}.pdf"
        update_tracking(tracking, ref_num, pdf_filename)
        print(f"[SUCCESS] PDF downloaded and tracked: {ref_num}.pdf")
        
        # Navigate back to inventory
        if not navigate_to_inventory(page):
            print(f"[WARNING] Could not navigate back to inventory after {ref_num}")
            # Try to recover by clicking the inventory link
            page.goto(config.INVENTORY_URL)
            page.wait_for_load_state("networkidle")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Exception while processing {ref_num}: {e}")
        # Try to navigate back to inventory for recovery
        try:
            navigate_to_inventory(page)
        except:
            pass
        return False


def run():
    """Main orchestration function to run the PDF downloader."""
    print(f"Starting JD Power PDF Downloader...")
    print(f"Today's folder: {config.TODAY_FOLDER}")
    print(f"Run directory: {config.RUN_DIR}")
    print(f"Headless mode: {config.HEADLESS}")
    print(f"Target URL: {config.BASE_URL}")
    
    # Configuration for batch processing
    MAX_DOWNLOADS = 50  # Download up to 50 PDFs in this run (configurable)
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=config.HEADLESS)
        context = browser.new_context()
        page = context.new_page()
        
        # Set default timeout
        page.set_default_timeout(config.DEFAULT_TIMEOUT)
        
        try:
            # Navigate to the website
            print(f"\nNavigating to {config.BASE_URL}...")
            page.goto(config.BASE_URL, wait_until="networkidle")
            print(f"Page loaded: {page.title()}")
            
            # Perform login
            if not login(page):
                print("Login failed. Exiting...")
                return
            
            # Accept license agreement if present
            accept_license(page)
            
            # Navigate to inventory page
            if not navigate_to_inventory(page):
                print("Failed to navigate to inventory. Exiting...")
                return
            
            # Clear any existing filters
            clear_filters(page)
            
            # Export inventory to CSV
            csv_path = export_inventory_csv(page)
            if not csv_path:
                print("Failed to export CSV. Exiting...")
                return
            
            print(f"\nInventory CSV saved at: {csv_path}")
            
            # Build tracking of reference numbers and their PDF status
            tracking = build_reference_tracking(csv_path)
            
            # Save tracking to JSON for resume capability
            save_tracking_to_json(tracking)
            
            # Get list of reference numbers that need downloading
            pending_refs = [ref for ref, status in tracking.items() if status is None]
            total_pending = len(pending_refs)
            already_done = len(tracking) - total_pending
            
            print(f"\n{'='*60}")
            print(f"BATCH PROCESSING: Will download up to {MAX_DOWNLOADS} PDFs")
            print(f"Total vehicles: {len(tracking)}")
            print(f"Already downloaded: {already_done}")
            print(f"Pending: {total_pending}")
            print(f"{'='*60}\n")
            
            if total_pending == 0:
                print("All PDFs already downloaded! Nothing to do.")
                return
            
            # Limit to MAX_DOWNLOADS
            refs_to_process = pending_refs[:MAX_DOWNLOADS]
            
            # Process each reference number
            success_count = 0
            fail_count = 0
            
            for idx, ref_num in enumerate(refs_to_process, 1):
                print(f"\n{'='*60}")
                print(f"Processing {idx}/{len(refs_to_process)}: Reference {ref_num}")
                print(f"Progress: {success_count} succeeded, {fail_count} failed")
                print(f"{'='*60}")
                
                if process_single_vehicle(page, ref_num, tracking):
                    success_count += 1
                else:
                    fail_count += 1
                
                # Show progress
                print(f"\nStatus: {success_count}/{len(refs_to_process)} completed successfully")
            
            # Final summary
            print(f"\n{'='*60}")
            print(f"BATCH COMPLETE!")
            print(f"{'='*60}")
            print(f"Successfully downloaded: {success_count}")
            print(f"Failed: {fail_count}")
            print(f"Total processed: {len(refs_to_process)}")
            print(f"Remaining: {total_pending - len(refs_to_process)}")
            print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # ALWAYS logout before closing
            try:
                logout(page)
            except:
                print("[WARNING] Could not logout (page may be closed)")
            
            browser.close()
            print("\nBrowser closed.")
