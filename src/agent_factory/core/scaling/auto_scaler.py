from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable, TYPE_CHECKING
from datetime import datetime
from enum import Enum
import asyncio

from .scaling_policy import ScalingPolicy, ScalingConfig, ScalingAction

if TYPE_CHECKING:
    from ..agent_pool import AgentPool, AgentInstance
    from ..queue import MultiQueueManager


@dataclass
class ScalingDecision:
    action: ScalingAction
    agent_type: str
    count: int
    reason: str
    timestamp: datetime = field(default_factory=datetime.now)
    current_count: int = 0
    target_count: int = 0
    metrics: Dict[str, Any] = field(default_factory=dict)


class AutoScaler:
    def __init__(
        self,
        agent_pool: "AgentPool",
        queue_manager: "MultiQueueManager",
        config: Optional[ScalingConfig] = None
    ):
        self.agent_pool = agent_pool
        self.queue_manager = queue_manager
        self.config = config or ScalingConfig()
        self.policy = ScalingPolicy(self.config)
        
        self._agent_factories: Dict[str, Callable] = {}
        self._running = False
        self._evaluation_count = 0
        self._last_evaluation: Optional[datetime] = None
        self._decisions: List[ScalingDecision] = []
    
    def register_agent_factory(self, agent_type: str, factory: Callable[[], "AgentInstance"]):
        self._agent_factories[agent_type] = factory
    
    async def evaluate_and_scale(self) -> List[ScalingDecision]:
        self._evaluation_count += 1
        self._last_evaluation = datetime.now()
        
        decisions = []
        
        agent_types = set(self.agent_pool._type_index.keys())
        
        for agent_type in agent_types:
            decision = await self._evaluate_agent_type(agent_type)
            if decision and decision.action != ScalingAction.NO_ACTION:
                decisions.append(decision)
                await self._apply_decision(decision)
        
        self._decisions.extend(decisions)
        if len(self._decisions) > 1000:
            self._decisions = self._decisions[-1000:]
        
        return decisions
    
    async def _evaluate_agent_type(self, agent_type: str) -> Optional[ScalingDecision]:
        agents = self.agent_pool.get_agents_by_type(agent_type)
        if not agents:
            return None
        
        current_count = len(agents)
        available_capacity = self.agent_pool.get_available_capacity(agent_type)
        total_capacity = self.agent_pool.get_capacity(agent_type)
        
        queue_length = await self._get_queue_length_for_type(agent_type)
        
        avg_utilization = self._calculate_avg_utilization(agents)
        avg_wait_time = await self._estimate_wait_time(agent_type, queue_length, available_capacity)
        
        action = self.policy.evaluate(
            agent_type=agent_type,
            queue_length=queue_length,
            available_capacity=available_capacity,
            total_capacity=total_capacity,
            current_agent_count=current_count,
            avg_utilization=avg_utilization,
            avg_wait_time=avg_wait_time
        )
        
        if action == ScalingAction.NO_ACTION:
            return None
        
        scale_count = self.policy.calculate_scale_count(
            action=action,
            queue_length=queue_length,
            available_capacity=available_capacity,
            current_count=current_count
        )
        
        if scale_count <= 0:
            return None
        
        return ScalingDecision(
            action=action,
            agent_type=agent_type,
            count=scale_count,
            reason=self._generate_reason(action, queue_length, available_capacity, current_count),
            current_count=current_count,
            target_count=current_count + scale_count if action == ScalingAction.SCALE_UP else current_count - scale_count,
            metrics={
                "queue_length": queue_length,
                "available_capacity": available_capacity,
                "total_capacity": total_capacity,
                "avg_utilization": avg_utilization,
                "avg_wait_time": avg_wait_time
            }
        )
    
    async def _get_queue_length_for_type(self, agent_type: str) -> int:
        pending_works = await self.queue_manager.get_all_pending()
        return sum(1 for w in pending_works if w.agent_type == agent_type)
    
    def _calculate_avg_utilization(self, agents: List["AgentInstance"]) -> float:
        if not agents:
            return 0.0
        return sum(a.utilization for a in agents) / len(agents)
    
    async def _estimate_wait_time(
        self,
        agent_type: str,
        queue_length: int,
        available_capacity: int
    ) -> float:
        if available_capacity > 0:
            return 0.0
        
        avg_work_duration = 60.0
        
        return queue_length * avg_work_duration / max(1, available_capacity)
    
    def _generate_reason(
        self,
        action: ScalingAction,
        queue_length: int,
        available_capacity: int,
        current_count: int
    ) -> str:
        if action == ScalingAction.SCALE_UP:
            return f"Queue length ({queue_length}) exceeds available capacity ({available_capacity})"
        elif action == ScalingAction.SCALE_DOWN:
            return f"Low utilization: available capacity ({available_capacity}) is high relative to queue ({queue_length})"
        return "No specific reason"
    
    async def _apply_decision(self, decision: ScalingDecision):
        if decision.action == ScalingAction.SCALE_UP:
            await self._scale_up(decision.agent_type, decision.count)
        elif decision.action == ScalingAction.SCALE_DOWN:
            await self._scale_down(decision.agent_type, decision.count)
        
        self.policy.record_scaling(decision.agent_type, decision.action, decision.count)
    
    async def _scale_up(self, agent_type: str, count: int):
        factory = self._agent_factories.get(agent_type)
        if not factory:
            print(f"No factory registered for agent type: {agent_type}")
            return
        
        for _ in range(count):
            try:
                agent = factory()
                self.agent_pool.register_agent(agent)
            except Exception as e:
                print(f"Failed to create agent of type {agent_type}: {e}")
                break
    
    async def _scale_down(self, agent_type: str, count: int):
        self.agent_pool.scale_down(agent_type, count)
    
    async def start_monitoring(self):
        self._running = True
        
        while self._running:
            try:
                await self.evaluate_and_scale()
            except Exception as e:
                print(f"Error in auto-scaling: {e}")
            
            await asyncio.sleep(self.config.evaluation_interval_seconds)
    
    def stop_monitoring(self):
        self._running = False
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "evaluation_count": self._evaluation_count,
            "last_evaluation": self._last_evaluation.isoformat() if self._last_evaluation else None,
            "total_decisions": len(self._decisions),
            "policy_stats": self.policy.get_stats(),
            "recent_decisions": [
                {
                    "action": d.action.value,
                    "agent_type": d.agent_type,
                    "count": d.count,
                    "reason": d.reason,
                    "timestamp": d.timestamp.isoformat()
                }
                for d in self._decisions[-10:]
            ]
        }
    
    def get_decision_history(self, limit: int = 100) -> List[ScalingDecision]:
        return self._decisions[-limit:]
    
    def force_scale_up(self, agent_type: str, count: int = 1) -> ScalingDecision:
        current_agents = self.agent_pool.get_agents_by_type(agent_type)
        current_count = len(current_agents)
        
        decision = ScalingDecision(
            action=ScalingAction.SCALE_UP,
            agent_type=agent_type,
            count=count,
            reason="Manual scale up request",
            current_count=current_count,
            target_count=current_count + count
        )
        
        self._decisions.append(decision)
        return decision
    
    def force_scale_down(self, agent_type: str, count: int = 1) -> ScalingDecision:
        current_agents = self.agent_pool.get_agents_by_type(agent_type)
        current_count = len(current_agents)
        
        decision = ScalingDecision(
            action=ScalingAction.SCALE_DOWN,
            agent_type=agent_type,
            count=count,
            reason="Manual scale down request",
            current_count=current_count,
            target_count=max(self.config.thresholds.min_agents, current_count - count)
        )
        
        self._decisions.append(decision)
        return decision
