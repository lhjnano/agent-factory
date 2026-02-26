from typing import Dict, Optional, Any
from .context import WorkContext, WorkflowContext


class ContextManager:
    def __init__(self):
        self._workflow_contexts: Dict[str, WorkflowContext] = {}
        self._memory_storage = None
        self._filesystem_storage = None
    
    def set_mcp_sessions(self, memory_session=None, filesystem_session=None):
        self._memory_storage = memory_session
        self._filesystem_storage = filesystem_session
    
    def create_workflow_context(
        self,
        workflow_id: str,
        name: str,
        description: str = ""
    ) -> WorkflowContext:
        workflow_ctx = WorkflowContext(
            workflow_id=workflow_id,
            name=name,
            description=description
        )
        self._workflow_contexts[workflow_id] = workflow_ctx
        return workflow_ctx
    
    def get_workflow_context(self, workflow_id: str) -> Optional[WorkflowContext]:
        return self._workflow_contexts.get(workflow_id)
    
    def create_work_context(
        self,
        workflow_id: str,
        work_id: str,
        work_type: str,
        inputs: Dict[str, Any],
        dependencies: Optional[list] = None
    ) -> WorkContext:
        workflow_ctx = self._workflow_contexts.get(workflow_id)
        if not workflow_ctx:
            raise ValueError(f"Workflow context not found: {workflow_id}")
        
        work_ctx = WorkContext(
            work_id=work_id,
            work_type=work_type,
            inputs=inputs
        )
        
        if dependencies:
            work_ctx.metadata["dependencies"] = dependencies
            resolved = workflow_ctx.resolve_dependencies(work_id, dependencies)
            work_ctx.extend_context(resolved)
        
        workflow_ctx.add_work_context(work_ctx)
        return work_ctx
    
    def get_work_context(self, workflow_id: str, work_id: str) -> Optional[WorkContext]:
        workflow_ctx = self._workflow_contexts.get(workflow_id)
        if not workflow_ctx:
            return None
        return workflow_ctx.get_work_context(work_id)
    
    def update_work_outputs(
        self,
        workflow_id: str,
        work_id: str,
        outputs: Dict[str, Any],
        propagate_to_global: bool = True
    ):
        workflow_ctx = self._workflow_contexts.get(workflow_id)
        if not workflow_ctx:
            raise ValueError(f"Workflow context not found: {workflow_id}")
        
        work_ctx = workflow_ctx.get_work_context(work_id)
        if not work_ctx:
            raise ValueError(f"Work context not found: {work_id}")
        
        work_ctx.update_outputs(outputs)
        
        if propagate_to_global:
            workflow_ctx.merge_work_outputs_to_global(work_id)
    
    def get_full_context_for_work(self, workflow_id: str, work_id: str) -> Dict[str, Any]:
        workflow_ctx = self._workflow_contexts.get(workflow_id)
        if not workflow_ctx:
            return {}
        return workflow_ctx.get_full_context_for_work(work_id)
    
    def get_global_context(self, workflow_id: str) -> Dict[str, Any]:
        workflow_ctx = self._workflow_contexts.get(workflow_id)
        if not workflow_ctx:
            return {}
        return workflow_ctx.global_context
    
    def add_global_context(self, workflow_id: str, key: str, value: Any):
        workflow_ctx = self._workflow_contexts.get(workflow_id)
        if not workflow_ctx:
            raise ValueError(f"Workflow context not found: {workflow_id}")
        workflow_ctx.add_global_context(key, value)
    
    async def save_workflow_context(self, workflow_id: str):
        import json
        
        workflow_ctx = self._workflow_contexts.get(workflow_id)
        if not workflow_ctx:
            return
        
        data = workflow_ctx.to_dict()
        
        if self._memory_storage:
            try:
                await self._memory_storage.call_tool(
                    "memory_store",
                    arguments={
                        "key": f"workflow_context_{workflow_id}",
                        "value": json.dumps(data)
                    }
                )
            except Exception as e:
                print(f"Warning: Failed to save workflow context to memory: {e}")
        
        if self._filesystem_storage:
            try:
                await self._filesystem_storage.call_tool(
                    "filesystem_write_file",
                    arguments={
                        "path": f"/tmp/agent_factory/workflow_contexts/{workflow_id}.json",
                        "content": json.dumps(data, indent=2, ensure_ascii=False)
                    }
                )
            except Exception as e:
                print(f"Warning: Failed to save workflow context to filesystem: {e}")
    
    async def load_workflow_context(self, workflow_id: str) -> Optional[WorkflowContext]:
        import json
        
        if self._memory_storage:
            try:
                result = await self._memory_storage.call_tool(
                    "memory_retrieve",
                    arguments={"key": f"workflow_context_{workflow_id}"}
                )
                if result and result.content and result.content.text:
                    data = json.loads(result.content.text)
                    workflow_ctx = WorkflowContext.from_dict(data)
                    self._workflow_contexts[workflow_id] = workflow_ctx
                    return workflow_ctx
            except Exception as e:
                print(f"Warning: Failed to load workflow context from memory: {e}")
        
        if self._filesystem_storage:
            try:
                result = await self._filesystem_storage.call_tool(
                    "filesystem_read_file",
                    arguments={"path": f"/tmp/agent_factory/workflow_contexts/{workflow_id}.json"}
                )
                if result and result.content and result.content.text:
                    data = json.loads(result.content.text)
                    workflow_ctx = WorkflowContext.from_dict(data)
                    self._workflow_contexts[workflow_id] = workflow_ctx
                    return workflow_ctx
            except Exception as e:
                print(f"Warning: Failed to load workflow context from filesystem: {e}")
        
        return None
    
    async def save_all_contexts(self):
        for workflow_id in self._workflow_contexts:
            await self.save_workflow_context(workflow_id)
    
    def clear_workflow_context(self, workflow_id: str):
        if workflow_id in self._workflow_contexts:
            del self._workflow_contexts[workflow_id]
    
    def clear_all_contexts(self):
        self._workflow_contexts.clear()
