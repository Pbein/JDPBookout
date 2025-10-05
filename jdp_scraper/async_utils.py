"""
Async utilities for parallel processing.

Provides AsyncSemaphorePool for managing concurrent task execution with statistics.
"""

import asyncio
from typing import Dict, Any
from datetime import datetime


class AsyncSemaphorePool:
    """
    Manages concurrent task execution with a semaphore and tracks statistics.
    
    Features:
    - Concurrency limiting via semaphore
    - Task tracking (active, completed, failed)
    - Performance statistics
    - Thread-safe operations with asyncio.Lock
    
    Example:
        pool = AsyncSemaphorePool(max_concurrent=5)
        async with pool.acquire():
            # Do work here with concurrency limit
            pass
    """
    
    def __init__(self, max_concurrent: int = 5):
        """
        Initialize the semaphore pool.
        
        Args:
            max_concurrent: Maximum number of concurrent tasks allowed
        """
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        # Statistics tracking (thread-safe with lock)
        self._lock = asyncio.Lock()
        self._active_count = 0
        self._completed_count = 0
        self._failed_count = 0
        self._total_started = 0
        
        # Timing
        self._started_at = datetime.utcnow()
        self._task_times = []
    
    def acquire(self):
        """
        Acquire a semaphore slot for task execution.
        
        Returns:
            An async context manager that tracks task lifecycle
            
        Example:
            async with pool.acquire():
                # Task executes here with concurrency limit
                pass
        """
        return self._TaskContext(self)
    
    class _TaskContext:
        """Internal context manager for individual task tracking."""
        
        def __init__(self, pool: 'AsyncSemaphorePool'):
            self.pool = pool
            self.task_start = None
            
        async def __aenter__(self):
            """Acquire semaphore and increment active count."""
            await self.pool.semaphore.acquire()
            
            async with self.pool._lock:
                self.pool._active_count += 1
                self.pool._total_started += 1
                
            self.task_start = datetime.utcnow()
            return self
            
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            """Release semaphore and update statistics."""
            task_duration = (datetime.utcnow() - self.task_start).total_seconds()
            
            async with self.pool._lock:
                self.pool._active_count -= 1
                self.pool._task_times.append(task_duration)
                
                if exc_type is None:
                    self.pool._completed_count += 1
                else:
                    self.pool._failed_count += 1
                    
            self.pool.semaphore.release()
            return False  # Don't suppress exceptions
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get current pool statistics.
        
        Returns:
            Dictionary containing pool statistics
        """
        async with self._lock:
            stats = {
                'active': self._active_count,
                'completed': self._completed_count,
                'failed': self._failed_count,
                'total_started': self._total_started,
                'max_concurrent': self.max_concurrent,
            }
            
            if self._task_times:
                stats['avg_duration'] = sum(self._task_times) / len(self._task_times)
                stats['min_duration'] = min(self._task_times)
                stats['max_duration'] = max(self._task_times)
            else:
                stats['avg_duration'] = 0
                stats['min_duration'] = 0
                stats['max_duration'] = 0
                
            stats['uptime'] = (datetime.utcnow() - self._started_at).total_seconds()
                
        return stats
    
    async def print_statistics(self) -> None:
        """Print formatted statistics to console (ASCII only)."""
        stats = await self.get_statistics()
        
        print("\n" + "="*60)
        print("ASYNC POOL STATISTICS")
        print("="*60)
        print(f"Active tasks       : {stats['active']}/{stats['max_concurrent']}")
        print(f"Completed tasks    : {stats['completed']}")
        print(f"Failed tasks       : {stats['failed']}")
        print(f"Total started      : {stats['total_started']}")
        
        if stats['avg_duration'] > 0:
            print(f"Avg task duration  : {stats['avg_duration']:.2f}s")
            print(f"Min task duration  : {stats['min_duration']:.2f}s")
            print(f"Max task duration  : {stats['max_duration']:.2f}s")
            
        print(f"Pool uptime        : {stats['uptime']:.1f}s")
        print("="*60 + "\n")
