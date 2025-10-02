"""Login flow using Playwright sync API.

Responsibilities:
- Navigate to login URL
- Enter credentials from env
- Submit and verify login success
"""
from playwright.sync_api import Page
from jdp_scraper import config, selectors


def login(page: Page) -> bool:
    """
    Perform login on the JD Power Values Online site.
    
    Args:
        page: Playwright Page object
        
    Returns:
        True if login successful, False otherwise
    """
    try:
        print("Starting login process...")
        
        # Debug: Show what we're using
        print(f"DEBUG - Username from config: '{config.JD_USER}' (length: {len(config.JD_USER)})")
        print(f"DEBUG - Password from config: {'*' * len(config.JD_PASS)} (length: {len(config.JD_PASS)})")
        
        # Wait for login form to be visible
        page.wait_for_selector(selectors.USERNAME_INPUT, state="visible")
        
        # Fill in username
        print(f"Entering username: {config.JD_USER}")
        page.fill(selectors.USERNAME_INPUT, config.JD_USER)
        
        # Verify username was filled
        username_value = page.input_value(selectors.USERNAME_INPUT)
        print(f"DEBUG - Username field value after fill: '{username_value}'")
        
        # Fill in password
        print("Entering password...")
        page.fill(selectors.PASSWORD_INPUT, config.JD_PASS)
        
        # Click login button
        print("Clicking login button...")
        page.click(selectors.LOGIN_BUTTON)
        
        # Wait for navigation after login (adjust as needed)
        print("Waiting for login to complete...")
        page.wait_for_load_state("networkidle")
        
        print("[SUCCESS] Login completed successfully!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Login failed: {e}")
        return False

