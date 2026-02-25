from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import asyncio


class AgentStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"


@dataclass
class AgentInstance:
    agent_id: str
    agent_type: str
    capabilities: List[str]
    status: AgentStatus = AgentStatus.IDLE
    current_work_id: Optional[str] = None
    completed_works: int = 0
    failed_works: int = 0
    total_tokens_used: int = 0
    total_work_time_seconds: float = 0.0
    last_activity: Optional[datetime] = None
    max_concurrent_works: int = 1
    current_concurrent_works: int = 0
    priority: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    execute_func: Optional[Callable] = None

    @property
    def utilization(self) -> float:
        if self.max_concurrent_works == 0:
            return 0.0
        return self.current_concurrent_works / self.max_concurrent_works

    @property
    def success_rate(self) -> float:
        total = self.completed_works + self.failed_works
        if total == 0:
            return 1.0
        return self.completed_works / total

    @property
    def is_available(self) -> bool:
        return (
            self.status == AgentStatus.IDLE and
            self.current_concurrent_works < self.max_concurrent_works
        )

    def can_handle(self, agent_type: str) -> bool:
        return agent_type in self.capabilities or agent_type == self.agent_type

    def assign_work(self, work_id: str):
        self.current_work_id = work_id
        self.current_concurrent_works += 1
        if self.current_concurrent_works >= self.max_concurrent_works:
            self.status = AgentStatus.BUSY
        self.last_activity = datetime.now()

    def complete_work(self, tokens_used: int, duration_seconds: float, success: bool):
        self.current_concurrent_works = max(0, self.current_concurrent_works - 1)
        self.total_tokens_used += tokens_used
        self.total_work_time_seconds += duration_seconds
        
        if success:
            self.completed_works += 1
        else:
            self.failed_works += 1
        
        if self.current_concurrent_works == 0:
            self.status = AgentStatus.IDLE
            self.current_work_id = None
        
        self.last_activity = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "capabilities": self.capabilities,
            "status": self.status.value,
            "current_work_id": self.current_work_id,
            "completed_works": self.completed_works,
            "failed_works": self.failed_works,
            "total_tokens_used": self.total_tokens_used,
            "total_work_time_seconds": self.total_work_time_seconds,
            "utilization": self.utilization,
            "success_rate": self.success_rate,
            "is_available": self.is_available
        }


class AgentPool:
    def __init__(self):
        self._agents: Dict[str, AgentInstance] = {}
        self._type_index: Dict[str, List[str]] = {}
        self._lock = asyncio.Lock()
    
    def register_agent(self, agent: AgentInstance):
        self._agents[agent.agent_id] = agent
        
        if agent.agent_type not in self._type_index:
            self._type_index[agent.agent_type] = []
        self._type_index[agent.agent_type].append(agent.agent_id)
        
        for cap in agent.capabilities:
            if cap not in self._type_index:
                self._type_index[cap] = []
            if agent.agent_id not in self._type_index[cap]:
                self._type_index[cap].append(agent.agent_id)
    
    def unregister_agent(self, agent_id: str):
        agent = self._agents.pop(agent_id, None)
        if agent:
            if agent.agent_type in self._type_index:
                self._type_index[agent.agent_type] = [
                    aid for aid in self._type_index[agent.agent_type] if aid != agent_id
                ]
            for cap in agent.capabilities:
                if cap in self._type_index:
                    self._type_index[cap] = [
                        aid for aid in self._type_index[cap] if aid != agent_id
                    ]
    
    def get_agent(self, agent_id: str) -> Optional[AgentInstance]:
        return self._agents.get(agent_id)
    
    def get_agents_by_type(self, agent_type: str) -> List[AgentInstance]:
        agent_ids = self._type_index.get(agent_type, [])
        return [self._agents[aid] for aid in agent_ids if aid in self._agents]
    
    def get_available_agents(self, agent_type: str) -> List[AgentInstance]:
        agents = self.get_agents_by_type(agent_type)
        return [a for a in agents if a.is_available]
    
    async def select_agent(self, agent_type: str, strategy: str = "least_loaded") -> Optional[AgentInstance]:
        async with self._lock:
            available = self.get_available_agents(agent_type)
            if not available:
                return None
            
            if strategy == "least_loaded":
                return min(available, key=lambda a: a.utilization)
            elif strategy == "round_robin":
                return available[0]
            elif strategy == "most_capable":
                return max(available, key=lambda a: len(a.capabilities))
            elif strategy == "highest_success":
                return max(available, key=lambda a: a.success_rate)
            else:
                return available[0]
    
    def get_pool_status(self) -> Dict[str, Any]:
        total_agents = len(self._agents)
        idle_agents = sum(1 for a in self._agents.values() if a.status == AgentStatus.IDLE)
        busy_agents = sum(1 for a in self._agents.values() if a.status == AgentStatus.BUSY)
        offline_agents = sum(1 for a in self._agents.values() if a.status == AgentStatus.OFFLINE)
        error_agents = sum(1 for a in self._agents.values() if a.status == AgentStatus.ERROR)
        
        total_tokens = sum(a.total_tokens_used for a in self._agents.values())
        total_works = sum(a.completed_works + a.failed_works for a in self._agents.values())
        
        by_type: Dict[str, int] = {}
        for agent in self._agents.values():
            by_type[agent.agent_type] = by_type.get(agent.agent_type, 0) + 1
        
        return {
            "total_agents": total_agents,
            "idle_agents": idle_agents,
            "busy_agents": busy_agents,
            "offline_agents": offline_agents,
            "error_agents": error_agents,
            "total_tokens_used": total_tokens,
            "total_works_completed": total_works,
            "agents_by_type": by_type,
            "utilization_rate": busy_agents / total_agents if total_agents > 0 else 0
        }
    
    def scale_up(self, agent_type: str, count: int, factory: Callable[[], AgentInstance]):
        for _ in range(count):
            agent = factory()
            if agent.agent_type == agent_type:
                self.register_agent(agent)
    
    def scale_down(self, agent_type: str, count: int):
        agents_of_type = self.get_agents_by_type(agent_type)
        idle_agents = [a for a in agents_of_type if a.status == AgentStatus.IDLE]
        
        for agent in idle_agents[:count]:
            self.unregister_agent(agent.agent_id)
    
    def get_capacity(self, agent_type: str) -> int:
        agents = self.get_agents_by_type(agent_type)
        return sum(a.max_concurrent_works for a in agents)
    
    def get_available_capacity(self, agent_type: str) -> int:
        agents = self.get_agents_by_type(agent_type)
        return sum(
            a.max_concurrent_works - a.current_concurrent_works
            for a in agents
            if a.status in [AgentStatus.IDLE, AgentStatus.BUSY]
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agents": {aid: agent.to_dict() for aid, agent in self._agents.items()},
            "pool_status": self.get_pool_status()
        }
