"""
Simple PyInstaller build script.
"""
import subprocess
import sys
import os

def main():
    print("Building JDPowerDownloader.exe...")
    
    # Clean previous builds
    import shutil
    
    def safe_rmtree(path):
        """Safely remove directory tree, handling permission errors."""
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
            except PermissionError:
                print(f"Warning: Could not remove {path} (permission denied)")
                print("You may need to close any running instances of the app")
    
    safe_rmtree('build')
    safe_rmtree('dist')
    
    # Run PyInstaller directly
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
        '--add-data=%LOCALAPPDATA%/ms-playwright;ms-playwright',
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
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("SUCCESS! Executable created.")
        print("Location: dist/JDPowerDownloader.exe")
        
        # Check file size
        exe_path = 'dist/JDPowerDownloader.exe'
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"Size: {size_mb:.1f} MB")
        
        return True
    else:
        print("ERROR: PyInstaller failed!")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\nBuild complete! Test the executable:")
        print("dist/JDPowerDownloader.exe")
    else:
        print("\nBuild failed!")
        sys.exit(1)
