"""
Build script for JD Power PDF Downloader Desktop Application

This script:
1. Creates a clean build directory with only essential files
2. Removes all development/test artifacts
3. Runs PyInstaller to create standalone executable
4. Tests the output

Usage:
    python build_app.py
"""
import os
import shutil
import sys
from pathlib import Path

# Colors for terminal output (Windows compatible)
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(msg):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{msg}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")

def print_success(msg):
    print(f"{Colors.OKGREEN}✓ {msg}{Colors.ENDC}")

def print_error(msg):
    print(f"{Colors.FAIL}✗ {msg}{Colors.ENDC}")

def print_warning(msg):
    print(f"{Colors.WARNING}⚠ {msg}{Colors.ENDC}")

def print_info(msg):
    print(f"{Colors.OKBLUE}ℹ {msg}{Colors.ENDC}")


# Essential files to include
ESSENTIAL_FILES = {
    'jdp_scraper': [
        '__init__.py',
        'async_utils.py',
        'auth_async.py',
        'checkpoint.py',
        'config.py',
        'downloads.py',
        'inventory_async.py',
        'license_page_async.py',
        'metrics.py',
        'orchestration_async.py',
        'page_pool.py',
        'selectors.py',
        'task_queue.py',
        'vehicle_async.py',
    ],
    'app': [
        # Will be created during development
        # '__init__.py',
        # 'gui.py',
        # 'settings.py',
        # 'worker.py',
        # 'utils.py',
    ],
    'root': [
        'main_async.py',  # Keep as backup CLI
        'requirements.txt',
    ]
}

def clean_build_dir():
    """Remove existing build directories."""
    print_header("Step 1: Cleaning Build Directory")
    
    dirs_to_remove = ['build', 'dist', 'build_temp']
    
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            print_info(f"Removing {dir_name}/...")
            shutil.rmtree(dir_name)
            print_success(f"Removed {dir_name}/")
    
    print_success("Build directory cleaned")


def create_build_structure():
    """Create clean build directory with only essential files."""
    print_header("Step 2: Creating Clean Build Structure")
    
    build_dir = Path('build_temp')
    build_dir.mkdir(exist_ok=True)
    
    # Copy essential jdp_scraper files
    print_info("Copying essential jdp_scraper files...")
    src_dir = build_dir / 'jdp_scraper'
    src_dir.mkdir(exist_ok=True)
    
    copied_count = 0
    for file in ESSENTIAL_FILES['jdp_scraper']:
        src = Path('jdp_scraper') / file
        dst = src_dir / file
        if src.exists():
            shutil.copy2(src, dst)
            copied_count += 1
        else:
            print_warning(f"File not found: {src}")
    
    print_success(f"Copied {copied_count} jdp_scraper files")
    
    # Copy app files (if they exist)
    if os.path.exists('app'):
        print_info("Copying app/ GUI files...")
        app_dst = build_dir / 'app'
        shutil.copytree('app', app_dst, dirs_exist_ok=True)
        print_success("Copied app/ directory")
    else:
        print_warning("app/ directory not found (will be created during GUI development)")
    
    # Copy root files
    print_info("Copying root files...")
    for file in ESSENTIAL_FILES['root']:
        src = Path(file)
        dst = build_dir / file
        if src.exists():
            shutil.copy2(src, dst)
            print_success(f"Copied {file}")
        else:
            print_warning(f"File not found: {file}")
    
    # Copy GUI entry point (if exists)
    if os.path.exists('main_gui.py'):
        shutil.copy2('main_gui.py', build_dir / 'main_gui.py')
        print_success("Copied main_gui.py")
    else:
        print_warning("main_gui.py not found (will be created during GUI development)")
    
    print_success("Build structure created successfully")
    return build_dir


def create_spec_file(build_dir):
    """Create PyInstaller spec file."""
    print_header("Step 3: Creating PyInstaller Spec File")
    
    spec_content = """
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main_gui.py'],  # or main_async.py for CLI version
    pathex=[],
    binaries=[],
    datas=[
        ('jdp_scraper', 'jdp_scraper'),
        ('app', 'app'),
    ],
    hiddenimports=[
        'playwright',
        'playwright._impl._api_types',
        'playwright.async_api',
        'asyncio',
        'keyring',
        'cryptography',
        'dotenv',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'test_*',
        'validate_*',
        'tkinter.test',
        'unittest',
        'xml',
        'pydoc',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='JDPowerDownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True for CLI version, False for GUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app_icon.ico',  # Add icon here when available
)
"""
    
    spec_path = build_dir / 'JDPowerDownloader.spec'
    with open(spec_path, 'w') as f:
        f.write(spec_content)
    
    print_success(f"Created spec file: {spec_path}")
    return spec_path


