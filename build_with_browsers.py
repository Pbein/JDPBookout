#!/usr/bin/env python3
"""
Build script that creates a standalone executable with Playwright browsers bundled.
This ensures the executable works on fresh Windows machines without any dependencies.
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

def get_playwright_browser_path():
    """Get the path to Playwright browsers."""
    import platformdirs
    if os.name == 'nt':  # Windows
        return os.path.join(os.environ.get('LOCALAPPDATA', ''), 'ms-playwright')
    else:  # Unix-like
        return os.path.expanduser('~/.local/share/ms-playwright')

def main():
    print("Building JDPowerDownloader.exe with bundled browsers...")
    
    # Clean previous builds
    safe_rmtree('build')
    safe_rmtree('dist')
    
    # Get Playwright browser path
    browser_path = get_playwright_browser_path()
    print(f"Playwright browsers location: {browser_path}")
    
    if not os.path.exists(browser_path):
        print(f"ERROR: Playwright browsers not found at {browser_path}")
        print("Please run: python -m playwright install chromium --with-deps")
        return False
    
    # Check if browsers are actually installed
    chromium_path = os.path.join(browser_path, 'chromium-1187')
    if not os.path.exists(chromium_path):
        print(f"ERROR: Chromium browser not found at {chromium_path}")
        print("Please run: python -m playwright install chromium --with-deps")
        return False
    
    print(f"Found browsers at: {browser_path}")
    
    # Build PyInstaller command
    cmd = [
        'pyinstaller',
        '--onefile',
        # '--windowed',  # Commented out for debug version to see console output
        '--name=JDPowerDownloader',
        '--add-data=jdp_scraper;jdp_scraper',
        '--add-data=app;app',
        '--collect-all=playwright',
        '--hidden-import=playwright',
        '--hidden-import=playwright.async_api',
        f'--add-data={browser_path};ms-playwright',
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
    print("Command:", ' '.join(cmd))
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("PyInstaller completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"PyInstaller failed with exit code {e.returncode}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False
    
    # Check if executable was created
    exe_path = Path('dist/JDPowerDownloader.exe')
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"\nSUCCESS! Executable created.")
        print(f"Location: {exe_path}")
        print(f"Size: {size_mb:.1f} MB")
        print(f"\nTest the executable:")
        print(f"{exe_path}")
        return True
    else:
        print("ERROR: Executable was not created")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
