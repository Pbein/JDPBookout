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


def run():
    """Main orchestration function to run the PDF downloader."""
    print(f"Starting JD Power PDF Downloader...")
    print(f"Today's folder: {config.TODAY_FOLDER}")
    print(f"Run directory: {config.RUN_DIR}")
    print(f"Headless mode: {config.HEADLESS}")
    print(f"Target URL: {config.BASE_URL}")
    
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
            
            # TEST: Download PDF for the FIRST reference number only
            print("\n=== TESTING PDF DOWNLOAD FOR FIRST REFERENCE NUMBER ===")
            
            # Get the first reference number that needs downloading
            first_ref = None
            for ref_num, pdf_status in tracking.items():
                if pdf_status is None:  # Not downloaded yet
                    first_ref = ref_num
                    break
            
            if first_ref:
                print(f"Testing with reference number: {first_ref}")
                
                # Filter inventory by reference number
                if filter_by_reference_number(page, first_ref):
                    # Click bookout to open vehicle page
                    if click_bookout_for_vehicle(page, first_ref):
                        # Download the PDF
                        pdf_path = download_vehicle_pdf(page, first_ref)
                        
                        if pdf_path:
                            # Update tracking
                            pdf_filename = f"{first_ref}.pdf"
                            update_tracking(tracking, first_ref, pdf_filename)
                            print(f"\n[TEST SUCCESS] PDF downloaded and tracking updated!")
                        else:
                            print(f"\n[TEST FAILED] Could not download PDF")
                        
                        # Navigate back to inventory
                        print("\nNavigating back to inventory...")
                        if navigate_to_inventory(page):
                            print("[SUCCESS] Back at inventory page")
                    else:
                        print("[TEST FAILED] Could not click bookout")
                else:
                    print("[TEST FAILED] Could not filter by reference number")
            else:
                print("No reference numbers need downloading!")
            
            print("=== TEST COMPLETE ===\n")
            
            # Keep browser open for now to inspect
            print("\nBrowser is open. Press Ctrl+C to close...")
            input("Press Enter to close the browser...")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            # ALWAYS logout before closing
            try:
                logout(page)
            except:
                print("[WARNING] Could not logout (page may be closed)")
            
            browser.close()
            print("\nBrowser closed.")

