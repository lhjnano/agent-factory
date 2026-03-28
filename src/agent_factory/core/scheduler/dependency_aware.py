from typing import List, Optional, Set, Dict, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque

from .base import BaseScheduler, SchedulingResult


@dataclass
class DependencyAwareConfig:
    critical_path_weight: float = 0.5
    dependency_depth_weight: float = 0.3
    parallelism_bonus: float = 0.2
    max_dependency_depth: int = 10


class DependencyAwareScheduler(BaseScheduler):
    def __init__(self, config: Optional[DependencyAwareConfig] = None):
        super().__init__(name="dependency_aware")
        self.config = config or DependencyAwareConfig()
        self._dependency_graph: Dict[str, List[str]] = {}
        self._reverse_graph: Dict[str, List[str]] = {}
        self._depth_cache: Dict[str, int] = {}
        self._critical_path: List[str] = []
    
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
        
        self._build_graph(works)
        self._calculate_depths()
        self._identify_critical_path(works, completed_ids)
        
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
            score = self._calculate_dependency_score(work, completed_ids)
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
        
        parallel_works = self._find_parallel_works(selected_work, eligible_works, completed_ids)
        if parallel_works:
            agent_for_parallel = self._select_agent_for_parallelism(
                capable_agents, selected_work, parallel_works
            )
            if agent_for_parallel:
                selected_agent = agent_for_parallel
            else:
                selected_agent = min(capable_agents, key=lambda a: a.current_concurrent_works)
        else:
            selected_agent = min(capable_agents, key=lambda a: a.current_concurrent_works)
        
        self._record_success(True)
        
        return SchedulingResult(
            work=selected_work,
            agent=selected_agent,
            score=scored_works[0][1],
            reason="Selected by dependency-aware scheduler",
            estimated_duration=self.estimate_duration(selected_work),
            estimated_tokens=self.estimate_tokens(selected_work),
            alternative_agents=[a.agent_id for a in capable_agents if a.agent_id != selected_agent.agent_id]
        )
    
    def _build_graph(self, works: List["Work"]):
        self._dependency_graph.clear()
        self._reverse_graph.clear()
        
        work_ids = {w.work_id for w in works}
        
        for work in works:
            self._dependency_graph[work.work_id] = work.dependencies.copy()
            
            for dep_id in work.dependencies:
                if dep_id not in self._reverse_graph:
                    self._reverse_graph[dep_id] = []
                if work.work_id not in self._reverse_graph[dep_id]:
                    self._reverse_graph[dep_id].append(work.work_id)
        
        for work_id in work_ids:
            if work_id not in self._dependency_graph:
                self._dependency_graph[work_id] = []
            if work_id not in self._reverse_graph:
                self._reverse_graph[work_id] = []
    
    def _calculate_depths(self):
        self._depth_cache.clear()
        
        def get_depth(work_id: str, visited: set) -> int:
            if work_id in visited:
                return 0
            if work_id in self._depth_cache:
                return self._depth_cache[work_id]
            
            visited.add(work_id)
            
            if work_id not in self._dependency_graph:
                self._depth_cache[work_id] = 0
                return 0
            
            if not self._dependency_graph[work_id]:
                self._depth_cache[work_id] = 0
                return 0
            
            max_dep_depth = 0
            for dep_id in self._dependency_graph[work_id]:
                dep_depth = get_depth(dep_id, visited.copy())
                max_dep_depth = max(max_dep_depth, dep_depth)
            
            depth = max_dep_depth + 1
            self._depth_cache[work_id] = depth
            return depth
        
        for work_id in list(self._dependency_graph.keys()):
            get_depth(work_id, set())
    
    def _identify_critical_path(self, works: List["Work"], completed_ids: Set[str]):
        works_dict = {w.work_id: w for w in works}
        
        max_depth = 0
        deepest_work = None
        for work_id, depth in self._depth_cache.items():
            if work_id not in completed_ids and depth > max_depth:
                max_depth = depth
                deepest_work = work_id
        
        if not deepest_work:
            self._critical_path = []
            return
        
        path = [deepest_work]
        current = deepest_work
        
        while current in self._dependency_graph and self._dependency_graph[current]:
            for dep_id in self._dependency_graph[current]:
                if dep_id in self._depth_cache:
                    if self._depth_cache.get(dep_id, 0) == self._depth_cache.get(current, 0) - 1:
                        path.append(dep_id)
                        current = dep_id
                        break
        
        self._critical_path = list(reversed(path))
    
    def _calculate_dependency_score(self, work: "Work", completed_ids: Set[str]) -> float:
        depth = self._depth_cache.get(work.work_id, 0)
        depth_score = depth / self.config.max_dependency_depth
        
        critical_score = 0.0
        if work.work_id in self._critical_path:
            position = self._critical_path.index(work.work_id)
            critical_score = self.config.critical_path_weight * (1.0 - position / len(self._critical_path))
        
        blocked_count = len(self._reverse_graph.get(work.work_id, []))
        parallelism_score = min(1.0, blocked_count / 5.0) * self.config.parallelism_bonus
        
        return depth_score * self.config.dependency_depth_weight + critical_score + parallelism_score
    
    def _find_parallel_works(
        self,
        selected_work: "Work",
        eligible_works: List["Work"],
        completed_ids: Set[str]
    ) -> List["Work"]:
        parallel = []
        selected_depth = self._depth_cache.get(selected_work.work_id, 0)
        
        for work in eligible_works:
            if work.work_id == selected_work.work_id:
                continue
            
            work_depth = self._depth_cache.get(work.work_id, 0)
            if work_depth == selected_depth:
                if not set(work.dependencies) & set(selected_work.dependencies):
                    parallel.append(work)
        
        return parallel
    
    def _select_agent_for_parallelism(
        self,
        agents: List["AgentInstance"],
        primary_work: "Work",
        parallel_works: List["Work"]
    ) -> Optional["AgentInstance"]:
        if len(agents) < 2:
            return None
        
        if not parallel_works:
            return None
        
        parallel_work = parallel_works[0]
        
        for agent in agents:
            if parallel_work.agent_type in agent.capabilities or parallel_work.agent_type == agent.agent_type:
                if agent.agent_id != agents[0].agent_id:
                    return agent
        
        return None
    
    def estimate_duration(self, work: "Work") -> float:
        return work.estimated_duration_seconds
    
    def estimate_tokens(self, work: "Work") -> int:
        return work.estimated_tokens
    
    def get_dependency_stats(self) -> dict:
        return {
            "total_works": len(self._dependency_graph),
            "max_depth": max(self._depth_cache.values()) if self._depth_cache else 0,
            "avg_depth": sum(self._depth_cache.values()) / len(self._depth_cache) if self._depth_cache else 0,
            "critical_path_length": len(self._critical_path),
            "works_with_no_dependencies": sum(1 for deps in self._dependency_graph.values() if not deps),
            "works_with_dependencies": sum(1 for deps in self._dependency_graph.values() if deps)
        }
    
    def get_blocked_works(self, work_id: str) -> List[str]:
        return self._reverse_graph.get(work_id, [])
    
    def get_blocking_works(self, work_id: str) -> List[str]:
        return self._dependency_graph.get(work_id, [])
