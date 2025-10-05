"""Async orchestration for parallel PDF downloads.

High-level control flow using Playwright async API with single context, multiple pages.
Implements pre-assignment strategy to prevent duplicate downloads.
"""
import asyncio
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from jdp_scraper import config
from jdp_scraper.async_utils import AsyncSemaphorePool
from jdp_scraper.page_pool import PagePool
from jdp_scraper.checkpoint import ProgressCheckpoint
from jdp_scraper.metrics import RunMetrics
from jdp_scraper.downloads import (
    read_reference_numbers_from_csv,
    build_reference_tracking,
    load_tracking_from_json,
    save_tracking_to_json,
    update_tracking
)
from jdp_scraper.auth_async import login_async
from jdp_scraper.license_page_async import accept_license_async
from jdp_scraper.inventory_async import (
    navigate_to_inventory_async,
    clear_filters_async,
    export_inventory_csv_async,
    filter_by_reference_number_async,
    click_bookout_for_vehicle_async
)
from jdp_scraper.vehicle_async import download_vehicle_pdf_async


async def setup_resource_blocking(context: BrowserContext) -> None:
    """
    Set up resource blocking for a context to improve performance.
    
    Blocks: images, stylesheets, fonts, media (30-50% speedup)
    
    Args:
        context: The browser context to configure
    """
    async def block_handler(route, request):
        """Block certain resource types."""
        resource_type = request.resource_type
        
        if resource_type in ['image', 'imageset', 'stylesheet', 'font', 'media']:
            await route.abort()
        else:
            await route.continue_()
            
    await context.route("**/*", block_handler)
    print("[RESOURCE_BLOCKING] Enabled (CSS/images/fonts blocked)")


async def recover_to_inventory_async(page: Page) -> bool:
    """
    Recover from stuck state by closing extra tabs and returning to inventory.
    
    Args:
        page: The main page for this context
        
    Returns:
        True if recovery successful, False otherwise
    """
    try:
        print("[RECOVERY] Attempting to recover to inventory page...")
        
        # Close any extra tabs/pages in this context
        for context_page in page.context.pages:
            if context_page != page and not context_page.is_closed():
                print(f"[RECOVERY] Closing extra tab: {context_page.url}")
                await context_page.close()
        
        # Navigate back to inventory
        await page.goto(config.INVENTORY_URL, wait_until="networkidle", timeout=20000)
        await asyncio.sleep(2)
        
        print("[RECOVERY] Successfully recovered to inventory page")
        return True
        
    except Exception as e:
        print(f"[RECOVERY] Failed to recover: {e}")
        return False


async def process_single_vehicle_async(
    page: Page,
    ref_num: str,
    tracking: Dict[str, Optional[str]],
    checkpoint: ProgressCheckpoint,
    metrics: RunMetrics,
    semaphore_pool: AsyncSemaphorePool,
    max_retries: int = 2
) -> bool:
    """
    Process a single vehicle: filter, open, download PDF (async version).
    
    Args:
        page: Playwright Page for this context
        ref_num: Reference number to process
        tracking: Tracking dictionary (shared, will be updated)
        checkpoint: Progress checkpoint (thread-safe)
        metrics: Metrics tracker
        semaphore_pool: Semaphore pool for concurrency control
        max_retries: Number of retry attempts
        
    Returns:
        True if successful, False otherwise
    """
    async with semaphore_pool.acquire():
        metrics.start_vehicle(ref_num)
        
        for attempt in range(max_retries + 1):
            try:
                print(f"\n{'='*60}")
                print(f"Processing: {ref_num} (Attempt {attempt + 1}/{max_retries + 1})")
                print(f"{'='*60}")
                
                # Filter by reference number
                if not await filter_by_reference_number_async(page, ref_num):
                    raise Exception("Failed to filter by reference number")
                
                # Click bookout to open vehicle page
                if not await click_bookout_for_vehicle_async(page, ref_num):
                    raise Exception("Failed to click bookout")
                
                # Download the PDF
                pdf_path = await download_vehicle_pdf_async(page, ref_num)
                if not pdf_path:
                    raise Exception("Failed to download PDF")
                
                # Update tracking
                update_tracking(tracking, ref_num, f"{ref_num}.pdf")
                
                # Record success
                await checkpoint.record_success(ref_num)
                metrics.end_vehicle(ref_num, status="success")
                
                # Navigate back to inventory for next vehicle
                await navigate_to_inventory_async(page)
                
                # Rate limiting
                await asyncio.sleep(1)
                
                print(f"[SUCCESS] Completed {ref_num}")
                return True
                
            except Exception as e:
                print(f"[ERROR] Attempt {attempt + 1} failed for {ref_num}: {e}")
                
                if attempt < max_retries:
                    print(f"[RETRY] Retrying {ref_num} after recovery...")
                    await recover_to_inventory_async(page)
                    await asyncio.sleep(3)
                else:
                    print(f"[FAILED] All attempts exhausted for {ref_num}")
                    await checkpoint.record_failure(ref_num)
                    metrics.end_vehicle(ref_num, status="failed", error=str(e))
                    
                    # Try to recover for next vehicle
                    await recover_to_inventory_async(page)
                    return False
        
        return False




