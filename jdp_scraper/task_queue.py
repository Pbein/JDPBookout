"""
Async task queue for robust parallel processing.

Provides thread-safe work distribution, retry logic, and stuck task recovery.
"""

import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Set


class AsyncTaskQueue:
    """
    Thread-safe async task queue with retry support.
    
    Features:
    - Dynamic work distribution (no pre-assignment)
    - Automatic retry for failed tasks
    - Stuck task detection and recovery
    - Thread-safe operations with asyncio.Lock
    - Statistics tracking
    
    Example:
        queue = AsyncTaskQueue(["ref1", "ref2", "ref3"])
        
        # Worker gets task
        task = await queue.get_task(worker_id=0)
        
        # Worker completes task
        await queue.mark_complete(task)
        
        # Or worker fails task (will retry)
        await queue.mark_failed(task, max_retries=2)
    """
    
    def __init__(self, items: List[str]):
        """
        Initialize the task queue.
        
        Args:
            items: List of reference numbers to process
        """
        self.queue = asyncio.Queue()
        self.in_progress: Dict[str, Dict] = {}  # task -> {worker_id, started_at, attempts}
        self.completed: Set[str] = set()
        self.failed: Dict[str, int] = {}  # task -> retry_count
        self._lock = asyncio.Lock()
        self._total_items = len(items)
        
        # Populate queue
        for item in items:
            self.queue.put_nowait(item)
        
        print(f"[TASK_QUEUE] Initialized with {len(items)} tasks")
    
    async def get_task(self, worker_id: int, timeout: float = 1.0) -> Optional[str]:
        """
        Get next task for worker.
        
        Args:
            worker_id: ID of the worker requesting work
            timeout: How long to wait for a task (seconds)
            
        Returns:
            Task reference number, or None if queue is empty
        """
        try:
            task = await asyncio.wait_for(
                self.queue.get(),
                timeout=timeout
            )
            
            async with self._lock:
                self.in_progress[task] = {
                    'worker_id': worker_id,
                    'started_at': datetime.utcnow(),
                    'attempts': self.failed.get(task, 0) + 1
                }
            
            return task
            
        except asyncio.TimeoutError:
            return None  # Queue empty
    
    async def mark_complete(self, task: str) -> None:
        """
        Mark task as successfully completed.
        
        Args:
            task: Task reference number
        """
        async with self._lock:
            self.in_progress.pop(task, None)
            self.completed.add(task)
            self.failed.pop(task, None)
    
    async def mark_failed(self, task: str, max_retries: int = 2) -> None:
        """
        Mark task as failed and requeue if retries remain.
        
        Args:
            task: Task reference number
            max_retries: Maximum number of retry attempts
        """
        async with self._lock:
            self.in_progress.pop(task, None)
            retry_count = self.failed.get(task, 0) + 1
            
            if retry_count <= max_retries:
                # Requeue for retry
                self.failed[task] = retry_count
                await self.queue.put(task)
                print(f"[TASK_QUEUE] Requeued {task} (attempt {retry_count + 1}/{max_retries + 1})")
            else:
                # Max retries exceeded
                print(f"[TASK_QUEUE] Task {task} failed after {retry_count} attempts")
    
    async def get_stuck_tasks(self, timeout_seconds: int = 300) -> List[str]:
        """
        Find tasks that have been in progress too long.
        
        Args:
            timeout_seconds: How long before a task is considered stuck
            
        Returns:
            List of stuck task reference numbers
        """
        stuck = []
        now = datetime.utcnow()
        
        async with self._lock:
            for task, info in self.in_progress.items():
                elapsed = (now - info['started_at']).total_seconds()
                if elapsed > timeout_seconds:
                    stuck.append(task)
        
        return stuck
    
    async def recover_stuck_task(self, task: str) -> None:
        """
        Recover a stuck task by requeueing it.
        
        Args:
            task: Task reference number
        """
        async with self._lock:
            if task in self.in_progress:
                worker_id = self.in_progress[task]['worker_id']
                print(f"[TASK_QUEUE] Recovering stuck task {task} from worker {worker_id}")
                self.in_progress.pop(task)
                await self.queue.put(task)
    
    async def get_statistics(self) -> Dict:
        """
        Get queue statistics.
        
        Returns:
            Dictionary with queue stats
        """
        async with self._lock:
            pending = self.queue.qsize()
            in_progress = len(self.in_progress)
            completed = len(self.completed)
            permanently_failed = len([k for k, v in self.failed.items() if v > 2 and k not in self.in_progress])
            
            return {
                'total': self._total_items,
                'pending': pending,
                'in_progress': in_progress,
                'completed': completed,
                'failed': permanently_failed,
                'success_rate': (completed / self._total_items * 100) if self._total_items > 0 else 0
            }
    
    async def print_statistics(self) -> None:
        """Print formatted statistics to console (ASCII only)."""
        stats = await self.get_statistics()
        
        print("\n" + "="*60)
        print("TASK QUEUE STATISTICS")
        print("="*60)
        print(f"Total tasks        : {stats['total']}")
        print(f"Pending            : {stats['pending']}")
        print(f"In progress        : {stats['in_progress']}")
        print(f"Completed          : {stats['completed']}")
        print(f"Failed (permanent) : {stats['failed']}")
        print(f"Success rate       : {stats['success_rate']:.1f}%")
        print("="*60 + "\n")
    
    async def is_empty(self) -> bool:
        """
        Check if queue is empty and no tasks in progress.
        
        Returns:
            True if all work is done, False otherwise
        """
        stats = await self.get_statistics()
        return stats['pending'] == 0 and stats['in_progress'] == 0
    
    async def wait_until_empty(self, check_interval: float = 2.0) -> None:
        """
        Wait until queue is empty and no tasks in progress.
        
        Args:
            check_interval: How often to check (seconds)
        """
        while not await self.is_empty():
            await asyncio.sleep(check_interval)
