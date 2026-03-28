from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime
from enum import Enum


class RetryStrategy(Enum):
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    CONSTANT = "constant"


@dataclass
class RetryPolicy:
    max_retries: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    base_delay: float = 1.0
    max_delay: float = 60.0
    retry_on_errors: List[str] = field(default_factory=lambda: ["timeout", "rate_limit", "connection_error"])
    
    def get_delay(self, retry_count: int) -> float:
        if retry_count <= 0:
            return 0
        
        if self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.base_delay * (2 ** (retry_count - 1))
            return min(delay, self.max_delay)
        
        elif self.strategy == RetryStrategy.LINEAR:
            return self.base_delay * retry_count
        
        elif self.strategy == RetryStrategy.CONSTANT:
            return self.base_delay
        
        return self.base_delay
    
    def should_retry(self, error: Exception) -> bool:
        error_str = str(error).lower()
        return any(err_type in error_str for err_type in self.retry_on_errors)


    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_retries": self.max_retries,
            "strategy": self.strategy.value,
            "base_delay": self.base_delay,
            "max_delay": self.max_delay,
            "retry_on_errors": self.retry_on_errors
        }


class RetryManager:
    def __init__(self, default_policy: Optional[RetryPolicy] = None):
        self.default_policy = default_policy or RetryPolicy()
        self._retry_history: Dict[str, List[Dict[str, Any]]] = {}
    
    def record_retry(self, work_id: str, error: Exception, policy: Optional[RetryPolicy] = None):
        if work_id not in self._retry_history:
            self._retry_history[work_id] = []
        
        self._retry_history[work_id].append({
            "timestamp": datetime.now().isoformat(),
            "error": str(error),
            "policy": (policy or self.default_policy).to_dict()
        })
    
    def get_retry_count(self, work_id: str) -> int:
        return len(self._retry_history.get(work_id, []))
    
    def can_retry(self, work_id: str, policy: Optional[RetryPolicy] = None) -> bool:
        retry_count = self.get_retry_count(work_id)
        effective_policy = policy or self.default_policy
        return retry_count < effective_policy.max_retries
    
    def get_next_delay(self, work_id: str, policy: Optional[RetryPolicy] = None) -> float:
        retry_count = self.get_retry_count(work_id)
        effective_policy = policy or self.default_policy
        return effective_policy.get_delay(retry_count + 1)
    
    def get_stats(self) -> Dict[str, Any]:
        total_retries = sum(len(retries) for retries in self._retry_history.values())
        
        return {
            "total_retries": total_retries,
            "unique_works": len(self._retry_history),
            "retry_history": {
                work_id: retries for work_id, retries in self._retry_history.items()
            }
        }


class TimeoutStrategy:
    def __init__(self, default_timeout: float = 300.0):
        self.default_timeout = default_timeout
        self._timeout_history: Dict[str, Dict[str, Any]] = {}
    
    def set_timeout(self, work_id: str, timeout: float):
        self._timeout_history[work_id] = {
            "timeout": timeout,
            "set_at": datetime.now().isoformat()
        }
    
    def get_timeout(self, work_id: str) -> float:
        if work_id in self._timeout_history:
            return self._timeout_history[work_id]["timeout"]
        return self.default_timeout
    
    def clear_timeout(self, work_id: str):
        self._timeout_history.pop(work_id, None)
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "default_timeout": self.default_timeout,
            "active_timeouts": len(self._timeout_history),
            "timeout_history": self._timeout_history
        }
