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
from jdp_scraper.metrics import RunMetrics
from jdp_scraper.checkpoint import ProgressCheckpoint


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


def recover_to_inventory(page: Page) -> bool:
    """
    Attempt to recover back to the inventory page after an error.
    Closes any stuck tabs/modals and navigates back.
    
    Args:
        page: Playwright Page object
        
    Returns:
        True if recovery successful, False otherwise
    """
    try:
        print("[RECOVERY] Attempting to return to inventory...")
        
        # Close any extra tabs that might be open (stuck PDF tabs)
        try:
            for context_page in page.context.pages:
                if context_page != page and not context_page.is_closed():
                    print(f"[RECOVERY] Closing extra tab: {context_page.url}")
                    context_page.close()
        except Exception as e:
            print(f"[RECOVERY] Could not close extra tabs: {e}")
        
        # Try to navigate back to inventory
        if not navigate_to_inventory(page):
            # If normal navigation fails, force navigate via URL
            print("[RECOVERY] Normal navigation failed, forcing URL navigation...")
            page.goto(config.INVENTORY_URL, wait_until="networkidle", timeout=30000)
        
        print("[RECOVERY] Successfully returned to inventory")
        return True
        
    except Exception as e:
        print(f"[RECOVERY] Failed to recover to inventory: {e}")
        return False


