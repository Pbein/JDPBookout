#!/usr/bin/env python3
"""
Fix just the launcher script in the existing distribution package.
This should help with the browser path issue.
"""

import os
from pathlib import Path

def fix_launcher_script():
    """Update the launcher script with better browser path handling."""
    print("Fixing launcher script in existing distribution package...")
    
    dist_dir = Path('JDPowerDownloader_Distribution')
    if not dist_dir.exists():
        print(f"ERROR: Distribution package not found: {dist_dir}")
        return False
    
    # Create improved launcher script
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
    echo.
    echo Available files in this directory:
    dir /b
    echo.
    pause
    exit /b 1
)

echo Browser folder found. Checking for Chromium...

REM Check for Chromium specifically
set CHROMIUM_PATH=%PLAYWRIGHT_BROWSERS_PATH%\\chromium-1187\\chrome-win\\chrome.exe
if not exist "%CHROMIUM_PATH%" (
    echo ERROR: Chromium browser not found at: %CHROMIUM_PATH%
    echo Available browsers:
    dir /b "%PLAYWRIGHT_BROWSERS_PATH%"
    echo.
    pause
    exit /b 1
)

echo Chromium browser found. Launching application...

REM Launch the application
"%SCRIPT_DIR%JDPowerDownloader.exe"

echo Application has closed.
pause
'''
    
    # Update the launcher script
    launcher_path = dist_dir / 'Launch_JDPowerDownloader.bat'
    with open(launcher_path, 'w') as f:
        f.write(launcher_content)
    
    print(f"[OK] Updated launcher script: {launcher_path}")
    
    # Also create a debug launcher that shows console output
    debug_launcher_content = '''@echo off
REM JDPowerDownloader Debug Launcher
REM This version shows console output to help debug issues

echo Starting JDPowerDownloader Debug Version...
echo This version will show console output to help debug issues.
echo.

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
echo.
echo NOTE: You will see console output that will help identify any issues.
echo.

REM Launch the application (this will show console output)
REM We need to run the executable directly to see console output
cd /d "%SCRIPT_DIR%"
JDPowerDownloader.exe

echo.
echo Application has closed.
pause
'''
    
    debug_launcher_path = dist_dir / 'Launch_Debug.bat'
    with open(debug_launcher_path, 'w') as f:
        f.write(debug_launcher_content)
    
    print(f"[OK] Created debug launcher script: {debug_launcher_path}")
    
    print(f"\n[SUCCESS] Launcher scripts updated!")
    print(f"Location: {dist_dir.name}/")
    print(f"\nAvailable launchers:")
    print(f"- Launch_JDPowerDownloader.bat (normal version)")
    print(f"- Launch_Debug.bat (debug version with console output)")
    print(f"\nTry running the debug version to see what error messages appear.")
    
    return True

def main():
    print("Fixing JDPowerDownloader Distribution Package Launcher...\n")
    success = fix_launcher_script()
    
    if success:
        print(f"\n[SUCCESS] Launcher scripts fixed!")
        print("The debug version will show you exactly what's happening.")
    else:
        print(f"\n[FAILED] Could not fix launcher scripts")
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

