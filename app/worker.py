"""
Background worker thread for running the PDF download process.
"""
import threading
import asyncio
import queue
import os
import sys
from pathlib import Path

# Add parent directory to path to import jdp_scraper
sys.path.insert(0, str(Path(__file__).parent.parent))

from jdp_scraper.orchestration_async import run_async


class DownloadWorker(threading.Thread):
    """
    Background worker thread that runs the async PDF downloader.
    
    This thread runs the download process and communicates progress
    back to the GUI via a queue.
    """
    
    def __init__(self, username, password, download_folder, max_downloads, num_workers, 
                 headless, result_queue):
        """
        Initialize the download worker.
        
        Args:
            username: JD Power username
            password: JD Power password
            download_folder: Where to save PDFs
            max_downloads: Max number of PDFs to download (0 = all)
            num_workers: Number of parallel workers
            headless: Run browser in headless mode
            result_queue: Queue for sending progress updates to GUI
        """
        super().__init__(daemon=True)
        self.username = username
        self.password = password
        self.download_folder = download_folder
        self.max_downloads = max_downloads
        self.num_workers = num_workers
        self.headless = headless
        self.result_queue = result_queue
        self._stop_event = threading.Event()
    
    def run(self):
        """
        Run the download process in this thread.
        
        This is called automatically when thread.start() is called.
        """
        try:
            # Set environment variables for the downloader
            os.environ['JD_USER'] = self.username
            os.environ['JD_PASS'] = self.password
            os.environ['HEADLESS'] = 'true' if self.headless else 'false'
            os.environ['MAX_DOWNLOADS'] = str(self.max_downloads)
            os.environ['CONCURRENT_CONTEXTS'] = str(self.num_workers)
            os.environ['BLOCK_RESOURCES'] = 'true'
            
            # Change to download folder (for config.py to use)
            original_dir = os.getcwd()
            
            # Send start message
            self.result_queue.put({
                'type': 'start',
                'message': 'Starting download process...'
            })
            
            # Run the async downloader
            asyncio.run(self._run_with_progress())
            
            # Send completion message
            self.result_queue.put({
                'type': 'complete',
                'message': 'Download complete!'
            })
            
        except Exception as e:
            # Send error message
            self.result_queue.put({
                'type': 'error',
                'message': f'Error: {str(e)}'
            })
            
            import traceback
            traceback.print_exc()
    
    async def _run_with_progress(self):
        """
        Run the async downloader with progress reporting.
        
        This wraps the main run_async function and sends progress
        updates to the GUI.
        """
        # Import here to avoid circular imports
        from jdp_scraper import checkpoint, metrics
        
        # Monkey-patch checkpoint to send updates to GUI
        original_record_success = checkpoint.ProgressCheckpoint.record_success
        original_record_failure = checkpoint.ProgressCheckpoint.record_failure
        
        async def patched_record_success(self_checkpoint, ref):
            await original_record_success(self_checkpoint, ref)
            # Send progress update
            self.result_queue.put({
                'type': 'progress',
                'processed': self_checkpoint.total_processed,
                'succeeded': self_checkpoint.total_succeeded,
                'failed': self_checkpoint.total_failed,
                'last_ref': ref,
                'status': 'success'
            })
        
        async def patched_record_failure(self_checkpoint, ref):
            await original_record_failure(self_checkpoint, ref)
            # Send progress update
            self.result_queue.put({
                'type': 'progress',
                'processed': self_checkpoint.total_processed,
                'succeeded': self_checkpoint.total_succeeded,
                'failed': self_checkpoint.total_failed,
                'last_ref': ref,
                'status': 'failure'
            })
        
        # Apply patches
        checkpoint.ProgressCheckpoint.record_success = patched_record_success
        checkpoint.ProgressCheckpoint.record_failure = patched_record_failure
        
        try:
            # Run the main async downloader
            await run_async()
        finally:
            # Restore original methods
            checkpoint.ProgressCheckpoint.record_success = original_record_success
            checkpoint.ProgressCheckpoint.record_failure = original_record_failure
    
    def stop(self):
        """
        Signal the worker to stop.
        
        Note: This is a graceful stop request. The worker may take
        time to finish current task.
        """
        self._stop_event.set()
        self.result_queue.put({
            'type': 'stop_requested',
            'message': 'Stop requested, finishing current task...'
        })
    
    def is_stopped(self):
        """Check if stop has been requested."""
        return self._stop_event.is_set()

