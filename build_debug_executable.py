#!/usr/bin/env python3
"""
Build a debug version of the executable with console output visible.
This will help us see what's happening when the app runs.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def safe_rmtree(path):
    """Safely remove directory tree, handling permission errors."""
    if os.path.exists(path):
        try:
            shutil.rmtree(path)
        except PermissionError:
            print(f"Warning: Could not remove {path} (permission denied)")
            print("You may need to close any running instances of the app")

def build_debug_executable():
    """Build a debug version of the executable with console output."""
    print("Building debug JDPowerDownloader.exe...")
    
    # Clean previous builds
    safe_rmtree('build')
    safe_rmtree('dist')
    
    # Build PyInstaller command (WITHOUT --windowed for console output)
    cmd = [
        'pyinstaller',
        '--onefile',
        # '--windowed',  # Commented out to see console output
        '--name=JDPowerDownloader_Debug',
        '--add-data=jdp_scraper;jdp_scraper',
        '--add-data=app;app',
        '--collect-all=playwright',
        '--hidden-import=playwright',
        '--hidden-import=playwright.async_api',
        '--hidden-import=asyncio',
        '--hidden-import=queue',
        '--hidden-import=threading',
        '--hidden-import=tkinter',
        '--hidden-import=tkinter.messagebox',
        '--hidden-import=tkinter.filedialog',
        '--hidden-import=tkinter.ttk',
        '--exclude-module=test_*',
        '--exclude-module=validate_*',
        '--exclude-module=tkinter.test',
        '--exclude-module=unittest',
        '--exclude-module=pydoc',
        'main_gui.py'
    ]
    
    print("Running PyInstaller...")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("PyInstaller completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"PyInstaller failed with exit code {e.returncode}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False

def create_debug_distribution():
    """Create a debug distribution package."""
    print("Creating debug distribution package...")
    
    # Build the debug executable
    if not build_debug_executable():
        return False
    
    # Check if executable was created
    exe_path = Path('dist/JDPowerDownloader_Debug.exe')
    if not exe_path.exists():
        print("ERROR: Debug executable was not created")
        return False
    
    # Get Playwright browser path
    browser_path = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'ms-playwright')
    if not os.path.exists(browser_path):
        print(f"ERROR: Playwright browsers not found at {browser_path}")
        return False
    
    # Create debug distribution directory
    dist_dir = Path('JDPowerDownloader_Debug_Distribution')
    if dist_dir.exists():
        safe_rmtree(dist_dir)
    
    dist_dir.mkdir()
    
    # Copy debug executable
    shutil.copy2(exe_path, dist_dir / 'JDPowerDownloader_Debug.exe')
    print(f"[OK] Copied debug executable")
    
    # Copy browsers
    browsers_dest = dist_dir / 'ms-playwright'
    shutil.copytree(browser_path, browsers_dest)
    print(f"[OK] Copied Playwright browsers")
    
    # Create debug launcher script
    launcher_content = '''@echo off
REM JDPowerDownloader Debug Launcher
REM This script sets up the environment and launches the debug version

echo Starting JDPowerDownloader Debug Version...
echo This version will show console output to help debug issues.

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

REM Set Playwright browser path to the ms-playwright folder in the same directory
set PLAYWRIGHT_BROWSERS_PATH=%SCRIPT_DIR%ms-playwright

echo Browser path set to: %PLAYWRIGHT_BROWSERS_PATH%

REM Verify the browser path exists
if not exist "%PLAYWRIGHT_BROWSERS_PATH%" (
    echo ERROR: Browser folder not found at: %PLAYWRIGHT_BROWSERS_PATH%
    pause
    exit /b 1
)

echo Browser folder found. Launching debug application...
echo.
echo NOTE: You will see console output that will help identify any issues.
echo.

REM Launch the debug application
"%SCRIPT_DIR%JDPowerDownloader_Debug.exe"

echo.
echo Debug application has closed.
pause
'''
    
    with open(dist_dir / 'Launch_Debug.bat', 'w') as f:
        f.write(launcher_content)
    print("[OK] Created debug launcher script")
    
    # Create README
    readme_content = '''JDPowerDownloader Debug Version

This is a debug version that shows console output to help identify issues.

HOW TO USE:
1. Double-click "Launch_Debug.bat" to start the debug version
2. Watch the console output to see what's happening
3. The GUI will still appear, but you'll also see error messages in the console

This version helps identify why the application might be completing immediately
without processing any downloads.

For support, share the console output with the developer.
'''
    
    with open(dist_dir / 'README_Debug.txt', 'w') as f:
        f.write(readme_content)
    print("[OK] Created debug README")
    
    print(f"\n[SUCCESS] Debug distribution package created!")
    print(f"Location: {dist_dir.name}/")
    print(f"\nTo test:")
    print(f"1. Copy the folder to your external location")
    print(f"2. Run Launch_Debug.bat")
    print(f"3. Watch the console output for error messages")
    
    return True

def main():
    print("Creating JDPowerDownloader Debug Distribution Package...\n")
    success = create_debug_distribution()
    
    if success:
        print(f"\n[SUCCESS] Debug package ready!")
    else:
        print(f"\n[FAILED] Could not create debug package")
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

