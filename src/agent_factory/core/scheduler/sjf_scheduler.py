from typing import List, Optional, Set
from dataclasses import dataclass

from .base import BaseScheduler, SchedulingResult


@dataclass
class SJFConfig:
    duration_weight: float = 1.0
    priority_weight: float = 0.5
    starvation_threshold: int = 10
    aging_factor: float = 0.1


class SJFScheduler(BaseScheduler):
    def __init__(self, config: Optional[SJFConfig] = None):
        super().__init__(name="sjf")
        self.config = config or SJFConfig()
        self._starvation_counters: dict = {}
    
    def select(
        self,
        works: List["Work"],
        agents: List["AgentInstance"],
        completed_work_ids: Set[str] = None
    ) -> SchedulingResult:
        from ..work import WorkStatus
        
        self._update_starvation_counters(works)
        
        completed_ids = completed_work_ids or set()
        
        available_agents = [a for a in agents if a.is_available]
        if not available_agents or not works:
            return SchedulingResult(
                work=None,
                agent=None,
                reason="No available agents or works"
            )
        
        eligible_works = [
            w for w in works
            if w.status in [WorkStatus.PENDING, WorkStatus.QUEUED]
            and w.can_start(completed_ids)
        ]
        
        if not eligible_works:
            return SchedulingResult(
                work=None,
                agent=None,
                reason="No eligible works with satisfied dependencies"
            )
        
        scored_works = []
        for work in eligible_works:
            duration_score = self._calculate_duration_score(work)
            priority_score = self._calculate_priority_score(work)
            starvation_bonus = self._calculate_starvation_bonus(work)
            
            total_score = (
                duration_score * self.config.duration_weight +
                priority_score * self.config.priority_weight +
                starvation_bonus
            )
            
            scored_works.append((work, total_score))
        
        scored_works.sort(key=lambda x: x[1], reverse=True)
        selected_work = scored_works[0][0]
        
        capable_agents = [
            a for a in available_agents
            if selected_work.agent_type in a.capabilities or
               selected_work.agent_type == a.agent_type
        ]
        
        if not capable_agents:
            return SchedulingResult(
                work=None,
                agent=None,
                reason=f"No capable agent for work type: {selected_work.agent_type}"
            )
        
        selected_agent = min(
            capable_agents,
            key=lambda a: a.current_concurrent_works
        )
        
        self._record_success(True)
        self._reset_starvation_counter(selected_work.work_id)
        
        return SchedulingResult(
            work=selected_work,
            agent=selected_agent,
            score=scored_works[0][1],
            reason="Selected by SJF: shortest estimated duration",
            estimated_duration=self.estimate_duration(selected_work),
            estimated_tokens=self.estimate_tokens(selected_work),
            alternative_agents=[a.agent_id for a in capable_agents if a.agent_id != selected_agent.agent_id]
        )
    
    def _update_starvation_counters(self, works: List["Work"]):
        from ..work import WorkStatus
        
        current_ids = {w.work_id for w in works}
        
        for work_id in list(self._starvation_counters.keys()):
            if work_id not in current_ids:
                del self._starvation_counters[work_id]
        
        for work in works:
            if work.status in [WorkStatus.PENDING, WorkStatus.QUEUED]:
                if work.work_id not in self._starvation_counters:
                    self._starvation_counters[work.work_id] = 0
                self._starvation_counters[work.work_id] += 1
    
    def _calculate_duration_score(self, work: "Work") -> float:
        estimated = self.estimate_duration(work)
        max_duration = 600.0
        normalized = 1.0 - (estimated / max_duration)
        return max(0.0, min(1.0, normalized))
    
    def _calculate_priority_score(self, work: "Work") -> float:
        from ..work import WorkPriority
        
        priority_scores = {
            WorkPriority.CRITICAL: 1.0,
            WorkPriority.HIGH: 0.75,
            WorkPriority.MEDIUM: 0.5,
            WorkPriority.LOW: 0.25,
        }
        return priority_scores.get(work.priority, 0.5)
    
    def _calculate_starvation_bonus(self, work: "Work") -> float:
        counter = self._starvation_counters.get(work.work_id, 0)
        if counter >= self.config.starvation_threshold:
            return self.config.aging_factor * (counter - self.config.starvation_threshold)
        return 0.0
    
    def _reset_starvation_counter(self, work_id: str):
        if work_id in self._starvation_counters:
            del self._starvation_counters[work_id]
    
    def estimate_duration(self, work: "Work") -> float:
        return work.estimated_duration_seconds
    
    def estimate_tokens(self, work: "Work") -> int:
        return work.estimated_tokens
    
    def get_starvation_stats(self) -> dict:
        return {
            "starving_works": sum(
                1 for c in self._starvation_counters.values()
                if c >= self.config.starvation_threshold
            ),
            "max_starvation": max(self._starvation_counters.values()) if self._starvation_counters else 0,
            "average_starvation": (
                sum(self._starvation_counters.values()) / len(self._starvation_counters)
                if self._starvation_counters else 0
            )
        }