async def logout_async(page: Page) -> None:
    """
    Logout from the application.
    
    Args:
        page: Playwright Page object
    """
    try:
        from jdp_scraper import selectors
        print("\n[LOGOUT] Logging out...")
        logout_button = page.locator(selectors.LOGOUT_BUTTON)
        if await logout_button.is_visible(timeout=5000):
            await logout_button.click()
            await asyncio.sleep(2)
            print("[LOGOUT] Logged out successfully")
    except Exception as e:
        print(f"[LOGOUT] Logout failed (not critical): {e}")


async def run_async() -> None:
    """
    Main async orchestration function for parallel PDF downloads.
    
    This function:
    1. Launches browser (headless)
    2. Creates context pool
    3. Initializes all contexts (parallel login)
    4. Exports CSV (once)
    5. Pre-assigns vehicles to contexts
    6. Processes vehicles in parallel
    7. Cleans up and reports
    """
    # Initialize metrics and checkpoint
    metrics = RunMetrics()
    checkpoint = ProgressCheckpoint()
    
    # Get number of pages (workers)
    num_pages = int(os.getenv("CONCURRENT_CONTEXTS", "5"))
    
    print("\n" + "="*60)
    print("JD POWER PDF DOWNLOADER - PARALLEL VERSION")
    print("="*60)
    print(f"Run directory      : {config.RUN_DIR}")
    print(f"Max downloads      : {config.MAX_DOWNLOADS_PER_RUN}")
    print(f"Parallel pages     : {num_pages}")
    print(f"Headless mode      : {config.HEADLESS}")
    print(f"Block resources    : {config.BLOCK_RESOURCES} (CSS/images/fonts)")
    print("="*60 + "\n")
    
    async with async_playwright() as p:
        browser: Browser = None
        context: BrowserContext = None
        page_pool: PagePool = None
        pages: List[Page] = []
        
        try:
            # Launch browser
            print("[BROWSER] Launching browser...")
            browser = await p.chromium.launch(headless=config.HEADLESS)
            print(f"[BROWSER] Browser launched (headless={config.HEADLESS})")
            
            # Create single context
            print("\n[CONTEXT] Creating single browser context...")
            context = await browser.new_context()
            print("[CONTEXT] Context created")
            
            # Apply resource blocking if enabled
            if config.BLOCK_RESOURCES:
                await setup_resource_blocking(context)
            
            # Login on first page
            print("\n[LOGIN] Logging in on first page...")
            page_0 = await context.new_page()
            await page_0.goto(config.LOGIN_URL, wait_until="networkidle")
            
            if not await login_async(page_0):
                raise Exception("Login failed")
            
            # Accept license if present
            await accept_license_async(page_0)
            
            # Wait for page to settle
            await asyncio.sleep(2)
            
            # Navigate to inventory
            print("\n[INVENTORY] Navigating to inventory...")
            await page_0.goto(config.INVENTORY_URL, wait_until="networkidle", timeout=20000)
            await asyncio.sleep(2)
            
            # Clear filters
            await clear_filters_async(page_0)
            
            # Export CSV
            print("\n[CSV] Exporting inventory CSV...")
            csv_path = await export_inventory_csv_async(page_0)
            if not csv_path:
                raise Exception("Failed to export CSV")
            
            # Read reference numbers from CSV
            print("[CSV] Reading reference numbers from CSV...")
            all_refs = read_reference_numbers_from_csv(csv_path)
            print(f"[CSV] Found {len(all_refs)} reference numbers")
            
            # Load or build tracking
            tracking = load_tracking_from_json()
            if not tracking:
                tracking = build_reference_tracking(csv_path)
                save_tracking_to_json(tracking)
            
            # Filter to pending references
            pending_refs = [
                ref for ref, status in tracking.items()
                if status is None
            ][:config.MAX_DOWNLOADS_PER_RUN]
            
            print(f"\n[PROCESSING] {len(pending_refs)} vehicles to process")
            
            if not pending_refs:
                print("[INFO] No pending vehicles to process")
                return
            
            # Create page pool with additional pages
            print(f"\n[PAGE_POOL] Creating page pool with {num_pages} pages...")
            page_pool = PagePool(context, num_pages=num_pages)
            await page_pool.initialize(first_page=page_0)
            await page_pool.navigate_all_to_inventory()
            
            # Get all pages
            pages = [page_pool.get_page(i) for i in range(num_pages)]
            
            # Pre-assign vehicles to pages (prevents duplicates)
            print(f"\n[ASSIGNMENT] Pre-assigning vehicles to {num_pages} pages...")
            assignments: Dict[int, List[str]] = {}
            for idx, ref in enumerate(pending_refs):
                page_id = idx % num_pages
                if page_id not in assignments:
                    assignments[page_id] = []
                assignments[page_id].append(ref)
            
            for page_id, refs in assignments.items():
                print(f"[ASSIGNMENT] Page {page_id}: {len(refs)} vehicles")
            
            # Create semaphore pool
            semaphore_pool = AsyncSemaphorePool(max_concurrent=num_pages)
            
            # Process vehicles in parallel
            print(f"\n[PARALLEL] Starting parallel processing...")
            
            all_tasks = []
            for page_id, refs in assignments.items():
                page = pages[page_id]
                for ref in refs:
                    task = process_single_vehicle_async(
                        page=page,
                        ref_num=ref,
                        tracking=tracking,
                        checkpoint=checkpoint,
                        metrics=metrics,
                        semaphore_pool=semaphore_pool
                    )
                    all_tasks.append(task)
            
            # Wait for all tasks to complete (BLOCKING)
            results = await asyncio.gather(*all_tasks, return_exceptions=True)
            
            # Count successes
            successes = sum(1 for r in results if r is True)
            failures = len(results) - successes
            
            print(f"\n[COMPLETE] Processing finished")
            print(f"[COMPLETE] Successes: {successes}/{len(results)}")
            print(f"[COMPLETE] Failures: {failures}/{len(results)}")
            
            # Logout from first context
            await logout_async(pages[0])
            
        except KeyboardInterrupt:
            print("\n[INTERRUPTED] Received interrupt signal")
            
        except Exception as e:
            print(f"\n[ERROR] Fatal error: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            # Cleanup
            print("\n[CLEANUP] Cleaning up...")
            
            # Close page pool
            if page_pool:
                await page_pool.close_all()
            
            # Close context
            if context:
                await context.close()
                print("[CLEANUP] Context closed")
            
            # Close browser
            if browser:
                await browser.close()
                print("[CLEANUP] Browser closed")
            
            # Finalize metrics
            total_inventory = len(all_refs) if 'all_refs' in locals() else 0
            attempted = len(pending_refs) if 'pending_refs' in locals() else 0
            succeeded = checkpoint.total_succeeded
            failed = checkpoint.total_failed
            remaining = total_inventory - checkpoint.total_processed
            
            metrics.finalize(
                total_inventory=total_inventory,
                attempted=attempted,
                succeeded=succeeded,
                failed=failed,
                remaining=remaining
            )
            metrics.save()
            
            # Print final report
            print("\n" + "="*60)
            print("FINAL REPORT")
            print("="*60)
            checkpoint.print_status()
            metrics.print_console_report(checkpoint_data=checkpoint.get_status())
            
            print("\n[EXIT] Program complete")


# Import os for environment variable
import os
