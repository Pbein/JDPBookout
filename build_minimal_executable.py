#!/usr/bin/env python3
"""
Build a minimal distribution package with only Chromium browser to reduce size from 1.4GB to ~360MB.
This keeps the current JDPowerDownloader_Clean_Distribution intact as a backup.
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

def build_minimal_executable():
    """Build a clean production version without console output."""
    print("Building minimal JDPowerDownloader.exe...")
    
    # Clean previous builds
    safe_rmtree('build')
    safe_rmtree('dist')
    
    # Build PyInstaller command (WITH --windowed to hide console)
    cmd = [
        'pyinstaller',
        '--onefile',
        '--windowed',  # This hides the console window
        '--name=JDPowerDownloader_Minimal',
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

def create_minimal_distribution():
    """Create a minimal distribution package with only Chromium browser."""
    print("Creating minimal distribution package...")
    
    # Create distribution directory
    dist_dir = Path('JDPowerDownloader_Minimal_Distribution')
    if dist_dir.exists():
        safe_rmtree(dist_dir)
    dist_dir.mkdir()
    
    # Copy the minimal executable
    exe_source = Path('dist/JDPowerDownloader_Minimal.exe')
    exe_dest = dist_dir / 'JDPowerDownloader.exe'
    
    if exe_source.exists():
        shutil.copy2(exe_source, exe_dest)
        print(f"[OK] Copied minimal executable: {exe_dest}")
    else:
        print(f"[ERROR] Executable not found: {exe_source}")
        return False
    
    # Create minimal ms-playwright directory
    playwright_dest = dist_dir / 'ms-playwright'
    playwright_dest.mkdir()
    
    # Copy only the necessary browser files
    source_playwright = Path('JDPowerDownloader_Clean_Distribution/ms-playwright')
    
    # Only copy Chromium-1187 (the one actually used by the app)
    chromium_source = source_playwright / 'chromium-1187'
    chromium_dest = playwright_dest / 'chromium-1187'
    
    if chromium_source.exists():
        shutil.copytree(chromium_source, chromium_dest)
        print(f"[OK] Copied Chromium-1187 browser (~360MB)")
    else:
        print(f"[ERROR] Chromium-1187 not found: {chromium_source}")
        return False
    
    # Copy winldd-1007 (small dependency, ~1MB)
    winldd_source = source_playwright / 'winldd-1007'
    winldd_dest = playwright_dest / 'winldd-1007'
    
    if winldd_source.exists():
        shutil.copytree(winldd_source, winldd_dest)
        print(f"[OK] Copied winldd-1007 dependency (~1MB)")
    else:
        print(f"[WARNING] winldd-1007 not found: {winldd_source}")
    
    # Copy .links directory if it exists (Playwright metadata)
    links_source = source_playwright / '.links'
    if links_source.exists():
        links_dest = playwright_dest / '.links'
        shutil.copytree(links_source, links_dest)
        print(f"[OK] Copied .links metadata")
    
    # Create minimal README
    readme_content = '''JDPowerDownloader - Minimal Version

This is a minimal distribution package that includes only the essential files needed to run JDPowerDownloader.
The package size has been reduced from ~1.5GB to ~360MB by including only the Chromium browser.

CONTENTS:
- JDPowerDownloader.exe: The main application (no console window)
- ms-playwright/: Minimal browser files (only Chromium-1187)

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
- Minimal size - only includes necessary Chromium browser

SIZE COMPARISON:
- Full package: ~1.5GB (includes all browsers)
- Minimal package: ~360MB (Chromium only)
- Savings: ~1.1GB (73% reduction)

TROUBLESHOOTING:
- If you get browser errors, make sure the ms-playwright folder is in the same directory as the executable
- The application will create folders in your selected download location
- This minimal version only includes Chromium browser (which is all that's needed)

For support, contact the developer.
'''
    
    with open(dist_dir / 'README.txt', 'w') as f:
        f.write(readme_content)
    print("[OK] Created minimal README")
    
    # Calculate size reduction
    total_size = sum(f.stat().st_size for f in playwright_dest.rglob('*') if f.is_file())
    total_size_mb = total_size / (1024 * 1024)
    
    print(f"\n[SUCCESS] Minimal distribution package created!")
    print(f"Location: {dist_dir.name}/")
    print(f"\nFiles included:")
    print(f"- JDPowerDownloader.exe (clean version, no console)")
    print(f"- ms-playwright/ (Chromium browser only)")
    print(f"- README.txt (user instructions)")
    print(f"\nSize reduction:")
    print(f"- Original package: ~1.5GB")
    print(f"- Minimal package: ~{total_size_mb:.0f}MB")
    print(f"- Savings: ~{(1500 - total_size_mb):.0f}MB ({(1 - total_size_mb/1500)*100:.0f}% reduction)")
    print(f"\nThis minimal package is ready for end users - no technical knowledge required!")

def main():
    """Main function to build minimal executable and create distribution."""
    print("=== JDPowerDownloader Minimal Build ===")
    print("Building minimal package with only Chromium browser...")
    print("Keeping JDPowerDownloader_Clean_Distribution as backup...")
    
    if not build_minimal_executable():
        print("Build failed!")
        return False
    
    if not create_minimal_distribution():
        print("Distribution creation failed!")
        return False
    
    print("\n🎉 Minimal build completed successfully!")
    print("The new minimal package is ready for end users!")
    print("Your original clean distribution remains intact as a backup.")
    return True

if __name__ == "__main__":
    main()

