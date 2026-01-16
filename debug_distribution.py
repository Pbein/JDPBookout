#!/usr/bin/env python3
"""
Debug script to test the distribution package and see what's happening.
"""

import os
import sys
import subprocess

def test_distribution():
    """Test the distribution package and debug issues."""
    print("Testing JDPowerDownloader distribution package...")
    
    # Check if distribution folder exists
    dist_dir = "JDPowerDownloader_Distribution"
    if not os.path.exists(dist_dir):
        print(f"ERROR: Distribution folder {dist_dir} not found")
        return False
    
    print(f"[OK] Found distribution folder: {dist_dir}")
    
    # Check contents
    exe_path = os.path.join(dist_dir, "JDPowerDownloader.exe")
    browser_path = os.path.join(dist_dir, "ms-playwright")
    launcher_path = os.path.join(dist_dir, "Launch_JDPowerDownloader.bat")
    
    if not os.path.exists(exe_path):
        print(f"ERROR: Executable not found: {exe_path}")
        return False
    print(f"[OK] Found executable: {exe_path}")
    
    if not os.path.exists(browser_path):
        print(f"ERROR: Browser folder not found: {browser_path}")
        return False
    print(f"[OK] Found browser folder: {browser_path}")
    
    if not os.path.exists(launcher_path):
        print(f"ERROR: Launcher script not found: {launcher_path}")
        return False
    print(f"[OK] Found launcher script: {launcher_path}")
    
    # Check browser contents
    chromium_path = os.path.join(browser_path, "chromium-1187")
    if os.path.exists(chromium_path):
        print(f"[OK] Found Chromium browser: {chromium_path}")
        chrome_exe = os.path.join(chromium_path, "chrome-win", "chrome.exe")
        if os.path.exists(chrome_exe):
            print(f"[OK] Found Chrome executable: {chrome_exe}")
        else:
            print(f"[ERROR] Chrome executable not found: {chrome_exe}")
            return False
    else:
        print(f"[ERROR] Chromium browser not found: {chromium_path}")
        return False
    
    # Test environment variable setting
    print("\nTesting environment variable setup...")
    
    # Set up environment
    env = os.environ.copy()
    env['PLAYWRIGHT_BROWSERS_PATH'] = os.path.abspath(browser_path)
    
    print(f"PLAYWRIGHT_BROWSERS_PATH = {env['PLAYWRIGHT_BROWSERS_PATH']}")
    
    # Test if browsers are accessible
    try:
        import playwright
        print(f"[OK] Playwright module available")
        
        # Try to get browser path
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser_type = p.chromium
            executable_path = browser_type.executable_path
            print(f"[INFO] Playwright expects browser at: {executable_path}")
            
            # Check if the expected path exists
            if os.path.exists(executable_path):
                print(f"[OK] Expected browser path exists")
            else:
                print(f"[ERROR] Expected browser path does not exist")
                print(f"[INFO] Available browsers in {browser_path}:")
                for item in os.listdir(browser_path):
                    print(f"  - {item}")
                return False
                
    except Exception as e:
        print(f"[ERROR] Playwright test failed: {e}")
        return False
    
    print("\n[SUCCESS] Distribution package appears to be correctly set up")
    return True

def create_fixed_launcher():
    """Create a fixed launcher script that sets the environment correctly."""
    print("\nCreating fixed launcher script...")
    
    launcher_content = '''@echo off
REM JDPowerDownloader Launcher - Fixed Version
REM This script sets up the environment and launches the application

echo Starting JDPowerDownloader...
echo Setting up browser environment...

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

REM Set Playwright browser path to the ms-playwright folder in the same directory
set PLAYWRIGHT_BROWSERS_PATH=%SCRIPT_DIR%ms-playwright

echo Browser path set to: %PLAYWRIGHT_BROWSERS_PATH%

REM Verify the browser path exists
if not exist "%PLAYWRIGHT_BROWSERS_PATH%" (
    echo ERROR: Browser folder not found at: %PLAYWRIGHT_BROWSERS_PATH%
    echo Please make sure the ms-playwright folder is in the same directory as this script.
    pause
    exit /b 1
)

echo Browser folder found. Launching application...

REM Launch the application
"%SCRIPT_DIR%JDPowerDownloader.exe"

echo Application has closed.
pause
'''
    
    dist_dir = "JDPowerDownloader_Distribution"
    launcher_path = os.path.join(dist_dir, "Launch_JDPowerDownloader_Fixed.bat")
    
    with open(launcher_path, 'w') as f:
        f.write(launcher_content)
    
    print(f"[OK] Created fixed launcher: {launcher_path}")
    return launcher_path

def main():
    print("=== JDPowerDownloader Distribution Debug Tool ===\n")
    
    # Test the distribution package
    if not test_distribution():
        print("\n[FAILED] Distribution package has issues")
        return False
    
    # Create fixed launcher
    fixed_launcher = create_fixed_launcher()
    
    print(f"\n[SUCCESS] Debug complete!")
    print(f"Try running: {fixed_launcher}")
    print("\nIf it still doesn't work, the issue might be in the application code itself.")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

