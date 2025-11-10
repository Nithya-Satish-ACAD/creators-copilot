"""
Task Manager Service for handling async background tasks
"""
import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
import threading

logger = logging.getLogger(__name__)

class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Task:
    def __init__(self, task_id: str, task_type: str, metadata: Dict[str, Any] = None):
        self.task_id = task_id
        self.task_type = task_type
        self.status = TaskStatus.PENDING
        self.result = None
        self.error = None
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

class TaskManager:
    """
    Thread-safe in-memory task manager for tracking background tasks
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self.tasks: Dict[str, Task] = {}
        self._lock = threading.Lock()
        self._initialized = True
        logger.info("TaskManager initialized")
    
    def create_task(self, task_type: str, metadata: Dict[str, Any] = None) -> str:
        """Create a new task and return its ID"""
        task_id = str(uuid.uuid4())
        task = Task(task_id, task_type, metadata)
        
        with self._lock:
            self.tasks[task_id] = task
        
        logger.info(f"Created task {task_id} of type {task_type}")
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        with self._lock:
            return self.tasks.get(task_id)
    
    def update_task_status(self, task_id: str, status: TaskStatus, result: Any = None, error: str = None):
        """Update task status and optional result/error"""
        with self._lock:
            task = self.tasks.get(task_id)
            if not task:
                logger.warning(f"Task {task_id} not found")
                return
            
            task.status = status
            task.updated_at = datetime.now()
            
            if status == TaskStatus.PROCESSING and task.started_at is None:
                task.started_at = datetime.now()
            
            if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                task.completed_at = datetime.now()
            
            if result is not None:
                task.result = result
            
            if error is not None:
                task.error = error
            
            logger.info(f"Task {task_id} status updated to {status.value}")
    
    def mark_processing(self, task_id: str):
        """Mark task as processing"""
        self.update_task_status(task_id, TaskStatus.PROCESSING)
    
    def mark_completed(self, task_id: str, result: Any):
        """Mark task as completed with result"""
        self.update_task_status(task_id, TaskStatus.COMPLETED, result=result)
    
    def mark_failed(self, task_id: str, error: str):
        """Mark task as failed with error"""
        self.update_task_status(task_id, TaskStatus.FAILED, error=error)
    
    def mark_cancelled(self, task_id: str):
        """Mark task as cancelled"""
        self.update_task_status(task_id, TaskStatus.CANCELLED)
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Remove tasks older than max_age_hours"""
        cutoff = datetime.now().timestamp() - (max_age_hours * 3600)
        
        with self._lock:
            old_tasks = [
                task_id for task_id, task in self.tasks.items()
                if task.created_at.timestamp() < cutoff
            ]
            
            for task_id in old_tasks:
                del self.tasks[task_id]
            
            if old_tasks:
                logger.info(f"Cleaned up {len(old_tasks)} old tasks")

# Global instance
task_manager = TaskManager()

