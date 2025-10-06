"""
Settings management and credential storage for the GUI application.
"""
import os
import json
import keyring
from pathlib import Path


# Application name for credential storage
APP_NAME = "JDPowerDownloader"

# Settings file location
SETTINGS_DIR = Path.home() / "AppData" / "Local" / APP_NAME
SETTINGS_FILE = SETTINGS_DIR / "settings.json"


def ensure_settings_dir():
    """Create settings directory if it doesn't exist."""
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)


def save_credentials(username, password):
    """
    Save credentials securely in Windows Credential Manager.
    
    Args:
        username: Username to save
        password: Password to save
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        keyring.set_password(APP_NAME, username, password)
        return True
    except Exception as e:
        print(f"Error saving credentials: {e}")
        return False


def load_credentials(username):
    """
    Load credentials from Windows Credential Manager.
    
    Args:
        username: Username to load password for
    
    Returns:
        str or None: Password if found, None otherwise
    """
    try:
        return keyring.get_password(APP_NAME, username)
    except Exception as e:
        print(f"Error loading credentials: {e}")
        return None


def delete_credentials(username):
    """
    Delete credentials from Windows Credential Manager.
    
    Args:
        username: Username to delete
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        keyring.delete_password(APP_NAME, username)
        return True
    except Exception as e:
        print(f"Error deleting credentials: {e}")
        return False


def save_preferences(preferences):
    """
    Save user preferences to JSON file.
    
    Args:
        preferences: Dictionary of preferences to save
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        ensure_settings_dir()
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(preferences, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving preferences: {e}")
        return False


def load_preferences():
    """
    Load user preferences from JSON file.
    
    Returns:
        dict: Preferences dictionary with defaults if file doesn't exist
    """
    defaults = {
        "last_username": "",
        "download_folder": str(Path.home() / "Downloads" / "JD_Power_PDFs"),
        "save_credentials": False,
        "max_downloads": 0,
        "num_workers": 5,
        "headless": True,
        "window_width": 650,
        "window_height": 750,
    }
    
    try:
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, 'r') as f:
                saved_prefs = json.load(f)
                # Merge with defaults (in case new settings were added)
                defaults.update(saved_prefs)
    except Exception as e:
        print(f"Error loading preferences: {e}")
    
    return defaults


def get_last_username():
    """
    Get the last used username.
    
    Returns:
        str: Last username or empty string
    """
    prefs = load_preferences()
    return prefs.get("last_username", "")


def save_last_username(username):
    """
    Save the last used username.
    
    Args:
        username: Username to save
    """
    prefs = load_preferences()
    prefs["last_username"] = username
    save_preferences(prefs)

