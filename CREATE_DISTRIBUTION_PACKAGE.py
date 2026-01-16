"""
Create the final distribution package for end users.
This script copies the executable and documentation to a clean folder.
"""
import os
import shutil
from pathlib import Path

def create_distribution():
    """Create the distribution package."""
    print("Creating JD Power PDF Downloader Distribution Package...")
    
    # Create distribution directory
    dist_dir = Path("JDPowerDownloader_v1.0")
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir()
    
    # Copy the executable
    exe_source = Path("dist/JDPowerDownloader.exe")
    if exe_source.exists():
        shutil.copy2(exe_source, dist_dir / "JDPowerDownloader.exe")
        print(f"[OK] Copied JDPowerDownloader.exe ({exe_source.stat().st_size / (1024*1024):.1f} MB)")
    else:
        print("[ERROR] JDPowerDownloader.exe not found!")
        return False
    
    # Copy documentation
    docs_to_copy = [
        "README.txt",
        "TESTING_GUIDE.md", 
        "DISTRIBUTION_PACKAGE.md",
        "FINAL_DISTRIBUTION_SUMMARY.md"
    ]
    
    for doc in docs_to_copy:
        if Path(doc).exists():
            shutil.copy2(doc, dist_dir / doc)
            print(f"[OK] Copied {doc}")
        else:
            print(f"[WARNING] {doc} not found")
    
    # Create a simple batch file for easy launching
    batch_content = """@echo off
echo Starting JD Power PDF Downloader...
echo.
echo Make sure you have:
echo 1. JD Power username and password
echo 2. A folder selected for PDF downloads
echo 3. Stable internet connection
echo.
pause
JDPowerDownloader.exe
"""
    
    with open(dist_dir / "Launch.bat", "w") as f:
        f.write(batch_content)
    print("[OK] Created Launch.bat")
    
    # Show final package contents
    print(f"\n[PACKAGE] Distribution Package Created: {dist_dir.name}/")
    print("Contents:")
    for item in sorted(dist_dir.iterdir()):
        if item.is_file():
            size = item.stat().st_size
            if size > 1024*1024:
                size_str = f"{size / (1024*1024):.1f} MB"
            elif size > 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size} bytes"
            print(f"  [FILE] {item.name} ({size_str})")
    
    print(f"\n[SUCCESS] Package ready for distribution!")
    print(f"[LOCATION] {dist_dir.absolute()}")
    print(f"[LAUNCH] Users can double-click 'Launch.bat' or 'JDPowerDownloader.exe'")
    
    return True

if __name__ == "__main__":
    success = create_distribution()
    if success:
        print("\n[SUCCESS] Distribution package created successfully!")
    else:
        print("\n[ERROR] Failed to create distribution package!")
