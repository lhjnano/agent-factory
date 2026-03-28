from typing import Dict, Any
from datetime import datetime


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
