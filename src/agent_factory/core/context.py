from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import json


@dataclass
class WorkContext:
    work_id: str
    work_type: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    accumulated_context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def update_outputs(self, outputs: Dict[str, Any]):
        self.outputs.update(outputs)
        self.updated_at = datetime.now()
    
    def add_to_context(self, key: str, value: Any):
        self.accumulated_context[key] = value
        self.updated_at = datetime.now()
    
    def extend_context(self, context: Dict[str, Any]):
        self.accumulated_context.update(context)
        self.updated_at = datetime.now()
    
    def get_full_context(self) -> Dict[str, Any]:
        return {
            "inputs": self.inputs,
            "outputs": self.outputs,
            "accumulated": self.accumulated_context,
            "metadata": self.metadata
        }
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "work_id": self.work_id,
            "work_type": self.work_type,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "accumulated_context": self.accumulated_context,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkContext':
        created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now()
        updated_at = datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now()
        
        return cls(
            work_id=data["work_id"],
            work_type=data["work_type"],
            inputs=data.get("inputs", {}),
            outputs=data.get("outputs", {}),
            accumulated_context=data.get("accumulated_context", {}),
            metadata=data.get("metadata", {}),
            created_at=created_at,
            updated_at=updated_at
        )


@dataclass
class WorkflowContext:
    workflow_id: str
    name: str
    description: str = ""
    work_contexts: Dict[str, WorkContext] = field(default_factory=dict)
    global_context: Dict[str, Any] = field(default_factory=dict)
    dependency_chain: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_work_context(self, work_context: WorkContext):
        self.work_contexts[work_context.work_id] = work_context
        self.updated_at = datetime.now()
    
    def get_work_context(self, work_id: str) -> Optional[WorkContext]:
        return self.work_contexts.get(work_id)
    
    def get_work_outputs(self, work_id: str) -> Dict[str, Any]:
        context = self.work_contexts.get(work_id)
        return context.outputs if context else {}
    
    def resolve_dependencies(self, work_id: str, dependency_ids: List[str]) -> Dict[str, Any]:
        resolved_context = {}
        
        for dep_id in dependency_ids:
            dep_context = self.work_contexts.get(dep_id)
            if dep_context:
                resolved_context[dep_id] = {
                    "outputs": dep_context.outputs,
                    "accumulated": dep_context.accumulated_context
                }
        
        return resolved_context
    
    def add_global_context(self, key: str, value: Any):
        self.global_context[key] = value
        self.updated_at = datetime.now()
    
    def get_full_context_for_work(self, work_id: str) -> Dict[str, Any]:
        work_context = self.work_contexts.get(work_id)
        if not work_context:
            return {}
        
        return {
            "work_inputs": work_context.inputs,
            "global_context": self.global_context,
            "resolved_dependencies": self.resolve_dependencies(work_id, work_context.metadata.get("dependencies", []))
        }
    
    def merge_work_outputs_to_global(self, work_id: str, keys: Optional[List[str]] = None):
        work_context = self.work_contexts.get(work_id)
        if not work_context:
            return
        
        if keys:
            for key in keys:
                if key in work_context.outputs:
                    self.global_context[f"{work_id}.{key}"] = work_context.outputs[key]
        else:
            self.global_context[work_id] = work_context.outputs
        
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "work_contexts": {
                wid: ctx.to_dict() for wid, ctx in self.work_contexts.items()
            },
            "global_context": self.global_context,
            "dependency_chain": self.dependency_chain,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowContext':
        created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now()
        updated_at = datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now()
        
        work_contexts = {}
        for wid, ctx_data in data.get("work_contexts", {}).items():
            work_contexts[wid] = WorkContext.from_dict(ctx_data)
        
        return cls(
            workflow_id=data["workflow_id"],
            name=data["name"],
            description=data.get("description", ""),
            work_contexts=work_contexts,
            global_context=data.get("global_context", {}),
            dependency_chain=data.get("dependency_chain", []),
            created_at=created_at,
            updated_at=updated_at
        )
