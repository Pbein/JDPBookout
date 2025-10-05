"""Checkpoint and recovery system for robust long-running downloads.

This module provides mechanisms to:
- Save progress checkpoints after each successful download
- Detect when the automation is stuck (consecutive failures)
- Recover from failures by restarting from the last good state
- Validate that forward progress is being made
"""
import json
import os
from datetime import datetime
from typing import Dict, Optional
from jdp_scraper import config


class ProgressCheckpoint:
    """Manages checkpoints for resumable downloads."""
    
    def __init__(self, checkpoint_file: str = None):
        """
        Initialize checkpoint manager.
        
        Args:
            checkpoint_file: Path to checkpoint file (default: in RUN_DIR)
        """
        if checkpoint_file is None:
            checkpoint_file = os.path.join(config.RUN_DIR, "checkpoint.json")
        
        self.checkpoint_file = checkpoint_file
        self.consecutive_failures = 0
        self.last_successful_ref = None
        self.total_processed = 0
        self.total_succeeded = 0
        self.total_failed = 0
        self.started_at = datetime.utcnow().isoformat()
        self.last_checkpoint_at = None
        
        # Load existing checkpoint if it exists
        self.load()
    
    def load(self) -> bool:
        """
        Load checkpoint from disk if it exists.
        
        Returns:
            True if checkpoint was loaded, False if starting fresh
        """
        try:
            if os.path.exists(self.checkpoint_file):
                with open(self.checkpoint_file, 'r') as f:
                    data = json.load(f)
                    self.consecutive_failures = data.get('consecutive_failures', 0)
                    self.last_successful_ref = data.get('last_successful_ref')
                    self.total_processed = data.get('total_processed', 0)
                    self.total_succeeded = data.get('total_succeeded', 0)
                    self.total_failed = data.get('total_failed', 0)
                    self.started_at = data.get('started_at', self.started_at)
                    self.last_checkpoint_at = data.get('last_checkpoint_at')
                    print(f"[CHECKPOINT] Loaded existing checkpoint")
                    print(f"[CHECKPOINT] Last successful: {self.last_successful_ref}")
                    print(f"[CHECKPOINT] Progress: {self.total_succeeded} succeeded, {self.total_failed} failed")
                    return True
        except Exception as e:
            print(f"[CHECKPOINT] Could not load checkpoint: {e}")
        
        return False
    
    def save(self) -> bool:
        """
        Save current checkpoint to disk.
        
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            os.makedirs(os.path.dirname(self.checkpoint_file), exist_ok=True)
            
            data = {
                'consecutive_failures': self.consecutive_failures,
                'last_successful_ref': self.last_successful_ref,
                'total_processed': self.total_processed,
                'total_succeeded': self.total_succeeded,
                'total_failed': self.total_failed,
                'started_at': self.started_at,
                'last_checkpoint_at': datetime.utcnow().isoformat()
            }
            
            with open(self.checkpoint_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.last_checkpoint_at = data['last_checkpoint_at']
            return True
            
        except Exception as e:
            print(f"[CHECKPOINT] Could not save checkpoint: {e}")
            return False
    
    def record_success(self, reference_number: str) -> None:
        """
        Record a successful download.
        
        Args:
            reference_number: The reference number that succeeded
        """
        self.consecutive_failures = 0
        self.last_successful_ref = reference_number
        self.total_processed += 1
        self.total_succeeded += 1
        self.save()
    
    def record_failure(self, reference_number: str) -> None:
        """
        Record a failed download.
        
        Args:
            reference_number: The reference number that failed
        """
        self.consecutive_failures += 1
        self.total_processed += 1
        self.total_failed += 1
        self.save()
    
    def is_stuck(self, threshold: int = 5) -> bool:
        """
        Check if we're stuck (too many consecutive failures).
        
        Args:
            threshold: Number of consecutive failures to consider "stuck"
            
        Returns:
            True if stuck, False otherwise
        """
        return self.consecutive_failures >= threshold
    
    def get_status(self) -> Dict[str, any]:
        """
        Get current checkpoint status.
        
        Returns:
            Dictionary with checkpoint information
        """
        return {
            'consecutive_failures': self.consecutive_failures,
            'last_successful_ref': self.last_successful_ref,
            'total_processed': self.total_processed,
            'total_succeeded': self.total_succeeded,
            'total_failed': self.total_failed,
            'success_rate': (self.total_succeeded / self.total_processed * 100) if self.total_processed > 0 else 0,
            'is_stuck': self.is_stuck()
        }
    
    def print_status(self) -> None:
        """Print checkpoint status to console."""
        status = self.get_status()
        print(f"\n{'='*60}")
        print(f"CHECKPOINT STATUS")
        print(f"{'='*60}")
        print(f"Total processed    : {status['total_processed']}")
        print(f"Succeeded          : {status['total_succeeded']}")
        print(f"Failed             : {status['total_failed']}")
        print(f"Success rate       : {status['success_rate']:.1f}%")
        print(f"Consecutive fails  : {status['consecutive_failures']}")
        print(f"Last successful    : {status['last_successful_ref']}")
        print(f"Status             : {'⚠️ STUCK' if status['is_stuck'] else '✓ OK'}")
        print(f"{'='*60}\n")
    
    def reset_if_stuck(self) -> bool:
        """
        Reset consecutive failure counter if we're stuck.
        Useful for forcing a fresh start after recovery attempts.
        
        Returns:
            True if was stuck and got reset, False otherwise
        """
        if self.is_stuck():
            print(f"[CHECKPOINT] Resetting stuck state (was {self.consecutive_failures} consecutive failures)")
            self.consecutive_failures = 0
            self.save()
            return True
        return False
