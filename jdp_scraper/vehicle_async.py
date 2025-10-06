"""Vehicle page interactions (async version).

Responsibilities:
- Wait for vehicle page ready (Print available)
- Open Print/Email Reports modal
- Click Create PDF and download
- Handle new tab with PDF
"""
import asyncio
from playwright.async_api import Page
from jdp_scraper import selectors
import os

# Global lock to prevent race condition when multiple workers download PDFs simultaneously
# This ensures only one worker clicks "Create PDF" at a time, preventing PDF tab mix-ups
_pdf_download_lock: asyncio.Lock = None

def get_pdf_download_lock() -> asyncio.Lock:
    """Get or create the global PDF download lock."""
    global _pdf_download_lock
    if _pdf_download_lock is None:
        _pdf_download_lock = asyncio.Lock()
    return _pdf_download_lock


async def download_vehicle_pdf_async(page: Page, reference_number: str, save_directory: str = None) -> str:
    """
    Download the PDF for a vehicle from the vehicle details page (async version).
    
    Args:
        page: Playwright Page object (async, on vehicle page)
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
        await print_button.wait_for(state="visible", timeout=20000)
        
        # Step 2: Click Print/Email Reports button
        print("Clicking 'Print/Email Reports' button...")
        await print_button.click()
        await asyncio.sleep(1)
        
        # Step 3: Wait for modal and click Create PDF button
        print("Waiting for Create PDF button in modal...")
        create_pdf_button = page.locator(selectors.CREATE_PDF_BUTTON)
        await create_pdf_button.wait_for(state="visible", timeout=10000)
        
        print("Clicking 'Create PDF' button...")
        
        # Initialize pdf_page to None so we can track if it was created
        pdf_page = None
        
        # CRITICAL SECTION: Use lock to prevent race condition
        # Multiple workers share the same browser context, so when they click "Create PDF"
        # simultaneously, they can grab each other's PDF tabs (page.context.expect_page()
        # listens to ALL pages in the context). The lock ensures only one worker
        # opens/downloads/closes a PDF tab at a time, preventing mix-ups.
        lock = get_pdf_download_lock()
        async with lock:
            print("[LOCK] Acquired PDF download lock")
            
            try:
                # Wait for new page/tab to open when clicking Create PDF
                async with page.context.expect_page() as new_page_info:
                    await create_pdf_button.click()
                
                # Get the new page (PDF tab)
                pdf_page = await new_page_info.value
                pdf_url = pdf_page.url
                print(f"New tab opened: {pdf_url}")
            
                # Wait for PDF to load
                print("Waiting for PDF to load...")
                await pdf_page.wait_for_load_state("load", timeout=30000)
                await asyncio.sleep(2)  # Extra wait for PDF to fully load
                
                # Download the PDF file directly from the URL
                pdf_filename = f"{reference_number}.pdf"
                pdf_path = os.path.join(save_directory, pdf_filename)
                
                print(f"Downloading PDF from URL to: {pdf_path}")
                
                # Use the page context to download the PDF
                import requests  # Keep requests sync for simplicity
                
                # Get cookies from the browser context for authenticated download
                cookies = await pdf_page.context.cookies()
                
                # Build cookie dict for requests
                cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
                
                # Download the PDF using requests with the browser's session
                # Note: requests.get is sync, but it's fast for single file downloads
                response = requests.get(pdf_url, cookies=cookie_dict, stream=True)
                
                if response.status_code == 200:
                    with open(pdf_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"PDF file downloaded successfully: {os.path.getsize(pdf_path)} bytes")
                else:
                    print(f"[WARNING] HTTP {response.status_code} when downloading PDF")
                    raise Exception(f"HTTP {response.status_code}")
                
                print(f"[SUCCESS] PDF downloaded: {pdf_path}")
                return pdf_path
                
            finally:
                # ALWAYS close the PDF tab if it was created, even if download fails
                if pdf_page is not None:
                    print("Closing PDF tab...")
                    try:
                        if pdf_page.is_closed():
                            print("PDF tab already closed")
                        else:
                            # Close with timeout to prevent hanging
                            try:
                                await asyncio.wait_for(pdf_page.close(), timeout=5.0)
                                print("PDF tab closed successfully")
                            except asyncio.TimeoutError:
                                print("[WARNING] PDF tab close timed out after 5s")
                                # Force close by finding and closing the tab
                                for ctx_page in page.context.pages:
                                    try:
                                        if ctx_page == pdf_page and not ctx_page.is_closed():
                                            print("[FORCE CLOSE] Attempting force close on stuck PDF tab")
                                            await ctx_page.close()
                                            break
                                    except:
                                        pass
                    except Exception as e:
                        print(f"[WARNING] Error closing PDF tab: {e}")
                    
                    # Final safety check: close ANY remaining PDF tabs
                    try:
                        await asyncio.sleep(0.5)  # Brief wait for close to complete
                        for ctx_page in page.context.pages:
                            if "GetPdfReport" in ctx_page.url and not ctx_page.is_closed():
                                print(f"[CLEANUP] Closing orphaned PDF tab: {ctx_page.url}")
                                try:
                                    await asyncio.wait_for(ctx_page.close(), timeout=3.0)
                                except:
                                    pass
                    except Exception as cleanup_error:
                        print(f"[WARNING] Cleanup failed: {cleanup_error}")
                
                # CRITICAL: Add buffer delay before releasing lock to ensure context stabilizes
                # This prevents the next worker from immediately opening a PDF tab while
                # the context is still processing the closure of the previous tab
                await asyncio.sleep(1.0)  # Buffer to ensure tab is fully closed and context is stable
                
                # Final verification: ensure no PDF tabs remain
                pdf_tabs_remaining = 0
                try:
                    for ctx_page in page.context.pages:
                        if "GetPdfReport" in ctx_page.url and not ctx_page.is_closed():
                            pdf_tabs_remaining += 1
                            print(f"[WARNING] PDF tab still open: {ctx_page.url}")
                    
                    if pdf_tabs_remaining > 0:
                        print(f"[WARNING] {pdf_tabs_remaining} PDF tabs still open before releasing lock")
                except Exception as e:
                    print(f"[WARNING] Could not verify PDF tabs: {e}")
                
                print("[LOCK] Released PDF download lock")
        
    except Exception as e:
        print(f"[ERROR] Failed to download PDF: {e}")
        
        # Safety check: Close any PDF tabs that might have been opened
        # Look for tabs with "GetPdfReport" in the URL (PDF viewer tabs)
        try:
            for context_page in page.context.pages:
                if "GetPdfReport" in context_page.url and not context_page.is_closed():
                    print(f"[CLEANUP] Closing orphaned PDF tab: {context_page.url}")
                    await context_page.close()
        except Exception as cleanup_error:
            print(f"[WARNING] Could not cleanup orphaned PDF tabs: {cleanup_error}")
        
        return ""