def process_single_vehicle(
    page: Page, ref_num: str, tracking: dict, checkpoint: ProgressCheckpoint = None, 
    metrics: RunMetrics | None = None, max_retries: int = 2
) -> bool:
    """
    Process a single vehicle: filter, open, download PDF, return to inventory.
    Includes retry logic for transient failures.
    
    Args:
        page: Playwright Page object
        ref_num: Reference number to process
        tracking: Tracking dictionary to update
        metrics: Optional metrics tracker
        max_retries: Maximum number of retry attempts (default: 2)
        
    Returns:
        True if successful, False otherwise
    """
    if metrics is not None:
        metrics.start_vehicle(ref_num)

    for attempt in range(max_retries + 1):
        if attempt > 0:
            print(f"\n[RETRY] Attempt {attempt + 1}/{max_retries + 1} for reference: {ref_num}")
            import time
            time.sleep(3)  # Wait a bit before retrying
        
        try:
            # Filter inventory by reference number
            if not filter_by_reference_number(page, ref_num):
                print(f"[ERROR] Could not filter by reference number: {ref_num}")
                if attempt < max_retries:
                    recover_to_inventory(page)
                    continue
                if metrics is not None:
                    metrics.end_vehicle(ref_num, status="failed", error="filter_failed")
                return False

            # Click bookout to open vehicle page
            if not click_bookout_for_vehicle(page, ref_num):
                print(f"[ERROR] Could not click bookout for: {ref_num}")
                if attempt < max_retries:
                    recover_to_inventory(page)
                    continue
                if metrics is not None:
                    metrics.end_vehicle(ref_num, status="failed", error="bookout_click_failed")
                return False
            
            # Download the PDF
            pdf_path = download_vehicle_pdf(page, ref_num)
            
            if not pdf_path:
                print(f"[ERROR] Could not download PDF for: {ref_num}")
                # Recover back to inventory
                if not recover_to_inventory(page):
                    # If recovery fails, try harder
                    page.goto(config.INVENTORY_URL, wait_until="networkidle", timeout=30000)
                
                # Retry if we have attempts left
                if attempt < max_retries:
                    continue
                    
                if metrics is not None:
                    metrics.end_vehicle(ref_num, status="failed", error="download_failed")
                return False

            # Update tracking
            pdf_filename = f"{ref_num}.pdf"
            update_tracking(tracking, ref_num, pdf_filename)
            print(f"[SUCCESS] PDF downloaded and tracked: {ref_num}.pdf")
            
            # Record success in checkpoint
            if checkpoint is not None:
                checkpoint.record_success(ref_num)
            
            if metrics is not None:
                metrics.end_vehicle(ref_num, status="success")
            
            # Navigate back to inventory
            if not navigate_to_inventory(page):
                print(f"[WARNING] Could not navigate back to inventory after {ref_num}")
                # Force recovery
                recover_to_inventory(page)
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Exception while processing {ref_num}: {e}")
            
            # Try to recover
            try:
                recover_to_inventory(page)
            except:
                print("[ERROR] Recovery failed, forcing URL navigation...")
                try:
                    page.goto(config.INVENTORY_URL, wait_until="networkidle", timeout=30000)
                except:
                    pass
            
            # Retry if we have attempts left
            if attempt < max_retries:
                continue
            
            # Record failure in checkpoint after all retries exhausted
            if checkpoint is not None:
                checkpoint.record_failure(ref_num)
                
            if metrics is not None:
                metrics.end_vehicle(ref_num, status="failed", error=str(e))
            return False
    
    # Should never reach here, but just in case
    if checkpoint is not None:
        checkpoint.record_failure(ref_num)
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
    STUCK_THRESHOLD = 5  # Number of consecutive failures before considering "stuck"

    metrics = RunMetrics()
    metrics.add_metadata(headless=config.HEADLESS, max_downloads=MAX_DOWNLOADS)
    
    checkpoint = ProgressCheckpoint()

    total_inventory = 0
    attempted = 0
    success_count = 0
    fail_count = 0
    remaining = 0

    with sync_playwright() as p:
        # Launch browser
        with metrics.track_step("launch_browser"):
            browser = p.chromium.launch(headless=config.HEADLESS)
            context = browser.new_context()
            page = context.new_page()

        # Set default timeout
        page.set_default_timeout(config.DEFAULT_TIMEOUT)

        try:
            # Navigate to the website
            print(f"\nNavigating to {config.BASE_URL}...")
            with metrics.track_step("navigate_to_base"):
                page.goto(config.BASE_URL, wait_until="networkidle")
                print(f"Page loaded: {page.title()}")

            # Perform login
            with metrics.track_step("login"):
                login_success = login(page)
            if not login_success:
                print("Login failed. Exiting...")
                return

            # Accept license agreement if present
            with metrics.track_step("accept_license"):
                accept_license(page)

            # Navigate to inventory page
            with metrics.track_step("navigate_to_inventory"):
                inventory_loaded = navigate_to_inventory(page)
            if not inventory_loaded:
                print("Failed to navigate to inventory. Exiting...")
                return

            # Clear any existing filters
            with metrics.track_step("clear_filters"):
                clear_filters(page)

            # Export inventory to CSV
            with metrics.track_step("export_inventory_csv"):
                csv_path = export_inventory_csv(page)
            if not csv_path:
                print("Failed to export CSV. Exiting...")
                return

            print(f"\nInventory CSV saved at: {csv_path}")

            # Build tracking of reference numbers and their PDF status
            with metrics.track_step("build_reference_tracking"):
                tracking = build_reference_tracking(csv_path)
            total_inventory = len(tracking)
            metrics.add_metadata(total_inventory=total_inventory)

            # Save tracking to JSON for resume capability
            with metrics.track_step("save_tracking"):
                save_tracking_to_json(tracking)

            # Get list of reference numbers that need downloading
            pending_refs = [ref for ref, status in tracking.items() if status is None]
            total_pending = len(pending_refs)
            already_done = len(tracking) - total_pending
            remaining = total_pending

            print(f"\n{'='*60}")
            print(f"BATCH PROCESSING: Will download up to {MAX_DOWNLOADS} PDFs")
            print(f"Total vehicles: {len(tracking)}")
            print(f"Already downloaded: {already_done}")
            print(f"Pending: {total_pending}")
            print(f"{'='*60}\n")

            if total_pending == 0:
                print("All PDFs already downloaded! Nothing to do.")
                metrics.finalize(
                    total_inventory=total_inventory,
                    attempted=0,
                    succeeded=0,
                    failed=0,
                    remaining=0,
                )
                return

            # Limit to MAX_DOWNLOADS
            refs_to_process = pending_refs[:MAX_DOWNLOADS]
            attempted = len(refs_to_process)

            # Process each reference number
            for idx, ref_num in enumerate(refs_to_process, 1):
                print(f"\n{'='*60}")
                print(f"Processing {idx}/{len(refs_to_process)}: Reference {ref_num}")
                print(f"Progress: {success_count} succeeded, {fail_count} failed")
                print(f"{'='*60}")

                # Check if we're stuck (too many consecutive failures)
                if checkpoint.is_stuck(STUCK_THRESHOLD):
                    print(f"\n⚠️  WARNING: {checkpoint.consecutive_failures} consecutive failures detected!")
                    print(f"[RECOVERY] Attempting browser recovery...")
                    
                    # Try to recover by closing browser and restarting
                    try:
                        browser.close()
                        print("[RECOVERY] Browser closed, relaunching...")
                        import time
                        time.sleep(5)  # Wait before relaunch
                        
                        browser = p.chromium.launch(headless=config.HEADLESS)
                        context = browser.new_context()
                        page = context.new_page()
                        page.set_default_timeout(config.DEFAULT_TIMEOUT)
                        
                        # Re-login
                        print("[RECOVERY] Re-logging in...")
                        page.goto(config.BASE_URL, wait_until="networkidle")
                        if not login(page):
                            print("[RECOVERY] Login failed, aborting...")
                            break
                        accept_license(page)
                        navigate_to_inventory(page)
                        
                        # Reset stuck state
                        checkpoint.reset_if_stuck()
                        print("[RECOVERY] Browser recovered successfully!")
                        
                    except Exception as recovery_error:
                        print(f"[RECOVERY] Failed to recover: {recovery_error}")
                        print("[RECOVERY] Continuing with existing browser...")
                        checkpoint.reset_if_stuck()  # Reset anyway to avoid infinite loop

                if process_single_vehicle(page, ref_num, tracking, checkpoint=checkpoint, metrics=metrics):
                    success_count += 1
                    # Add a small delay after successful download to avoid overwhelming the server
                    if idx < len(refs_to_process):  # Don't delay after the last one
                        import time
                        time.sleep(1)  # 1 second pause between successful downloads
                else:
                    fail_count += 1

                # Show progress and checkpoint status every 10 items
                print(f"\nStatus: {success_count}/{len(refs_to_process)} completed successfully")
                if idx % 10 == 0:
                    checkpoint.print_status()
                
                remaining = max(total_pending - (success_count + fail_count), 0)

            # Final summary
            print(f"\n{'='*60}")
            print(f"BATCH COMPLETE!")
            print(f"{'='*60}")
            print(f"Successfully downloaded: {success_count}")
            print(f"Failed: {fail_count}")
            print(f"Total processed: {len(refs_to_process)}")
            print(f"Remaining: {total_pending - len(refs_to_process)}")
            print(f"{'='*60}\n")
            
            # Print final checkpoint status
            checkpoint.print_status()

            metrics.finalize(
                total_inventory=total_inventory,
                attempted=attempted,
                succeeded=success_count,
                failed=fail_count,
                remaining=remaining,
            )

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

            if metrics.summary is None:
                metrics.finalize(
                    total_inventory=total_inventory,
                    attempted=attempted,
                    succeeded=success_count,
                    failed=fail_count,
                    remaining=remaining,
                )
            metrics_path = metrics.save()
            print(f"[METRICS] Saved timing data to {metrics_path}")
            metrics.print_console_report(additional_targets=[2000])
