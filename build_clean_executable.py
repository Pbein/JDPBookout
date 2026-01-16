#!/usr/bin/env python3
"""
Build a clean production version of the executable without console output.
This will be the user-friendly version for end users.
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
            print("You may need to close any running instances of the app")

def build_clean_executable():
    """Build a clean production version without console output."""
    print("Building clean JDPowerDownloader.exe...")
    
    # Clean previous builds
    safe_rmtree('build')
    safe_rmtree('dist')
    
    # Build PyInstaller command (WITH --windowed to hide console)
    cmd = [
        'pyinstaller',
        '--onefile',
        '--windowed',  # This hides the console window
        '--name=JDPowerDownloader_Clean',
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

def create_clean_distribution():
    """Create a clean distribution package."""
    print("Creating clean distribution package...")
    
    # Create distribution directory
    dist_dir = Path('JDPowerDownloader_Clean_Distribution')
    if dist_dir.exists():
        safe_rmtree(dist_dir)
    dist_dir.mkdir()
    
    # Copy the clean executable
    exe_source = Path('dist/JDPowerDownloader_Clean.exe')
    exe_dest = dist_dir / 'JDPowerDownloader.exe'
    
    if exe_source.exists():
        shutil.copy2(exe_source, exe_dest)
        print(f"[OK] Copied clean executable: {exe_dest}")
    else:
        print(f"[ERROR] Executable not found: {exe_source}")
        return False
    
    # Copy Playwright browsers
    playwright_source = Path('JDPowerDownloader_Distribution/ms-playwright')
    playwright_dest = dist_dir / 'ms-playwright'
    
    if playwright_source.exists():
        shutil.copytree(playwright_source, playwright_dest)
        print(f"[OK] Copied Playwright browsers")
    else:
        print(f"[ERROR] Playwright browsers not found: {playwright_source}")
        return False
    
    # Create clean README
    readme_content = '''JDPowerDownloader - Clean Version

This package includes everything needed to run JDPowerDownloader on a fresh Windows computer.

CONTENTS:
- JDPowerDownloader.exe: The main application (no console window)
- ms-playwright/: Browser files required for web scraping

HOW TO USE:
1. Double-click "JDPowerDownloader.exe" to start the application
2. No terminal window will appear - just the clean GUI interface
3. Enter your credentials and select download location
4. Click Start to begin downloading PDFs

REQUIREMENTS:
- Windows 10 or later
- No additional software installation required

FEATURES:
- Clean GUI interface with no technical console output
- Automatic browser setup
- Progress tracking and download management
- Self-contained package - works on any Windows computer

TROUBLESHOOTING:
- If you get browser errors, make sure the ms-playwright folder is in the same directory as the executable
- The application will create folders in your selected download location

For support, contact the developer.
'''
    
    with open(dist_dir / 'README.txt', 'w') as f:
        f.write(readme_content)
    print("[OK] Created clean README")
    
    print(f"\n[SUCCESS] Clean distribution package created!")
    print(f"Location: {dist_dir.name}/")
    print(f"\nFiles included:")
    print(f"- JDPowerDownloader.exe (clean version, no console)")
    print(f"- ms-playwright/ (browser files)")
    print(f"- README.txt (user instructions)")
    print(f"\nThis package is ready for end users - no technical knowledge required!")

def main():
    """Main function to build clean executable and create distribution."""
    print("=== JDPowerDownloader Clean Build ===")
    print("Building user-friendly version without console output...")
    
    if not build_clean_executable():
        print("Build failed!")
        return False
    
    if not create_clean_distribution():
        print("Distribution creation failed!")
        return False
    
    print("\n🎉 Clean build completed successfully!")
    print("The new package is ready for end users!")
    return True

if __name__ == "__main__":
    main()

