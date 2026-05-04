import asyncio
from typing import Callable, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field
from collections import deque
import threading
from app.utils.logger import logger


@dataclass
class Task:
    id: str
    func: Callable
    args: tuple
    kwargs: dict
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class AsyncTaskQueue:
    def __init__(self, max_workers: int = 5, max_queue_size: int = 100):
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        self._queue: deque = deque()
        self._workers: List[asyncio.Task] = []
        self._running = False
        self._lock = asyncio.Lock()
        self._stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "queue_size": 0
        }
    
    async def add_task(
        self,
        func: Callable,
        *args,
        priority: int = 0,
        **kwargs
    ) -> str:
        import uuid
        task_id = str(uuid.uuid4())[:8]
        
        task = Task(
            id=task_id,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority
        )
        
        async with self._lock:
            if len(self._queue) >= self.max_queue_size:
                logger.warning(f"Task queue full, dropping task {task_id}")
                raise RuntimeError("Task queue is full")
            
            self._queue.append(task)
            self._stats["total_tasks"] += 1
            self._stats["queue_size"] = len(self._queue)
        
        logger.debug(f"Task {task_id} added to queue")
        return task_id
    
    async def _worker(self, worker_id: int):
        logger.info(f"Worker {worker_id} started")
        
        while self._running:
            try:
                task = None
                async with self._lock:
                    if self._queue:
                        task = self._queue.popleft()
                        self._stats["queue_size"] = len(self._queue)
                
                if task:
                    task.started_at = datetime.now()
                    logger.debug(f"Worker {worker_id} processing task {task.id}")
                    
                    try:
                        if asyncio.iscoroutinefunction(task.func):
                            await task.func(*task.args, **task.kwargs)
                        else:
                            await asyncio.get_event_loop().run_in_executor(
                                None,
                                task.func,
                                *task.args
                            )
                        
                        task.completed_at = datetime.now()
                        async with self._lock:
                            self._stats["completed_tasks"] += 1
                        
                        logger.debug(f"Task {task.id} completed")
                    except Exception as e:
                        task.error = str(e)
                        async with self._lock:
                            self._stats["failed_tasks"] += 1
                        logger.error(f"Task {task.id} failed: {e}")
                else:
                    await asyncio.sleep(0.1)
            
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(1)
        
        logger.info(f"Worker {worker_id} stopped")
    
    async def start(self):
        if self._running:
            return
        
        self._running = True
        
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(i))
            self._workers.append(worker)
        
        logger.info(f"Task queue started with {self.max_workers} workers")
    
    async def stop(self):
        self._running = False
        
        for worker in self._workers:
            worker.cancel()
        
        self._workers.clear()
        logger.info("Task queue stopped")
    
    def get_stats(self) -> dict:
        return {
            **self._stats,
            "workers": len(self._workers),
            "is_running": self._running
        }


task_queue = AsyncTaskQueue(max_workers=5, max_queue_size=100)


def async_task(priority: int = 0):
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            return await task_queue.add_task(func, *args, priority=priority, **kwargs)
        return wrapper
    return decorator


class BackgroundTaskManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._tasks = {}
                    cls._instance._results = {}
        return cls._instance
    
    def add_background_task(
        self,
        task_id: str,
        coro: Callable,
        callback: Optional[Callable] = None
    ):
        async def run_task():
            try:
                result = await coro
                self._results[task_id] = {
                    "status": "completed",
                    "result": result,
                    "completed_at": datetime.now().isoformat()
                }
                if callback:
                    await callback(result)
            except Exception as e:
                self._results[task_id] = {
                    "status": "failed",
                    "error": str(e),
                    "completed_at": datetime.now().isoformat()
                }
                logger.error(f"Background task {task_id} failed: {e}")
        
        self._tasks[task_id] = asyncio.create_task(run_task())
        logger.info(f"Background task {task_id} started")
    
    def get_task_result(self, task_id: str) -> Optional[dict]:
        return self._results.get(task_id)
    
    def cleanup_old_results(self, max_age_seconds: int = 3600):
        cutoff = datetime.now()
        for task_id in list(self._results.keys()):
            result = self._results[task_id]
            completed_at = datetime.fromisoformat(result["completed_at"])
            if (cutoff - completed_at).total_seconds() > max_age_seconds:
                del self._results[task_id]


background_task_manager = BackgroundTaskManager()
