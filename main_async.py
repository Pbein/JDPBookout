"""
Entry point for parallel PDF downloader using async Playwright.

This script uses asyncio.run() which BLOCKS until all processing is complete.
The script will NOT exit until all work is done.
"""
import asyncio
from jdp_scraper.orchestration_async import run_async


def main():
    """
    Main entry point - BLOCKING execution.
    
    This function blocks until run_async() completes all work.
    """
    try:
        print("[STARTUP] Starting parallel PDF downloader...")
        print("[STARTUP] This script will block until all processing is complete")
        print("[STARTUP] Press Ctrl+C to interrupt\n")
        
        # This BLOCKS until run_async() completes
        asyncio.run(run_async())
        
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] User interrupted the process")
        print("[INTERRUPTED] Shutting down gracefully...")
        
    except Exception as e:
        print(f"\n[FATAL ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n[EXIT] Program terminated")


if __name__ == "__main__":
    main()  # Blocks here until complete
