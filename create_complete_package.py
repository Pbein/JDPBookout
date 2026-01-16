#!/usr/bin/env python3
"""
Create a complete distribution package that includes:
1. The standalone executable (without browsers bundled)
2. The Playwright browsers in a separate folder
3. A launcher script that sets up the environment

This approach is better than bundling browsers into the executable because:
- Smaller executable size
- Faster build times
- Easier to update browsers separately
- More reliable on different systems
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
    if os.name == 'nt':  # Windows
        return os.path.join(os.environ.get('LOCALAPPDATA', ''), 'ms-playwright')
    else:  # Unix-like
        return os.path.expanduser('~/.local/share/ms-playwright')

def build_executable():
    """Build the standalone executable without browsers."""
    print("Building JDPowerDownloader.exe...")
    
    # Clean previous builds
    safe_rmtree('build')
    safe_rmtree('dist')
    
    # Build PyInstaller command (without browsers)
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

def create_distribution_package():
    """Create a complete distribution package."""
    print("Creating distribution package...")
    
    # Build the executable first
    if not build_executable():
        return False
    
    # Check if executable was created
    exe_path = Path('dist/JDPowerDownloader.exe')
    if not exe_path.exists():
        print("ERROR: Executable was not created")
        return False
    
    # Get Playwright browser path
    browser_path = get_playwright_browser_path()
    print(f"Playwright browsers location: {browser_path}")
    
    if not os.path.exists(browser_path):
        print(f"ERROR: Playwright browsers not found at {browser_path}")
        print("Please run: python -m playwright install chromium --with-deps")
        return False
    
    # Create distribution directory
    dist_dir = Path('JDPowerDownloader_Distribution')
    if dist_dir.exists():
        safe_rmtree(dist_dir)
    
    dist_dir.mkdir()
    
    # Copy executable
    shutil.copy2(exe_path, dist_dir / 'JDPowerDownloader.exe')
    print(f"[OK] Copied JDPowerDownloader.exe")
    
    # Copy browsers
    browsers_dest = dist_dir / 'ms-playwright'
    shutil.copytree(browser_path, browsers_dest)
    print(f"[OK] Copied Playwright browsers ({sum(f.stat().st_size for f in browsers_dest.rglob('*') if f.is_file()) / (1024*1024):.1f} MB)")
    
    # Create launcher script
    launcher_content = '''@echo off
REM JDPowerDownloader Launcher
REM This script sets up the environment and launches the application

echo Starting JDPowerDownloader...

REM Set Playwright browser path
set PLAYWRIGHT_BROWSERS_PATH=%~dp0ms-playwright

REM Launch the application
"%~dp0JDPowerDownloader.exe"

pause
'''
    
    with open(dist_dir / 'Launch_JDPowerDownloader.bat', 'w') as f:
        f.write(launcher_content)
    print("[OK] Created launcher script")
    
    # Create README
    readme_content = '''JDPowerDownloader - Complete Package

This package includes everything needed to run JDPowerDownloader on a fresh Windows computer.

CONTENTS:
- JDPowerDownloader.exe: The main application
- ms-playwright/: Browser files required for web scraping
- Launch_JDPowerDownloader.bat: Easy launcher script

HOW TO USE:
1. Double-click "Launch_JDPowerDownloader.bat" to start the application
2. Or run "JDPowerDownloader.exe" directly

REQUIREMENTS:
- Windows 10 or later
- No additional software installation required

TROUBLESHOOTING:
- If you get browser errors, make sure the ms-playwright folder is in the same directory as the executable
- The application will create folders in your selected download location

For support, contact the developer.
'''
    
    with open(dist_dir / 'README.txt', 'w') as f:
        f.write(readme_content)
    print("[OK] Created README")
    
    # Calculate total size
    total_size = sum(f.stat().st_size for f in dist_dir.rglob('*') if f.is_file())
    
    print(f"\n[SUCCESS] Distribution package created!")
    print(f"Location: {dist_dir.name}/")
    print(f"Total size: {total_size / (1024*1024):.1f} MB")
    print(f"\nPackage contents:")
    for item in sorted(dist_dir.rglob('*')):
        if item.is_file():
            rel_path = item.relative_to(dist_dir)
            size_mb = item.stat().st_size / (1024*1024)
            print(f"  {rel_path} ({size_mb:.1f} MB)")
    
    return True

def main():
    print("Creating complete JDPowerDownloader distribution package...")
    success = create_distribution_package()
    
    if success:
        print(f"\n[SUCCESS] Package ready for distribution!")
        print("The package includes:")
        print("- Standalone executable")
        print("- Playwright browsers")
        print("- Launcher script")
        print("- README with instructions")
    else:
        print("\n[FAILED] Could not create distribution package")
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

