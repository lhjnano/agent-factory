# Context Management System Implementation

## Overview

This project (`~/source/agent-factory`) implemented the following features to solve the problem of insufficient work-by-work context management.

## Problem Analysis

### Previous Issues

1. **Insufficient Context Sharing Between Works**
   - Dependencies only reference work_id, no mechanism to directly retrieve outputs
   - At `orchestrator.py:168`, only work_id is passed like `inputs={"problem_def": work1.work_id}`

2. **Unable to Accumulate Context**
   - No structure where context accumulates as Work progresses
   - Previous work results are not passed to next work or must be managed manually

3. **Lack of Persistence**
   - Context is managed only in-memory and doesn't use MCP storage

4. **No Workflow-Level Context**
   - Only individual work context exists, insufficient context encompassing entire workflow

## Implementation Details

### 1. WorkContext (`src/agent_factory/core/context.py`)

Class that manages context for individual work

```python
@dataclass
class WorkContext:
    work_id: str
    work_type: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    accumulated_context: Dict[str, Any]  # Accumulating context
    metadata: Dict[str, Any]  # dependencies, etc.
```

**Main Features:**
- `update_outputs()`: Update work results
- `add_to_context()`: Add data to context
- `extend_context()`: Merge context

### 2. WorkflowContext (`src/agent_factory/core/context.py`)

Class that manages context for entire workflow

```python
@dataclass
class WorkflowContext:
    workflow_id: str
    name: str
    description: str
    work_contexts: Dict[str, WorkContext]  # All work contexts
    global_context: Dict[str, Any]  # Global context
    dependency_chain: List[str]
```

**Main Features:**
- `add_work_context()`: Add work context
- `resolve_dependencies()`: Resolve dependencies' outputs
- `get_full_context_for_work()`: Return full context needed for work execution
- `merge_work_outputs_to_global()`: Merge work results into global context

### 3. ContextManager (`src/agent_factory/core/context_manager.py`)

Manages contexts and supports persistence

```python
class ContextManager:
    def __init__(self):
        self._workflow_contexts: Dict[str, WorkflowContext] = {}
        self._memory_storage = None
        self._filesystem_storage = None
```

**Main Features:**
- `create_workflow_context()`: Create workflow context
- `create_work_context()`: Create work context and resolve dependencies
- `update_work_outputs()`: Update work results and propagate to global context
- `get_full_context_for_work()`: Return context needed for work execution
- `save_workflow_context()`: Save context to MCP storage
- `load_workflow_context()`: Load context from MCP storage

### 4. Orchestrator Integration (`src/agent_factory/core/orchestrator.py`)

Integrate ContextManager into MultiAgentOrchestrator

**Changes:**
- Added `self.context_manager = ContextManager()`
- Pass MCP sessions to context_manager in `set_mcp_sessions()`
- Added context creation and injection logic in `_execute_work()`
- Added workflow context creation and storage logic in `execute_workflow()`

**Context Injection Method:**
```python
if self._current_workflow_id:
    work_ctx = self.context_manager.create_work_context(
        workflow_id=self._current_workflow_id,
        work_id=work.work_id,
        work_type=work.work_type,
        inputs=work.inputs,
        dependencies=work.dependencies
    )

    full_context = self.context_manager.get_full_context_for_work(
        self._current_workflow_id,
        work.work_id
    )

    inputs_with_context = {
        **work.inputs,
        "_context": full_context  # Include context when passing to handler
    }
```

## Usage Examples

### Example 1: Basic WorkContext Usage

```python
work_ctx = WorkContext(
    work_id="work_001",
    work_type="data_collection",
    inputs={"source": "data.csv"}
)

work_ctx.update_outputs({"rows": 100, "columns": 5})
work_ctx.add_to_context("summary", {"total_rows": 100})
```

### Example 2: Dependency Resolution via WorkflowContext

```python
workflow_ctx = WorkflowContext(
    workflow_id="workflow_001",
    name="ML Pipeline"
)

# data_collection work
work1 = WorkContext(work_id="data_collection", ...)
work1.update_outputs({"data": [[1, 2], [3, 4]]})
workflow_ctx.add_work_context(work1)

# preprocessing work (depends on data_collection)
work2 = WorkContext(
    work_id="preprocessing",
    inputs={"data": "data_collection"}
)
work2.metadata["dependencies"] = ["data_collection"]

resolved = workflow_ctx.resolve_dependencies(
    "preprocessing",
    ["data_collection"]
)
# resolved: {'data_collection': {'outputs': {...}, 'accumulated': {...}}}
```

### Example 3: Using ContextManager

