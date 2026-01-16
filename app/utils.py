"""
Utility functions for the GUI application.
"""
import os
from datetime import timedelta


def validate_credentials(username, password):
    """
    Validate that credentials are not empty.
    
    Args:
        username: Username string
        password: Password string
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not username or not username.strip():
        return False, "Username cannot be empty"
    
    if not password or not password.strip():
        return False, "Password cannot be empty"
    
    return True, ""


def validate_folder(folder_path):
    """
    Validate that folder exists and is writable.
    
    Args:
        folder_path: Path to folder
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not folder_path or not folder_path.strip():
        return False, "Please select a download folder"
    
    # Try to create folder if it doesn't exist
    try:
        os.makedirs(folder_path, exist_ok=True)
    except Exception as e:
        return False, f"Cannot create folder: {e}"
    
    # Check if writable
    if not os.access(folder_path, os.W_OK):
        return False, "Folder is not writable. Please choose a different location."
    
    return True, ""


def format_time(seconds):
    """
    Format seconds as human-readable time.
    
    Args:
        seconds: Number of seconds
    
    Returns:
        str: Formatted time string (e.g., "1h 30m 45s")
    """
    if seconds < 0:
        return "Unknown"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def format_progress(current, total):
    """
    Format progress as "X/Y (Z%)".
    
    Args:
        current: Current progress
        total: Total items
    
    Returns:
        str: Formatted progress string
    """
    if total == 0:
        return "0/0 (0%)"
    
    percentage = (current / total) * 100
    return f"{current}/{total} ({percentage:.1f}%)"


def calculate_speed(processed, elapsed_seconds):
    """
    Calculate processing speed in items per hour.
    
    Args:
        processed: Number of items processed
        elapsed_seconds: Time elapsed in seconds
    
    Returns:
        float: Items per hour
    """
    if elapsed_seconds == 0:
        return 0.0
    
    items_per_second = processed / elapsed_seconds
    items_per_hour = items_per_second * 3600
    return items_per_hour


def estimate_remaining_time(processed, total, elapsed_seconds):
    """
    Estimate remaining time based on current progress.
    
    Args:
        processed: Number of items processed
        total: Total items
        elapsed_seconds: Time elapsed in seconds
    
    Returns:
        int: Estimated remaining seconds
    """
    if processed == 0:
        return -1  # Unknown
    
    remaining_items = total - processed
    avg_time_per_item = elapsed_seconds / processed
    estimated_seconds = remaining_items * avg_time_per_item
    
    return int(estimated_seconds)

