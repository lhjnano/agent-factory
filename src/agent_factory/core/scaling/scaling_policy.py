from dataclasses import dataclass, field
from typing import Optional, List, Set
from enum import Enum
from datetime import datetime, timedelta


class ScalingMetric(Enum):
    QUEUE_LENGTH = "queue_length"
    AGENT_UTILIZATION = "agent_utilization"
    THROUGHPUT = "throughput"
    LATENCY = "latency"
    CUSTOM = "custom"


class ScalingAction(Enum):
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    NO_ACTION = "no_action"


@dataclass
class ScalingThresholds:
    scale_up_threshold: float = 2.0
    scale_down_threshold: float = 0.3
    critical_threshold: float = 5.0
    
    scale_up_cooldown_seconds: float = 60.0
    scale_down_cooldown_seconds: float = 120.0
    
    min_agents: int = 1
    max_agents: int = 10
    max_scale_up_count: int = 3
    max_scale_down_count: int = 2


@dataclass
class ScalingConfig:
    enabled: bool = True
    thresholds: ScalingThresholds = field(default_factory=ScalingThresholds)
    metrics: List[ScalingMetric] = field(default_factory=lambda: [
        ScalingMetric.QUEUE_LENGTH,
        ScalingMetric.AGENT_UTILIZATION
    ])
    evaluation_interval_seconds: float = 30.0
    enable_predictive_scaling: bool = False
    prediction_window_seconds: float = 300.0


class ScalingPolicy:
    def __init__(self, config: Optional[ScalingConfig] = None):
        self.config = config or ScalingConfig()
        self._last_scale_up: dict = {}
        self._last_scale_down: dict = {}
        self._scaling_history: list = []
    
    def evaluate(
        self,
        agent_type: str,
        queue_length: int,
        available_capacity: int,
        total_capacity: int,
        current_agent_count: int,
        avg_utilization: float = 0.0,
        avg_wait_time: float = 0.0,
    ) -> ScalingAction:
        if not self.config.enabled:
            return ScalingAction.NO_ACTION
        
        thresholds = self.config.thresholds
        
        if current_agent_count >= thresholds.max_agents:
            return ScalingAction.NO_ACTION
        
        if current_agent_count <= thresholds.min_agents:
            if queue_length > 0 and available_capacity == 0:
                return ScalingAction.SCALE_UP
            return ScalingAction.NO_ACTION
        
        if self._is_in_cooldown(agent_type, ScalingAction.SCALE_UP):
            return ScalingAction.NO_ACTION
        
        queue_to_capacity_ratio = queue_length / total_capacity if total_capacity > 0 else 0
        
        if queue_to_capacity_ratio >= thresholds.critical_threshold:
            return ScalingAction.SCALE_UP
        
        if queue_to_capacity_ratio >= thresholds.scale_up_threshold:
            if available_capacity == 0:
                return ScalingAction.SCALE_UP
        
        if self._is_in_cooldown(agent_type, ScalingAction.SCALE_DOWN):
            return ScalingAction.NO_ACTION
        
        if queue_to_capacity_ratio <= thresholds.scale_down_threshold:
            idle_ratio = available_capacity / total_capacity if total_capacity > 0 else 0
            if idle_ratio >= 0.7:
                return ScalingAction.SCALE_DOWN
        
        return ScalingAction.NO_ACTION
    
    def _is_in_cooldown(self, agent_type: str, action: ScalingAction) -> bool:
        now = datetime.now()
        thresholds = self.config.thresholds
        
        if action == ScalingAction.SCALE_UP:
            last_time = self._last_scale_up.get(agent_type)
            cooldown = thresholds.scale_up_cooldown_seconds
        else:
            last_time = self._last_scale_down.get(agent_type)
            cooldown = thresholds.scale_down_cooldown_seconds
        
        if last_time is None:
            return False
        
        return (now - last_time).total_seconds() < cooldown
    
    def record_scaling(self, agent_type: str, action: ScalingAction, count: int):
        now = datetime.now()
        
        if action == ScalingAction.SCALE_UP:
            self._last_scale_up[agent_type] = now
        elif action == ScalingAction.SCALE_DOWN:
            self._last_scale_down[agent_type] = now
        
        self._scaling_history.append({
            "agent_type": agent_type,
            "action": action.value,
            "count": count,
            "timestamp": now.isoformat()
        })
    
    def calculate_scale_count(
        self,
        action: ScalingAction,
        queue_length: int,
        available_capacity: int,
        current_count: int,
    ) -> int:
        thresholds = self.config.thresholds
        
        if action == ScalingAction.SCALE_UP:
            needed = queue_length - available_capacity
            scale_count = min(
                max(1, needed),
                thresholds.max_scale_up_count
            )
            
            max_possible = thresholds.max_agents - current_count
            return min(scale_count, max_possible)
        
        elif action == ScalingAction.SCALE_DOWN:
            if available_capacity >= current_count * 0.5:
                scale_count = min(
                    current_count // 2,
                    thresholds.max_scale_down_count
                )
                
                min_required = thresholds.min_agents
                max_down = current_count - min_required
                return min(scale_count, max_down)
            
            return 0
        
        return 0
    
    def get_scaling_history(self, limit: int = 100) -> list:
        return self._scaling_history[-limit:]
    
    def get_stats(self) -> dict:
        scale_ups = sum(1 for h in self._scaling_history if h["action"] == "scale_up")
        scale_downs = sum(1 for h in self._scaling_history if h["action"] == "scale_down")
        
        return {
            "enabled": self.config.enabled,
            "total_scale_ups": scale_ups,
            "total_scale_downs": scale_downs,
            "history_size": len(self._scaling_history),
            "cooldowns": {
                "scale_up": list(self._last_scale_up.keys()),
                "scale_down": list(self._last_scale_down.keys())
            }
        }
    
    def reset(self):
        self._last_scale_up.clear()
        self._last_scale_down.clear()
        self._scaling_history.clear()
