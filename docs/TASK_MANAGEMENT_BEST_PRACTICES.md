# Async Task Management Best Practices

**Date:** 2025-10-05  
**Purpose:** Robust task orchestration for parallel PDF downloads  
**Status:** Implementation Guide

---

## 🎯 **Core Principles**

### **1. Work Queue Pattern**
**Problem:** Multiple tasks might try to process the same vehicle  
**Solution:** Pre-assign work to prevent conflicts

### **2. Timeout Management**
**Problem:** Stuck tasks block progress indefinitely  
**Solution:** Per-task timeouts with automatic cancellation

### **3. Task Recovery**
**Problem:** Failed tasks disappear without retry  
**Solution:** Failed tasks return to queue for retry

### **4. Resource Isolation**
**Problem:** One stuck page blocks others  
**Solution:** Each page operates independently

---

## 🏗️ **Architecture: Task Queue with Worker Pool**

```
┌─────────────────────────────────────────────────────────┐
│                    Work Queue                            │
│  [ref1, ref2, ref3, ref4, ref5, ref6, ..., ref2000]    │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │  Task Manager  │  Coordinates workers
              │  - Assigns work│
              │  - Monitors    │
              │  - Recovers    │
              └────────┬───────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   ┌────────┐     ┌────────┐     ┌────────┐
   │Worker 1│     │Worker 2│     │Worker 3│
   │(Page 1)│     │(Page 2)│     │(Page 3)│
   │────────│     │────────│     │────────│
   │Get task│     │Get task│     │Get task│
   │Process │     │Process │     │Process │
   │Report  │     │Report  │     │Report  │
   └────────┘     └────────┘     └────────┘
```

---

## 📋 **Implementation Components**

### **1. AsyncTaskQueue**
**Purpose:** Thread-safe work queue for vehicle references

```python
class AsyncTaskQueue:
    """Thread-safe async task queue with retry support."""
    
    def __init__(self, items: List[str]):
        self.queue = asyncio.Queue()
        self.in_progress = {}  # Track what's being processed
        self.completed = set()
        self.failed = {}  # Track failures with retry count
        self._lock = asyncio.Lock()
        
        # Populate queue
        for item in items:
            self.queue.put_nowait(item)
    
    async def get_task(self, worker_id: int) -> Optional[str]:
        """Get next task for worker."""
        try:
            task = await asyncio.wait_for(
                self.queue.get(), 
                timeout=1.0
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
    
    async def mark_complete(self, task: str):
        """Mark task as successfully completed."""
        async with self._lock:
            self.in_progress.pop(task, None)
            self.completed.add(task)
            self.failed.pop(task, None)
    
    async def mark_failed(self, task: str, max_retries: int = 2):
        """Mark task as failed and requeue if retries remain."""
        async with self._lock:
            self.in_progress.pop(task, None)
            retry_count = self.failed.get(task, 0) + 1
            
            if retry_count <= max_retries:
                # Requeue for retry
                self.failed[task] = retry_count
                await self.queue.put(task)
                print(f"[QUEUE] Requeued {task} (attempt {retry_count + 1}/{max_retries + 1})")
            else:
                # Max retries exceeded
                print(f"[QUEUE] Task {task} failed after {retry_count} attempts")
    
    async def get_stuck_tasks(self, timeout_seconds: int = 300) -> List[str]:
        """Find tasks that have been in progress too long."""
        stuck = []
        now = datetime.utcnow()
        
        async with self._lock:
            for task, info in self.in_progress.items():
                elapsed = (now - info['started_at']).total_seconds()
                if elapsed > timeout_seconds:
                    stuck.append(task)
        
        return stuck
    
    async def recover_stuck_task(self, task: str):
        """Recover a stuck task by requeueing it."""
        async with self._lock:
            if task in self.in_progress:
                worker_id = self.in_progress[task]['worker_id']
                print(f"[QUEUE] Recovering stuck task {task} from worker {worker_id}")
                self.in_progress.pop(task)
                await self.queue.put(task)
    
    def get_statistics(self) -> dict:
        """Get queue statistics."""
        return {
            'pending': self.queue.qsize(),
            'in_progress': len(self.in_progress),
            'completed': len(self.completed),
            'failed': len([k for k, v in self.failed.items() if v > 2]),
            'total': self.queue.qsize() + len(self.in_progress) + len(self.completed)
        }
```

---

### **2. Worker with Timeout**
**Purpose:** Process tasks with automatic timeout and cancellation

