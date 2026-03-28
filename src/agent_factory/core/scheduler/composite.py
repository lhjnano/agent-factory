from typing import List, Optional, Set, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from .base import BaseScheduler, SchedulingResult, SchedulingStrategy
from .sjf_scheduler import SJFScheduler, SJFConfig
from .token_aware import TokenAwareScheduler, TokenAwareConfig
from .dependency_aware import DependencyAwareScheduler, DependencyAwareConfig


@dataclass
class SchedulerConfig:
    strategies: List[SchedulingStrategy] = field(default_factory=lambda: [
        SchedulingStrategy.DEPENDENCY_AWARE,
        SchedulingStrategy.SJF,
        SchedulingStrategy.TOKEN_AWARE
    ])
    weights: Dict[SchedulingStrategy, float] = field(default_factory=lambda: {
        SchedulingStrategy.DEPENDENCY_AWARE: 0.4,
        SchedulingStrategy.SJF: 0.35,
        SchedulingStrategy.TOKEN_AWARE: 0.25
    })
    token_budget: int = 1000000
    enable_adaptive_weights: bool = True
    adaptation_window: int = 100


class CompositeScheduler(BaseScheduler):
    def __init__(self, config: Optional[SchedulerConfig] = None):
        super().__init__(name="composite")
        self.config = config or SchedulerConfig()
        
        self._schedulers: Dict[SchedulingStrategy, BaseScheduler] = {}
        self._initialize_schedulers()
        
        self._performance_history: List[Dict[str, Any]] = []
        self._adaptive_weights = self.config.weights.copy()
    
    def _initialize_schedulers(self):
        for strategy in self.config.strategies:
            if strategy == SchedulingStrategy.SJF:
                self._schedulers[strategy] = SJFScheduler(SJFConfig())
            elif strategy == SchedulingStrategy.TOKEN_AWARE:
                self._schedulers[strategy] = TokenAwareScheduler(
                    TokenAwareConfig(token_budget=self.config.token_budget)
                )
            elif strategy == SchedulingStrategy.DEPENDENCY_AWARE:
                self._schedulers[strategy] = DependencyAwareScheduler(
                    DependencyAwareConfig()
                )
    
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
        
        work_scores: Dict[str, Dict[SchedulingStrategy, float]] = {}
        for work in eligible_works:
            work_scores[work.work_id] = {}
            for strategy, scheduler in self._schedulers.items():
                score = scheduler.calculate_score(work, None)
                work_scores[work.work_id][strategy] = score
        
        weighted_scores: Dict[str, float] = {}
        for work_id, scores in work_scores.items():
            total_score = 0.0
            for strategy, score in scores.items():
                weight = self._adaptive_weights.get(strategy, 0.0)
                total_score += score * weight
            weighted_scores[work_id] = total_score
        
        best_work_id = max(weighted_scores.keys(), key=lambda wid: weighted_scores[wid])
        selected_work = next(w for w in eligible_works if w.work_id == best_work_id)
        
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
        self._update_performance_history(selected_work, weighted_scores[best_work_id])
        
        if self.config.enable_adaptive_weights:
            self._adapt_weights()
        
        return SchedulingResult(
            work=selected_work,
            agent=selected_agent,
            score=weighted_scores[best_work_id],
            reason="Selected by composite scheduler",
            estimated_duration=self.estimate_duration(selected_work),
            estimated_tokens=self.estimate_tokens(selected_work),
            alternative_agents=[a.agent_id for a in capable_agents if a.agent_id != selected_agent.agent_id]
        )
    
    def _update_performance_history(self, work: "Work", score: float):
        self._performance_history.append({
            "work_id": work.work_id,
            "work_type": work.work_type,
            "score": score,
            "timestamp": work.created_at.isoformat() if work.created_at else None
        })
        
        if len(self._performance_history) > 1000:
            self._performance_history = self._performance_history[-1000:]
    
    def _adapt_weights(self):
        if len(self._performance_history) < self.config.adaptation_window:
            return
        
        recent = self._performance_history[-self.config.adaptation_window:]
        
        for strategy in self.config.strategies:
            scheduler = self._schedulers[strategy]
            stats = scheduler.get_stats()
            
            success_rate = stats.get("success_rate", 0.5)
            current_weight = self._adaptive_weights.get(strategy, 0.0)
            
            adjustment = (success_rate - 0.5) * 0.1
            new_weight = current_weight + adjustment
            
            min_weight = 0.1
            max_weight = 0.6
            new_weight = max(min_weight, min(max_weight, new_weight))
            
            self._adaptive_weights[strategy] = new_weight
        
        total = sum(self._adaptive_weights.values())
        if total > 0:
            for strategy in self._adaptive_weights:
                self._adaptive_weights[strategy] /= total
    
    def estimate_duration(self, work: "Work") -> float:
        return work.estimated_duration_seconds
    
    def estimate_tokens(self, work: "Work") -> int:
        return work.estimated_tokens
    
    def get_composite_stats(self) -> dict:
        scheduler_stats = {}
        for strategy, scheduler in self._schedulers.items():
            scheduler_stats[strategy.value] = scheduler.get_stats()
        
        return {
            "name": self.name,
            "strategies": [s.value for s in self.config.strategies],
            "weights": {s.value: w for s, w in self._adaptive_weights.items()},
            "schedulers": scheduler_stats,
            "performance_history_size": len(self._performance_history),
            "adaptive_weights_enabled": self.config.enable_adaptive_weights
        }
    
    def set_weight(self, strategy: SchedulingStrategy, weight: float):
        self._adaptive_weights[strategy] = weight
    
    def reset_weights(self):
        self._adaptive_weights = self.config.weights.copy()
    
    def get_scheduler(self, strategy: SchedulingStrategy) -> Optional[BaseScheduler]:
        return self._schedulers.get(strategy)
