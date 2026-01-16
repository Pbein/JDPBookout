"""
Simple build script to create executable without user interaction.
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def main():
    print("Building JDPowerDownloader.exe...")
    
    # Clean previous builds
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    
    # Create clean build directory
    build_dir = Path('build_temp')
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir()
    
    # Copy essential files
    print("Copying essential files...")
    
    # Copy jdp_scraper
    shutil.copytree('jdp_scraper', build_dir / 'jdp_scraper')
    
    # Copy app
    shutil.copytree('app', build_dir / 'app')
    
    # Copy main files
    shutil.copy('main_gui.py', build_dir / 'main_gui.py')
    shutil.copy('requirements.txt', build_dir / 'requirements.txt')
    
    # Change to build directory
    original_dir = os.getcwd()
    os.chdir(build_dir)
    
    try:
        # Run PyInstaller
        print("Running PyInstaller...")
        cmd = [
            'pyinstaller',
            '--onefile',
            '--windowed',
            '--name=JDPowerDownloader',
            '--add-data=jdp_scraper;jdp_scraper',
            '--add-data=app;app',
            '--hidden-import=playwright',
            '--hidden-import=playwright._impl._api_types',
            '--hidden-import=playwright.async_api',
            '--hidden-import=asyncio',
            '--hidden-import=keyring',
            '--hidden-import=keyring.backends.Windows',
            '--hidden-import=cryptography',
            '--hidden-import=queue',
            '--hidden-import=threading',
            '--exclude-module=test_*',
            '--exclude-module=validate_*',
            '--exclude-module=tkinter.test',
            '--exclude-module=unittest',
            '--exclude-module=pydoc',
            'main_gui.py'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("SUCCESS! Executable created.")
            print("Location: dist/JDPowerDownloader.exe")
            
            # Check file size
            exe_path = Path('dist/JDPowerDownloader.exe')
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"Size: {size_mb:.1f} MB")
            
            return True
        else:
            print("ERROR: PyInstaller failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    finally:
        # Return to original directory
        os.chdir(original_dir)
        
        # Clean up build directory
        if build_dir.exists():
            shutil.rmtree(build_dir)

if __name__ == "__main__":
    success = main()
    if success:
        print("\nBuild complete! Test the executable:")
        print("dist/JDPowerDownloader.exe")
    else:
        print("\nBuild failed!")
        sys.exit(1)
