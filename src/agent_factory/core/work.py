from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
import asyncio


class WorkStatus(Enum):
    PENDING = "pending"
    QUEUED = "queued"
    PLAN_SUBMITTED = "plan_submitted"
    PLAN_APPROVED = "plan_approved"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class PlanStatus(Enum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class WorkPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class WorkResult:
    work_id: str
    status: WorkStatus
    output: Any = None
    error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    documentation: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


@dataclass
class WorkPlan:
    plan_id: str
    work_id: str
    proposed_by: str
    content: Dict[str, Any]
    submitted_at: datetime = field(default_factory=datetime.now)
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    status: PlanStatus = PlanStatus.PENDING


@dataclass
class Work:
    work_id: str
    name: str
    description: str
    work_type: str
    agent_type: str
    priority: WorkPriority = WorkPriority.MEDIUM
    status: WorkStatus = WorkStatus.PENDING
    dependencies: List[str] = field(default_factory=list)
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    estimated_tokens: int = 1000
    actual_tokens: int = 0
    estimated_duration_seconds: float = 60.0
    actual_duration_seconds: float = 0.0
    max_retries: int = 3
    retry_count: int = 0
    timeout_seconds: float = 300.0
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    assigned_agent: Optional[str] = None
    raci_roles: Dict[str, str] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    execute_func: Optional[Callable] = None
    require_plan_approval: bool = False
    plan: Optional[WorkPlan] = None
    required_skills: List[str] = field(default_factory=list)
    skill_assignments: Dict[str, Dict[str, List[str]]] = field(default_factory=dict)
    queue_preference: str = "auto"

    def can_start(self, completed_work_ids: set) -> bool:
        return all(dep_id in completed_work_ids for dep_id in self.dependencies)

    def start(self, agent_id: str):
        self.status = WorkStatus.RUNNING
        self.assigned_agent = agent_id
        self.started_at = datetime.now()

    def complete(self, result: WorkResult):
        self.status = result.status
        self.outputs = result.output if isinstance(result.output, dict) else {"result": result.output}
        self.actual_tokens = result.metrics.get("tokens_used", 0)
        self.completed_at = result.completed_at or datetime.now()
        if self.started_at:
            self.actual_duration_seconds = (self.completed_at - self.started_at).total_seconds()

    def fail(self, error: str):
        self.status = WorkStatus.FAILED
        self.retry_count += 1
        self.completed_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}
        self.metadata["last_error"] = error

    def can_retry(self) -> bool:
        return self.retry_count < self.max_retries

    def submit_plan(self, plan_content: Dict[str, Any], proposed_by: str) -> WorkPlan:
        plan_id = f"plan_{self.work_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        plan = WorkPlan(
            plan_id=plan_id,
            work_id=self.work_id,
            proposed_by=proposed_by,
            content=plan_content
        )
        self.plan = plan
        self.status = WorkStatus.PLAN_SUBMITTED
        return plan

    def approve_plan(self, approved_by: str) -> bool:
        if self.plan is None:
            return False
        self.plan.status = PlanStatus.APPROVED
        self.plan.approved_by = approved_by
        self.plan.approved_at = datetime.now()
        self.status = WorkStatus.PLAN_APPROVED
        return True

    def reject_plan(self, rejected_by: str, reason: str) -> bool:
        if self.plan is None:
            return False
        self.plan.status = PlanStatus.REJECTED
        self.plan.approved_by = rejected_by
        self.plan.approved_at = datetime.now()
        self.plan.rejection_reason = reason
        self.status = WorkStatus.PENDING
        return True

    def has_approved_plan(self) -> bool:
        return (
            self.plan is not None and
            self.plan.status == PlanStatus.APPROVED and
            self.require_plan_approval
        )

    def needs_plan_approval(self) -> bool:
        return (
            self.require_plan_approval and
            self.plan is None or
            (self.plan is not None and self.plan.status == PlanStatus.REJECTED)
        )

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "work_id": self.work_id,
            "name": self.name,
            "description": self.description,
            "work_type": self.work_type,
            "agent_type": self.agent_type,
            "priority": self.priority.value,
            "status": self.status.value,
            "dependencies": self.dependencies,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "estimated_tokens": self.estimated_tokens,
            "actual_tokens": self.actual_tokens,
            "estimated_duration_seconds": self.estimated_duration_seconds,
            "actual_duration_seconds": self.actual_duration_seconds,
            "assigned_agent": self.assigned_agent,
            "raci_roles": self.raci_roles,
            "tags": self.tags,
            "metadata": self.metadata,
            "require_plan_approval": self.require_plan_approval,
            "queue_preference": self.queue_preference
        }
        
        if self.plan:
            result["plan"] = {
                "plan_id": self.plan.plan_id,
                "proposed_by": self.plan.proposed_by,
                "content": self.plan.content,
                "submitted_at": self.plan.submitted_at.isoformat() if self.plan.submitted_at else None,
                "approved_by": self.plan.approved_by,
                "approved_at": self.plan.approved_at.isoformat() if self.plan.approved_at else None,
                "rejection_reason": self.plan.rejection_reason,
                "status": self.plan.status.value
            }
        
        return result


class WorkQueue:
    def __init__(self):
        self._queue: List[Work] = []
        self._lock = asyncio.Lock()

    async def enqueue(self, work: Work):
        async with self._lock:
            work.status = WorkStatus.QUEUED
            self._queue.append(work)
            self._queue.sort(key=lambda w: w.priority.value)

    async def dequeue(self, agent_capabilities: List[str], completed_work_ids: Optional[set] = None) -> Optional[Work]:
        async with self._lock:
            # Remove completed works from queue
            self._queue = [w for w in self._queue if w.status != WorkStatus.COMPLETED]
            
            completed_ids = completed_work_ids or set()
            for i, work in enumerate(self._queue):
                if work.status == WorkStatus.QUEUED:
                    if work.agent_type in agent_capabilities:
                        if work.can_start(completed_ids):
                            return self._queue.pop(i)
            return None

    async def peek(self) -> Optional[Work]:
        async with self._lock:
            for work in self._queue:
                if work.status == WorkStatus.QUEUED:
                    return work
            return None

    async def get_pending_count(self) -> int:
        async with self._lock:
            return sum(1 for w in self._queue if w.status in [WorkStatus.PENDING, WorkStatus.QUEUED])

    async def get_blocked_works(self) -> List[Work]:
        async with self._lock:
            completed_ids = {w.work_id for w in self._queue if w.status == WorkStatus.COMPLETED}
            return [w for w in self._queue if not w.can_start(completed_ids)]