```python
async def worker(
    worker_id: int,
    page: Page,
    task_queue: AsyncTaskQueue,
    checkpoint: ProgressCheckpoint,
    metrics: RunMetrics,
    timeout_seconds: int = 180  # 3 minutes per vehicle
):
    """Worker that processes tasks from queue with timeout."""
    
    print(f"[WORKER {worker_id}] Started")
    
    while True:
        # Get next task
        ref_num = await task_queue.get_task(worker_id)
        
        if ref_num is None:
            # Queue empty, check if we're done
            stats = task_queue.get_statistics()
            if stats['pending'] == 0 and stats['in_progress'] == 0:
                print(f"[WORKER {worker_id}] No more tasks, shutting down")
                break
            
            # Wait a bit and try again
            await asyncio.sleep(2)
            continue
        
        print(f"[WORKER {worker_id}] Processing {ref_num}")
        
        try:
            # Process with timeout
            success = await asyncio.wait_for(
                process_single_vehicle_async(
                    page=page,
                    ref_num=ref_num,
                    checkpoint=checkpoint,
                    metrics=metrics,
                    max_retries=1  # Worker handles retries via queue
                ),
                timeout=timeout_seconds
            )
            
            if success:
                await task_queue.mark_complete(ref_num)
                print(f"[WORKER {worker_id}] Completed {ref_num}")
            else:
                await task_queue.mark_failed(ref_num)
                print(f"[WORKER {worker_id}] Failed {ref_num}")
        
        except asyncio.TimeoutError:
            print(f"[WORKER {worker_id}] TIMEOUT on {ref_num} after {timeout_seconds}s")
            await task_queue.mark_failed(ref_num)
            
            # Try to recover the page
            try:
                await recover_to_inventory_async(page)
            except:
                print(f"[WORKER {worker_id}] Recovery failed, continuing...")
        
        except asyncio.CancelledError:
            print(f"[WORKER {worker_id}] Cancelled, requeueing {ref_num}")
            await task_queue.recover_stuck_task(ref_num)
            raise
        
        except Exception as e:
            print(f"[WORKER {worker_id}] Error on {ref_num}: {e}")
            await task_queue.mark_failed(ref_num)
    
    print(f"[WORKER {worker_id}] Stopped")
```

---

### **3. Watchdog for Stuck Tasks**
**Purpose:** Monitor and recover stuck workers

```python
async def watchdog(
    task_queue: AsyncTaskQueue,
    check_interval: int = 60,  # Check every minute
    timeout_seconds: int = 300  # 5 minutes = stuck
):
    """Monitor for stuck tasks and recover them."""
    
    print("[WATCHDOG] Started")
    
    while True:
        await asyncio.sleep(check_interval)
        
        # Check for stuck tasks
        stuck_tasks = await task_queue.get_stuck_tasks(timeout_seconds)
        
        if stuck_tasks:
            print(f"[WATCHDOG] Found {len(stuck_tasks)} stuck tasks")
            
            for task in stuck_tasks:
                print(f"[WATCHDOG] Recovering stuck task: {task}")
                await task_queue.recover_stuck_task(task)
        
        # Print statistics
        stats = task_queue.get_statistics()
        print(f"[WATCHDOG] Queue status: {stats}")
        
        # Check if we're done
        if stats['pending'] == 0 and stats['in_progress'] == 0:
            print("[WATCHDOG] All tasks complete, shutting down")
            break
    
    print("[WATCHDOG] Stopped")
```

---

### **4. Main Orchestrator**
**Purpose:** Coordinate workers, queue, and watchdog

```python
async def run_async_with_queue():
    """Main orchestration with task queue pattern."""
    
    # ... browser setup, login, CSV export ...
    
    # Create task queue
    task_queue = AsyncTaskQueue(pending_refs)
    
    # Create workers (one per page)
    workers = []
    for i, page in enumerate(pages):
        worker_task = asyncio.create_task(
            worker(
                worker_id=i,
                page=page,
                task_queue=task_queue,
                checkpoint=checkpoint,
                metrics=metrics,
                timeout_seconds=180
            )
        )
        workers.append(worker_task)
    
    # Start watchdog
    watchdog_task = asyncio.create_task(
        watchdog(
            task_queue=task_queue,
            check_interval=60,
            timeout_seconds=300
        )
    )
    
    # Wait for all workers to complete
    await asyncio.gather(*workers, watchdog_task)
    
    # Print final statistics
    stats = task_queue.get_statistics()
    print(f"\n[FINAL] Completed: {stats['completed']}/{stats['total']}")
```

---

## 🎯 **Key Benefits**

