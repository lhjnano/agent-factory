from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Set, Optional, Any
from datetime import datetime


class RACIRole(Enum):
    RESPONSIBLE = "R"
    ACCOUNTABLE = "A"
    CONSULTED = "C"
    INFORMED = "I"


@dataclass
class RACIAssignment:
    work_id: str
    agent_id: str
    role: RACIRole
    assigned_at: datetime = field(default_factory=datetime.now)
    notes: str = ""


@dataclass
class RACIMatrix:
    work_id: str
    assignments: Dict[str, RACIRole] = field(default_factory=dict)
    
    def get_responsible(self) -> List[str]:
        return [aid for aid, role in self.assignments.items() if role == RACIRole.RESPONSIBLE]
    
    def get_accountable(self) -> Optional[str]:
        for aid, role in self.assignments.items():
            if role == RACIRole.ACCOUNTABLE:
                return aid
        return None
    
    def get_consulted(self) -> List[str]:
        return [aid for aid, role in self.assignments.items() if role == RACIRole.CONSULTED]
    
    def get_informed(self) -> List[str]:
        return [aid for aid, role in self.assignments.items() if role == RACIRole.INFORMED]
    
    def validate(self) -> List[str]:
        errors = []
        responsible = self.get_responsible()
        accountable = self.get_accountable()
        
        if len(responsible) == 0:
            errors.append(f"Work {self.work_id}: No RESPONSIBLE agent assigned")
        
        if accountable is None:
            errors.append(f"Work {self.work_id}: No ACCOUNTABLE agent assigned")
        
        if len(responsible) > 3:
            errors.append(f"Work {self.work_id}: Too many RESPONSIBLE agents ({len(responsible)}), max 3")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "work_id": self.work_id,
            "assignments": {aid: role.value for aid, role in self.assignments.items()},
            "R": self.get_responsible(),
            "A": self.get_accountable(),
            "C": self.get_consulted(),
            "I": self.get_informed()
        }


class RACI:
    def __init__(self):
        self._matrix: Dict[str, RACIMatrix] = {}
        self._agent_works: Dict[str, Set[str]] = {}
        self._work_agents: Dict[str, Set[str]] = {}
    
    def assign(self, work_id: str, agent_id: str, role: RACIRole):
        if work_id not in self._matrix:
            self._matrix[work_id] = RACIMatrix(work_id=work_id)
        
        self._matrix[work_id].assignments[agent_id] = role
        
        if agent_id not in self._agent_works:
            self._agent_works[agent_id] = set()
        self._agent_works[agent_id].add(work_id)
        
        if work_id not in self._work_agents:
            self._work_agents[work_id] = set()
        self._work_agents[work_id].add(agent_id)
    
    def unassign(self, work_id: str, agent_id: str):
        if work_id in self._matrix:
            self._matrix[work_id].assignments.pop(agent_id, None)
        
        if agent_id in self._agent_works:
            self._agent_works[agent_id].discard(work_id)
        
        if work_id in self._work_agents:
            self._work_agents[work_id].discard(agent_id)
    
    def get_matrix(self, work_id: str) -> Optional[RACIMatrix]:
        return self._matrix.get(work_id)
    
    def get_agent_role(self, work_id: str, agent_id: str) -> Optional[RACIRole]:
        matrix = self._matrix.get(work_id)
        if matrix:
            return matrix.assignments.get(agent_id)
        return None
    
    def get_agent_works(self, agent_id: str, role: Optional[RACIRole] = None) -> List[str]:
        work_ids = self._agent_works.get(agent_id, set())
        if role:
            return [wid for wid in work_ids if self.get_agent_role(wid, agent_id) == role]
        return list(work_ids)
    
    def get_work_agents(self, work_id: str, role: Optional[RACIRole] = None) -> List[str]:
        agent_ids = self._work_agents.get(work_id, set())
        if role:
            return [aid for aid in agent_ids if self.get_agent_role(work_id, aid) == role]
        return list(agent_ids)
    
    def validate_all(self) -> Dict[str, List[str]]:
        errors = {}
        for work_id, matrix in self._matrix.items():
            validation_errors = matrix.validate()
            if validation_errors:
                errors[work_id] = validation_errors
        return errors
    
    def get_workload_summary(self) -> Dict[str, Dict[RACIRole, int]]:
        summary = {}
        for agent_id, work_ids in self._agent_works.items():
            workload = {role: 0 for role in RACIRole}
            for work_id in work_ids:
                role = self.get_agent_role(work_id, agent_id)
                if role:
                    workload[role] += 1
            summary[agent_id] = workload
        return summary
    
    def suggest_assignment(self, work_id: str, agent_workload: Dict[str, int]) -> List[str]:
        suggestions = []
        sorted_agents = sorted(agent_workload.items(), key=lambda x: x[1])
        
        for agent_id, _ in sorted_agents[:3]:
            suggestions.append(agent_id)
        
        return suggestions

    def get_responsible_agents_for_plan_submission(self, work_id: str) -> List[str]:
        return self.get_work_agents(work_id, RACIRole.RESPONSIBLE)

    def get_accountable_agent_for_plan_approval(self, work_id: str) -> Optional[str]:
        matrix = self.get_matrix(work_id)
        if matrix:
            return matrix.get_accountable()
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            work_id: matrix.to_dict()
            for work_id, matrix in self._matrix.items()
        }