```python
ctx_manager = ContextManager()

# Create workflow context
ctx_manager.create_workflow_context(
    workflow_id="workflow_002",
    name="Image Classification"
)

# Create work context and resolve dependencies
ctx_manager.create_work_context(
    workflow_id="workflow_002",
    work_id="train_model",
    work_type="training",
    inputs={"model_config": "resnet50"},
    dependencies=["data_prep"]
)

# Update work results
ctx_manager.update_work_outputs(
    "workflow_002",
    "data_prep",
    {"train_images": 1000, "val_images": 200}
)

# Get full context needed for work execution
full_ctx = ctx_manager.get_full_context_for_work(
    "workflow_002",
    "train_model"
)
```

### Example 4: Context Accumulation and Propagation

```python
# Context accumulates as each work completes
for work in works:
    ctx_manager.create_work_context(
        workflow_id="workflow_003",
        work_id=work["id"],
        work_type=work["type"],
        inputs=work["inputs"],
        dependencies=work.get("deps", [])
    )

    ctx_manager.update_work_outputs(
        "workflow_003",
        work["id"],
        outputs[work["id"]]
    )

    # Previous work results accumulate in global context
    print(ctx_manager.get_global_context("workflow_003"))
    # {'collect': {...}, 'process': {...}, 'analyze': {...}, ...}
```

## Persistence Support

### Memory Storage
```python
await ctx_manager.save_workflow_context(workflow_id)
await ctx_manager.load_workflow_context(workflow_id)
```

### Filesystem Storage
```python
await ctx_manager.save_workflow_context(workflow_id)
# Saved to /tmp/agent_factory/workflow_contexts/{workflow_id}.json
```

## Using Context in Work Handler

Access context via `_context` key in work handler:

```python
async def my_handler(inputs: Dict[str, Any], agent: AgentInstance):
    context = inputs.get("_context", {})

    work_inputs = context.get("work_inputs", {})
    global_context = context.get("global_context", {})
    dependencies = context.get("resolved_dependencies", {})

    # Use outputs from dependencies
    prev_outputs = dependencies.get("dependency_work_id", {}).get("outputs", {})

    # Perform processing
    result = process(work_inputs, prev_outputs, global_context)

    return result
```

## File Structure

```
src/agent_factory/core/
├── context.py              # WorkContext, WorkflowContext
├── context_manager.py      # ContextManager
├── work.py                # (Existing file, unchanged)
├── orchestrator.py         # ContextManager integration
└── __init__.py            # Export additions

example_context_standalone.py  # Example code
```

## Summary of Main Methods

### WorkContext
- `update_outputs(outputs)`: Update outputs
- `add_to_context(key, value)`: Add data to context
- `extend_context(context)`: Merge context
- `get_full_context()`: Return full context

### WorkflowContext
- `add_work_context(work_context)`: Add work context
- `get_work_context(work_id)`: Retrieve work context
- `get_work_outputs(work_id)`: Retrieve work outputs
- `resolve_dependencies(work_id, dependency_ids)`: Resolve dependencies
- `add_global_context(key, value)`: Add to global context
- `get_full_context_for_work(work_id)`: Return full context needed for work execution
- `merge_work_outputs_to_global(work_id)`: Merge work results into global context

### ContextManager
- `set_mcp_sessions(memory_session, filesystem_session)`: Set MCP sessions
- `create_workflow_context(workflow_id, name, description)`: Create workflow context
- `get_workflow_context(workflow_id)`: Retrieve workflow context
- `create_work_context(workflow_id, work_id, work_type, inputs, dependencies)`: Create work context
- `get_work_context(workflow_id, work_id)`: Retrieve work context
- `update_work_outputs(workflow_id, work_id, outputs, propagate_to_global)`: Update work results
- `get_full_context_for_work(workflow_id, work_id)`: Return context needed for work execution
- `get_global_context(workflow_id)`: Retrieve global context
- `add_global_context(workflow_id, key, value)`: Add to global context
- `save_workflow_context(workflow_id)`: Save workflow context
- `load_workflow_context(workflow_id)`: Load workflow context
- `save_all_contexts()`: Save all contexts
- `clear_workflow_context(workflow_id)`: Delete workflow context
- `clear_all_contexts()`: Delete all contexts

## Running Tests

```bash
cd ~/source/agent-factory
python3 example_context_standalone.py
```

## Future Improvements

1. **Context Size Limit**: Size limits and pruning functionality to prevent overly large contexts
2. **Context TTL**: Automatically delete contexts after certain time
3. **Context Versioning**: Context version management and rollback support
4. **Context Compression**: Context compression to optimize token usage
5. **Context Visualization**: Context visualization tools

## Conclusion

Through this Context Management System:
- Context sharing between Works is automated
- Context accumulates as Work progresses
- Context is permanently stored
- Context can be managed at the workflow level
- Easy access to context in work handlers
