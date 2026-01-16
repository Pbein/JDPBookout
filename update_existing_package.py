#!/usr/bin/env python3
"""
Update the existing distribution package with the fixed executable.
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

def build_fixed_executable():
    """Build just the executable with the browser path fix."""
    print("Building fixed JDPowerDownloader.exe...")
    
    # Clean previous builds
    safe_rmtree('build')
    safe_rmtree('dist')
    
    # Build PyInstaller command
    cmd = [
        'pyinstaller',
        '--onefile',
        '--windowed',  # Windowed mode for end users
        '--name=JDPowerDownloader',
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

def update_existing_package():
    """Update the existing distribution package with the fixed executable."""
    print("Updating existing distribution package...")
    
    # Build the fixed executable
    if not build_fixed_executable():
        return False
    
    # Check if executable was created
    exe_path = Path('dist/JDPowerDownloader.exe')
    if not exe_path.exists():
        print("ERROR: Fixed executable was not created")
        return False
    
    # Update the existing distribution package
    dist_dir = Path('JDPowerDownloader_Distribution')
    if not dist_dir.exists():
        print(f"ERROR: Distribution package not found: {dist_dir}")
        return False
    
    # Backup the old executable
    old_exe_path = dist_dir / 'JDPowerDownloader.exe'
    if old_exe_path.exists():
        backup_path = dist_dir / 'JDPowerDownloader_old.exe'
        shutil.copy2(old_exe_path, backup_path)
        print(f"[OK] Backed up old executable to: {backup_path}")
    
    # Copy the new executable
    shutil.copy2(exe_path, old_exe_path)
    print(f"[OK] Updated executable with browser path fix")
    
    # Update the launcher script with better error handling
    launcher_content = '''@echo off
REM JDPowerDownloader Launcher - Updated Version
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

echo Browser folder found. Launching application...

REM Launch the application
"%SCRIPT_DIR%JDPowerDownloader.exe"

echo Application has closed.
pause
'''
    
    launcher_path = dist_dir / 'Launch_JDPowerDownloader.bat'
    with open(launcher_path, 'w') as f:
        f.write(launcher_content)
    print("[OK] Updated launcher script with better error handling")
    
    print(f"\n[SUCCESS] Distribution package updated!")
    print(f"Location: {dist_dir.name}/")
    print(f"\nThe package now includes:")
    print("- Fixed executable with automatic browser path detection")
    print("- Updated launcher script with better error messages")
    print("- All existing browser files")
    
    return True

def main():
    print("Updating JDPowerDownloader Distribution Package...\n")
    success = update_existing_package()
    
    if success:
        print(f"\n[SUCCESS] Package updated successfully!")
        print("The browser path issue should now be fixed.")
    else:
        print(f"\n[FAILED] Could not update package")
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