### **1. No Duplicate Processing**
- ✅ Each task assigned to exactly one worker
- ✅ Queue ensures no two workers get same task
- ✅ In-progress tracking prevents reassignment

### **2. Automatic Timeout**
- ✅ Each task has 3-minute timeout
- ✅ Stuck tasks automatically cancelled
- ✅ Page recovered and task requeued

### **3. Automatic Retry**
- ✅ Failed tasks automatically requeued
- ✅ Max 2 retries per task
- ✅ Retry count tracked

### **4. Stuck Task Recovery**
- ✅ Watchdog monitors all tasks
- ✅ Tasks stuck >5 minutes recovered
- ✅ Automatic requeue for retry

### **5. Graceful Shutdown**
- ✅ Workers stop when queue empty
- ✅ Watchdog stops when all complete
- ✅ Clean exit with statistics

---

## 📊 **Comparison: Pre-Assignment vs Task Queue**

| Feature | Pre-Assignment | Task Queue |
|---------|---------------|------------|
| Duplicate prevention | ✅ Yes | ✅ Yes |
| Load balancing | ❌ Fixed | ✅ Dynamic |
| Stuck task recovery | ❌ No | ✅ Yes |
| Timeout handling | ❌ Manual | ✅ Automatic |
| Retry logic | ❌ Per-worker | ✅ Centralized |
| Worker failure | ❌ Loses tasks | ✅ Tasks requeued |
| Complexity | ✅ Simple | ⚠️ Moderate |

**Recommendation:** Use **Task Queue** for production (more robust)

---

## 🔧 **Configuration**

```python
# Task Queue Settings
TASK_TIMEOUT = 180  # 3 minutes per vehicle
WATCHDOG_INTERVAL = 60  # Check every minute
STUCK_THRESHOLD = 300  # 5 minutes = stuck
MAX_RETRIES = 2  # Retry failed tasks twice

# Worker Settings
NUM_WORKERS = 5  # Number of parallel workers (pages)
WORKER_DELAY = 1  # Delay between tasks (rate limiting)
```

---

## ⚠️ **Edge Cases Handled**

### **1. Worker Crashes**
- Task remains in queue
- Watchdog detects stuck task
- Task requeued for another worker

### **2. Page Hangs**
- Timeout cancels the task
- Page recovery attempted
- Task requeued for retry

### **3. Network Issues**
- Task fails with exception
- Automatic retry (up to 2 times)
- Checkpoint tracks failure

### **4. Browser Crash**
- All workers stop
- Tasks remain in queue
- Restart resumes from queue

---

## 🧪 **Testing Strategy**

### **Test 1: Verify No Duplicates**
```python
# Process 100 vehicles
# Check tracking.json - each ref should appear once
```

### **Test 2: Verify Timeout**
```python
# Inject a task that hangs
# Verify it times out after 3 minutes
# Verify it gets requeued
```

### **Test 3: Verify Recovery**
```python
# Simulate stuck task
# Verify watchdog detects it
# Verify it gets recovered
```

### **Test 4: Verify Retry**
```python
# Inject a task that fails
# Verify it retries up to 2 times
# Verify it's marked failed after max retries
```

---

## 📝 **Implementation Checklist**

- [ ] Create `AsyncTaskQueue` class
- [ ] Update `worker()` function with timeout
- [ ] Create `watchdog()` function
- [ ] Update `run_async()` to use queue pattern
- [ ] Add timeout configuration
- [ ] Add watchdog configuration
- [ ] Test with 10 vehicles
- [ ] Test with 30 vehicles
- [ ] Test timeout handling
- [ ] Test retry logic
- [ ] Test stuck task recovery

---

## 🚀 **Expected Improvements**

| Metric | Pre-Assignment | Task Queue | Improvement |
|--------|---------------|------------|-------------|
| Stuck task handling | Manual | Automatic | ✅ Better |
| Load balancing | Static | Dynamic | ✅ Better |
| Worker utilization | Fixed | Adaptive | ✅ Better |
| Failure recovery | Limited | Comprehensive | ✅ Better |
| Complexity | Low | Medium | ⚠️ Trade-off |

---

## 🎯 **Recommendation**

**Implement Task Queue pattern for production use.**

**Why:**
- ✅ More robust error handling
- ✅ Better resource utilization
- ✅ Automatic recovery from failures
- ✅ Handles edge cases gracefully
- ✅ Industry-standard pattern

**Trade-off:**
- Slightly more complex
- Worth it for 8-hour production runs

---

**Next Step:** Implement AsyncTaskQueue and update orchestration
