#!/usr/bin/env python3
"""
Debug script to help identify the correct login field selectors.
This will help us fix the "incorrect username or password" issue.
"""

import asyncio
import os
from playwright.async_api import async_playwright

async def debug_login_selectors():
    """Debug the login page to find the correct field selectors."""
    print("Debugging login page selectors...")
    print("This will help us identify the correct field IDs for username and password.")
    print()
    
    # Set up environment
    os.environ['PLAYWRIGHT_BROWSERS_PATH'] = os.path.join(os.getcwd(), 'JDPowerDownloader_Distribution', 'ms-playwright')
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Show browser for debugging
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            print("Navigating to JD Power login page...")
            await page.goto("https://valuesonline.jdpower.com", wait_until="networkidle", timeout=30000)
            
            print("Page loaded. Looking for login form elements...")
            
            # Wait a moment for the page to fully load
            await page.wait_for_timeout(3000)
            
            # Look for all input fields on the page
            print("\n=== ALL INPUT FIELDS ON THE PAGE ===")
            inputs = await page.query_selector_all('input')
            for i, input_elem in enumerate(inputs):
                input_type = await input_elem.get_attribute('type')
                input_id = await input_elem.get_attribute('id')
                input_name = await input_elem.get_attribute('name')
                input_class = await input_elem.get_attribute('class')
                placeholder = await input_elem.get_attribute('placeholder')
                
                print(f"Input {i+1}:")
                print(f"  Type: {input_type}")
                print(f"  ID: {input_id}")
                print(f"  Name: {input_name}")
                print(f"  Class: {input_class}")
                print(f"  Placeholder: {placeholder}")
                print()
            
            # Look for all buttons on the page
            print("\n=== ALL BUTTONS ON THE PAGE ===")
            buttons = await page.query_selector_all('button, input[type="submit"], input[type="button"]')
            for i, button_elem in enumerate(buttons):
                button_type = await button_elem.get_attribute('type')
                button_id = await button_elem.get_attribute('id')
                button_class = await button_elem.get_attribute('class')
                button_text = await button_elem.inner_text()
                
                print(f"Button {i+1}:")
                print(f"  Type: {button_type}")
                print(f"  ID: {button_id}")
                print(f"  Class: {button_class}")
                print(f"  Text: '{button_text}'")
                print()
            
            # Look for form elements
            print("\n=== ALL FORM ELEMENTS ===")
            forms = await page.query_selector_all('form')
            for i, form_elem in enumerate(forms):
                form_id = await form_elem.get_attribute('id')
                form_class = await form_elem.get_attribute('class')
                form_action = await form_elem.get_attribute('action')
                
                print(f"Form {i+1}:")
                print(f"  ID: {form_id}")
                print(f"  Class: {form_class}")
                print(f"  Action: {form_action}")
                print()
            
            print("\n=== DEBUGGING COMPLETE ===")
            print("Please examine the output above to identify the correct selectors.")
            print("Look for:")
            print("- Username/email input field")
            print("- Password input field")
            print("- Login/submit button")
            print()
            print("Press Enter to close the browser...")
            input()
            
        except Exception as e:
            print(f"Error during debugging: {e}")
            print("Press Enter to close the browser...")
            input()
        
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(debug_login_selectors())

