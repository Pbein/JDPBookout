"""
Test script for parallel processing with 30 vehicles and 5 workers.

This test validates the parallel processing system with optimal worker count.
"""
import os
import sys

# Set test configuration
os.environ["MAX_DOWNLOADS"] = "30"
os.environ["CONCURRENT_CONTEXTS"] = "5"  # Optimal for 30 vehicles
os.environ["HEADLESS"] = "false"  # Visible for monitoring
os.environ["BLOCK_RESOURCES"] = "false"  # Show styling for visibility

print("="*60)
print("PARALLEL PROCESSING TEST - 30 VEHICLES, 5 WORKERS")
print("="*60)
print("Configuration:")
print(f"  MAX_DOWNLOADS: {os.environ['MAX_DOWNLOADS']}")
print(f"  CONCURRENT_WORKERS: {os.environ['CONCURRENT_CONTEXTS']}")
print(f"  HEADLESS: {os.environ['HEADLESS']}")
print(f"  BLOCK_RESOURCES: {os.environ['BLOCK_RESOURCES']}")
print("="*60)
print()
print("Architecture:")
print("  - Single browser context (one login)")
print("  - 5 worker pages (tabs) sharing session")
print("  - Task queue for coordination")
print("  - Sequential access to inventory (no interference)")
print()
print("Expected Results:")
print("  - All 5 workers initialize successfully")
print("  - Vehicles processed in parallel (5 at a time)")
print("  - 28-30 PDFs downloaded (93-100% success rate)")
print("  - No duplicate downloads")
print("  - No page interference")
print("  - Script blocks until complete")
print("  - Runtime: ~3-4 minutes")
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
        print("\nNext Steps:")
        print("  1. Check downloads/10-05-2025/ for 30 PDFs")
        print("  2. Review tracking.json for completion status")
        print("  3. Check metrics.json for performance data")
        print("  4. Verify no duplicate downloads occurred")
        print("="*60)
    except Exception as e:
        print("\n" + "="*60)
        print(f"[TEST FAILED] Error: {e}")
        print("="*60)
        sys.exit(1)
