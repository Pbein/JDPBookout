"""Login flow using Playwright async API.

Responsibilities:
- Navigate to login URL
- Enter credentials from env
- Submit and verify login success
"""
from playwright.async_api import Page
from jdp_scraper import config, selectors


async def login_async(page: Page) -> bool:
    """
    Perform login on the JD Power Values Online site (async version).
    
    Args:
        page: Playwright Page object (async)
        
    Returns:
        True if login successful, False otherwise
    """
    try:
        print("Starting login process...")
        
        # Wait for login form to be visible
        await page.wait_for_selector(selectors.USERNAME_INPUT, state="visible")
        
        # Fill in username
        print(f"Entering username: {config.JD_USER}")
        await page.fill(selectors.USERNAME_INPUT, config.JD_USER)
        
        # Fill in password
        print("Entering password...")
        await page.fill(selectors.PASSWORD_INPUT, config.JD_PASS)
        
        # Click login button
        print("Clicking login button...")
        await page.click(selectors.LOGIN_BUTTON)
        
        # Wait for navigation after login
        print("Waiting for login to complete...")
        await page.wait_for_load_state("networkidle")
        
        print("[SUCCESS] Login completed successfully!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Login failed: {e}")
        return False
