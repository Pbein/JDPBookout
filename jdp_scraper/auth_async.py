"""Login flow using Playwright async API.

Responsibilities:
- Navigate to login URL
- Enter credentials from env
- Submit and verify login success
"""
from playwright.async_api import Page
from jdp_scraper import config, selectors


async def login_async(page: Page, username: str = None, password: str = None) -> bool:
    """
    Perform login on the JD Power Values Online site (async version).
    
    Args:
        page: Playwright Page object (async)
        username: Username to use (overrides environment variable)
        password: Password to use (overrides environment variable)
        
    Returns:
        True if login successful, False otherwise
    """
    try:
        print("Starting login process...")
        
        # Use provided credentials or fall back to environment variables
        login_username = username if username is not None else config.JD_USER
        login_password = password if password is not None else config.JD_PASS
        
        print(f"DEBUG: Using username: '{login_username}'")
        print(f"DEBUG: Using password: {'*' * len(login_password) if login_password else 'EMPTY'}")
        
        # Wait for login form to be visible
        print(f"Waiting for username input: {selectors.USERNAME_INPUT}")
        await page.wait_for_selector(selectors.USERNAME_INPUT, state="visible", timeout=10000)
        
        # Fill in username
        print(f"Entering username: {login_username}")
        await page.fill(selectors.USERNAME_INPUT, login_username)
        
        # Fill in password
        print("Entering password...")
        await page.fill(selectors.PASSWORD_INPUT, login_password)
        
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