def show_build_summary():
    """Show what will be included/excluded."""
    print_header("Build Configuration Summary")
    
    print_info("Files to INCLUDE:")
    total_files = 0
    for category, files in ESSENTIAL_FILES.items():
        print(f"\n  {category}/:")
        for file in files:
            print(f"    ✓ {file}")
            total_files += 1
    
    print(f"\n{Colors.OKGREEN}Total essential files: {total_files}{Colors.ENDC}")
    
    print_info("\nFiles to EXCLUDE:")
    exclude_patterns = [
        'test_*.py',
        'validate_*.py',
        'downloads/',
        'data/',
        'docs/ (except USER_GUIDE)',
        '__pycache__/',
        '.git/',
        '.venv/',
        'Old sync files (auth.py, inventory.py, etc.)',
    ]
    
    for pattern in exclude_patterns:
        print(f"    ✗ {pattern}")
    
    print(f"\n{Colors.WARNING}Estimated .exe size: 15-50 MB (without Playwright){Colors.ENDC}")
    print(f"{Colors.WARNING}                      300-400 MB (with Playwright bundled){Colors.ENDC}")


def run_pyinstaller(spec_path):
    """Run PyInstaller with the spec file."""
    print_header("Step 4: Running PyInstaller")
    
    print_info("This may take 5-10 minutes...")
    print_info("Building standalone executable...\n")
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print_error("PyInstaller not installed!")
        print_info("Install it with: pip install pyinstaller")
        return False
    
    # Run PyInstaller
    import subprocess
    
    result = subprocess.run(
        ['pyinstaller', str(spec_path), '--clean'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print_success("PyInstaller build completed successfully!")
        return True
    else:
        print_error("PyInstaller build failed!")
        print(result.stderr)
        return False


def show_final_output():
    """Show where the output is and next steps."""
    print_header("Build Complete!")
    
    exe_path = Path('dist') / 'JDPowerDownloader.exe'
    
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print_success(f"Executable created: {exe_path}")
        print_success(f"Size: {size_mb:.1f} MB")
        
        print_info("\nNext Steps:")
        print("  1. Test the .exe on this machine")
        print("  2. Copy to a clean Windows PC (no Python installed)")
        print("  3. Test all features")
        print("  4. Distribute to end users")
        
        print_info("\nFirst Run:")
        print("  - Playwright will be downloaded (~200 MB)")
        print("  - Takes 2-5 minutes")
        print("  - Only happens once")
        
    else:
        print_error("Executable not found!")
        print_info("Check the build output above for errors")


def main():
    """Main build process."""
    print_header("JD Power PDF Downloader - Build Script")
    
    print_info("This script creates a standalone .exe for end users")
    print_info("Excluding all development/test files\n")
    
    # Show what will be built
    show_build_summary()
    
    # Confirm
    response = input(f"\n{Colors.OKBLUE}Continue with build? (y/n): {Colors.ENDC}")
    if response.lower() != 'y':
        print_warning("Build cancelled")
        return
    
    try:
        # Step 1: Clean
        clean_build_dir()
        
        # Step 2: Create clean structure
        build_dir = create_build_structure()
        
        # Step 3: Create spec file
        spec_path = create_spec_file(build_dir)
        
        # Step 4: Run PyInstaller
        # Note: Uncomment when ready to build
        print_warning("\nPyInstaller build is commented out until GUI is complete")
        print_info("Uncomment 'run_pyinstaller()' in build_app.py when ready")
        
        # success = run_pyinstaller(spec_path)
        
        # if success:
        #     show_final_output()
        # else:
        #     print_error("Build failed")
        #     sys.exit(1)
        
        print_success("\nBuild structure ready!")
        print_info(f"Files prepared in: {build_dir}/")
        
    except Exception as e:
        print_error(f"Build failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

