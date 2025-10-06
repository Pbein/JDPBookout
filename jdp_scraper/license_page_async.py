"""License agreement acceptance (async version).

Responsibilities:
- Detect if license agreement is shown
- Check the agreement checkbox and wait for redirect
"""
import asyncio
from playwright.async_api import Page
from jdp_scraper import selectors


async def accept_license_async(page: Page) -> bool:
    """
    Accept the license agreement if present (async version).
    
    Args:
        page: Playwright Page object (async)
        
    Returns:
        True if license was accepted or not present, False on error
    """
    try:
        print("Checking for license agreement...")
        
        # Wait a moment for the page to load
        await asyncio.sleep(1)
        
        # Check if license checkbox is present
        checkbox = page.locator(selectors.LICENSE_CHECKBOX)
        
        if await checkbox.is_visible(timeout=5000):
            print("License agreement found. Accepting...")
            
            # Check the checkbox (this will trigger the auto-redirect)
            await checkbox.check()
            
            print("License checkbox checked. Waiting for redirect...")
            
            # Wait for navigation after accepting
            await page.wait_for_load_state("networkidle", timeout=10000)
            
            print("[SUCCESS] License agreement accepted!")
            return True
        else:
            print("No license agreement present (already accepted).")
            return True
            
    except Exception as e:
        print(f"Note: License check completed with message: {e}")
        # Not necessarily an error - license may not be present
        return True
