from typing import List, Optional, Set
from dataclasses import dataclass

from .base import BaseScheduler, SchedulingResult


@dataclass
class TokenAwareConfig:
    token_budget: int = 1000000
    warning_threshold: float = 0.8
    critical_threshold: float = 0.95
    small_task_bonus: float = 0.2


class TokenAwareScheduler(BaseScheduler):
    def __init__(self, config: Optional[TokenAwareConfig] = None):
        super().__init__(name="token_aware")
        self.config = config or TokenAwareConfig()
        self._tokens_used = 0
        self._tokens_reserved = 0
        self._budget_history: list = []
    
    @property
    def tokens_remaining(self) -> int:
        return self.config.token_budget - self._tokens_used - self._tokens_reserved
    
    @property
    def utilization_rate(self) -> float:
        return self._tokens_used / self.config.token_budget if self.config.token_budget > 0 else 0.0
    
    def select(
        self,
        works: List["Work"],
        agents: List["AgentInstance"],
        completed_work_ids: Set[str] = None
    ) -> SchedulingResult:
        from ..work import WorkStatus
        
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
                reason="No eligible works"
            )
        
        remaining = self.tokens_remaining
        if remaining <= 0:
            return SchedulingResult(
                work=None,
                agent=None,
                reason="Token budget exhausted"
            )
        
        affordable_works = [
            w for w in eligible_works
            if self.estimate_tokens(w) <= remaining
        ]
        
        if not affordable_works:
            smallest = min(eligible_works, key=lambda w: self.estimate_tokens(w))
            if self.estimate_tokens(smallest) <= remaining:
                affordable_works = [smallest]
            else:
                return SchedulingResult(
                    work=None,
                    agent=None,
                    reason=f"No affordable works (remaining: {remaining}, smallest: {self.estimate_tokens(smallest)})"
                )
        
        scored_works = []
        for work in affordable_works:
            score = self._calculate_token_score(work)
            scored_works.append((work, score))
        
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
        
        self._reserve_tokens(self.estimate_tokens(selected_work))
        self._record_success(True)
        
        return SchedulingResult(
            work=selected_work,
            agent=selected_agent,
            score=scored_works[0][1],
            reason="Selected by token-aware scheduler",
            estimated_duration=self.estimate_duration(selected_work),
            estimated_tokens=self.estimate_tokens(selected_work),
            alternative_agents=[a.agent_id for a in capable_agents if a.agent_id != selected_agent.agent_id]
        )
    
    def _calculate_token_score(self, work: "Work") -> float:
        estimated = self.estimate_tokens(work)
        remaining = self.tokens_remaining
        utilization = self.utilization_rate
        
        efficiency_score = 1.0 - (estimated / remaining) if remaining > 0 else 0.0
        
        if estimated < remaining * 0.1:
            small_task_bonus = self.config.small_task_bonus
        else:
            small_task_bonus = 0.0
        
        if utilization >= self.config.critical_threshold:
            urgency_penalty = (utilization - self.config.critical_threshold) * 2
        elif utilization >= self.config.warning_threshold:
            urgency_penalty = (utilization - self.config.warning_threshold)
        else:
            urgency_penalty = 0.0
        
        return max(0.0, efficiency_score + small_task_bonus - urgency_penalty)
    
    def _reserve_tokens(self, amount: int):
        self._tokens_reserved += amount
    
    def commit_tokens(self, actual_tokens: int, reserved_tokens: int):
        self._tokens_used += actual_tokens
        self._tokens_reserved -= reserved_tokens
        self._budget_history.append({
            "used": self._tokens_used,
            "reserved": self._tokens_reserved,
            "remaining": self.tokens_remaining
        })
    
    def release_reservation(self, reserved_tokens: int):
        self._tokens_reserved -= reserved_tokens
    
    def estimate_duration(self, work: "Work") -> float:
        return work.estimated_duration_seconds
    
    def estimate_tokens(self, work: "Work") -> int:
        return work.estimated_tokens
    
    def get_token_stats(self) -> dict:
        return {
            "budget": self.config.token_budget,
            "used": self._tokens_used,
            "reserved": self._tokens_reserved,
            "remaining": self.tokens_remaining,
            "utilization": self.utilization_rate,
            "warning_threshold": self.config.warning_threshold,
            "critical_threshold": self.config.critical_threshold,
            "is_warning": self.utilization_rate >= self.config.warning_threshold,
            "is_critical": self.utilization_rate >= self.config.critical_threshold
        }
    
    def reset_budget(self, new_budget: Optional[int] = None):
        if new_budget is not None:
            self.config.token_budget = new_budget
        self._tokens_used = 0
        self._tokens_reserved = 0
        self._budget_history.clear()
