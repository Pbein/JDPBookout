"""
Test script for parallel processing with 10 vehicles and 2 contexts.

This is a minimal test to verify the async system works correctly.
"""
import os
import sys

# Set test configuration
os.environ["MAX_DOWNLOADS"] = "10"
os.environ["CONCURRENT_CONTEXTS"] = "2"  # Number of pages (tabs)
os.environ["HEADLESS"] = "false"  # Visible for testing
os.environ["BLOCK_RESOURCES"] = "false"  # Show styling for visibility

print("="*60)
print("PARALLEL PROCESSING TEST - 10 VEHICLES, 2 PAGES")
print("="*60)
print("Configuration:")
print(f"  MAX_DOWNLOADS: {os.environ['MAX_DOWNLOADS']}")
print(f"  CONCURRENT_PAGES: {os.environ['CONCURRENT_CONTEXTS']}")
print(f"  HEADLESS: {os.environ['HEADLESS']}")
print(f"  BLOCK_RESOURCES: {os.environ['BLOCK_RESOURCES']}")
print("="*60)
print("Architecture: Single context, multiple pages (tabs)")
print("Expected: Single login, all pages share session")
print("="*60)
print()

# Import and run
from main_async import main

if __name__ == "__main__":
    try:
        main()
        print("\n" + "="*60)
        print("[TEST COMPLETE] Test finished successfully")
        print("="*60)
    except Exception as e:
        print("\n" + "="*60)
        print(f"[TEST FAILED] Error: {e}")
        print("="*60)
        sys.exit(1)
