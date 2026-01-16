"""
JD Power PDF Downloader - Desktop Application
Entry point for the GUI version.
"""
import tkinter as tk
from tkinter import messagebox
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.gui import JDPowerApp


def check_dependencies():
    """
    Check if required dependencies are installed.
    
    Returns:
        tuple: (success, error_message)
    """
    try:
        import playwright
    except ImportError:
        return False, ("Playwright is not installed.\n\n"
                      "Please run: pip install playwright\n"
                      "Then: playwright install chromium")
    
    # Keyring check removed - not required for standalone executable
    
    # Cryptography check removed - not required for standalone executable
    
    return True, ""


def main():
    """Main entry point for the GUI application."""
    # Check dependencies
    success, error_msg = check_dependencies()
    if not success:
        root = tk.Tk()
        root.withdraw()  # Hide main window
        messagebox.showerror("Missing Dependencies", error_msg)
        sys.exit(1)
    
    # Create and run the GUI
    try:
        root = tk.Tk()
        app = JDPowerApp(root)
        root.mainloop()
    except KeyboardInterrupt:
        print("\nApplication closed by user")
        sys.exit(0)
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred:\n\n{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

