# API Reference - Agent Factory v2.1

## 📚 Table of Contents

- [Queue System](#queue-system)
- [Retry System](#retry-system)
- [Scaling System](#scaling-system)
- [Scheduler System](#scheduler-system)
- [Worker System](#worker-system)
- [MCP Tools](#mcp-tools)

---

## Queue System

### `MultiQueueManager`

Manages multiple queues with different strategies.

```python
from agent_factory.core.queue import MultiQueueManager, MultiQueueConfig, QueueStrategy

config = MultiQueueConfig(
    strategy=QueueStrategy.PRIORITY_FIRST,
    enable_priority_queue=True,
    enable_type_queue=True
)
queue_manager = MultiQueueManager(config)
```

#### Methods

| Method | Parameters | Returns | Description |
|--------|-----------|----------|-------------|
| `enqueue(work, priority=None, queue_type=None)` | `work: Work`, `priority: WorkPriority`, `queue_type: str` | `None` | Add work to queue |
| `dequeue(agent_capabilities, completed_work_ids)` | `agent_capabilities: List[str]`, `completed_work_ids: Set[str]` | `Optional[Work]` | Get next work to execute |
| `peek()` | None | `Optional[Work]` | Preview next work without removing |
| `get_stats()` | None | `Dict[str, Any]` | Get queue statistics |
| `clear()` | None | `None` | Clear all queues |

#### Example

```python
await queue_manager.enqueue(
    work=my_work,
    priority=WorkPriority.HIGH,
    queue_type="design_development"
)

work = await queue_manager.dequeue(
    agent_capabilities=["design_development"],
    completed_work_ids={"work_1", "work_2"}
)

stats = await queue_manager.get_stats()
# Returns: {"total_works": 10, "pending_works": 5, "by_priority": {...}, "by_type": {...}}
```

---

### `PriorityQueue`

Priority-based queue implementation.

```python
from agent_factory.core.queue import PriorityQueue, PriorityLevel

priority_queue = PriorityQueue()
await priority_queue.enqueue(work, priority=PriorityLevel.HIGH)
work = await priority_queue.dequeue()
```

#### Priority Levels

- `CRITICAL` - Highest priority (value: 1)
- `HIGH` - High priority (value: 2)
- `MEDIUM` - Medium priority (value: 3)
- `LOW` - Low priority (value: 4)

---

### `TypeQueue`

Work type-based queue categorization.

```python
from agent_factory.core.queue import TypeQueue

type_queue = TypeQueue()
await type_queue.enqueue(work, work_type="design_development")
work = await type_queue.dequeue(work_type="design_development")
```

---

## Retry System

### `RetryPolicy`

Defines retry behavior.

```python
from agent_factory.core.retry import RetryPolicy, RetryStrategy

policy = RetryPolicy(
    max_retries=3,
    strategy=RetryStrategy.EXPONENTIAL,
    base_delay=1.0,
    max_delay=60.0,
    retry_on_errors=["timeout", "rate_limit", "connection_error"]
)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_retries` | `int` | 3 | Maximum number of retry attempts |
| `strategy` | `RetryStrategy` | `EXPONENTIAL` | Retry backoff strategy |
| `base_delay` | `float` | 1.0 | Base delay in seconds |
| `max_delay` | `float` | 60.0 | Maximum delay in seconds |
| `retry_on_errors` | `List[str]` | `["timeout", "rate_limit", "connection_error"]` | Error types to retry |

#### Retry Strategies

- `EXPONENTIAL` - Exponential backoff: `base_delay * 2^(retry_count - 1)`
- `LINEAR` - Linear backoff: `base_delay * retry_count`
- `CONSTANT` - Constant delay: `base_delay`

#### Methods

| Method | Parameters | Returns | Description |
|--------|-----------|----------|-------------|
| `get_delay(retry_count)` | `retry_count: int` | `float` | Get delay for given retry attempt |
| `should_retry(error)` | `error: Exception` | `bool` | Check if error should trigger retry |
| `to_dict()` | None | `Dict[str, Any]` | Convert policy to dictionary |

---

### `RetryManager`

Manages retry attempts and history.

```python
from agent_factory.core.retry import RetryManager

retry_manager = RetryManager(default_policy=policy)
retry_manager.record_retry(work_id="work_123", error=TimeoutError("Timeout"))
can_retry = retry_manager.can_retry(work_id="work_123")
delay = retry_manager.get_next_delay(work_id="work_123")
```

#### Methods

| Method | Parameters | Returns | Description |
|--------|-----------|----------|-------------|
| `record_retry(work_id, error, policy)` | `work_id: str`, `error: Exception`, `policy: Optional[RetryPolicy]` | `None` | Record a retry attempt |
| `get_retry_count(work_id)` | `work_id: str` | `int` | Get number of retry attempts |
| `can_retry(work_id, policy)` | `work_id: str`, `policy: Optional[RetryPolicy]` | `bool` | Check if work can be retried |
| `get_next_delay(work_id, policy)` | `work_id: str`, `policy: Optional[RetryPolicy]` | `float` | Get delay for next retry |
| `get_stats()` | None | `Dict[str, Any]` | Get retry statistics |

---

### `TimeoutStrategy`

Manages timeout settings per work.

```python
from agent_factory.core.retry import TimeoutStrategy

timeout_strategy = TimeoutStrategy(default_timeout=300.0)
timeout_strategy.set_timeout(work_id="work_123", timeout=600.0)
timeout = timeout_strategy.get_timeout(work_id="work_123")
```

#### Methods

| Method | Parameters | Returns | Description |
|--------|-----------|----------|-------------|
| `set_timeout(work_id, timeout)` | `work_id: str`, `timeout: float` | `None` | Set timeout for work |
| `get_timeout(work_id)` | `work_id: str` | `float` | Get timeout for work |
| `clear_timeout(work_id)` | `work_id: str` | `None` | Clear timeout for work |
| `get_stats()` | None | `Dict[str, Any]` | Get timeout statistics |

---

## Scaling System

### `AutoScaler`

Automatically scales agent pool based on metrics.

```python
from agent_factory.core.scaling import AutoScaler, ScalingPolicy

auto_scaler = AutoScaler(agent_pool=pool, policy=policy)
decision = await auto_scaler.evaluate_scaling()
if decision.action == "scale_up":
    await auto_scaler.scale_up(count=1)
```

#### Methods

| Method | Parameters | Returns | Description |
|--------|-----------|----------|-------------|
| `evaluate_scaling()` | None | `ScalingDecision` | Evaluate and decide scaling action |
| `scale_up(count)` | `count: int` | `None` | Add agents to pool |
| `scale_down(count)` | `count: int` | `None` | Remove agents from pool |
| `get_stats()` | None | `Dict[str, Any]` | Get scaling statistics |

---

### `ScalingPolicy`

Defines scaling rules and thresholds.

```python
from agent_factory.core.scaling import ScalingPolicy, ScalingMetric, ScalingThresholds

policy = ScalingPolicy(
    metric=ScalingMetric.QUEUE_LENGTH,
    scale_up_threshold=10,
    scale_down_threshold=3,
    cooldown_seconds=60
)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `metric` | `ScalingMetric` | `QUEUE_LENGTH` | Metric to evaluate |
| `scale_up_threshold` | `float` | 10.0 | Threshold to scale up |
| `scale_down_threshold` | `float` | 3.0 | Threshold to scale down |
| `cooldown_seconds` | `float` | 60.0 | Cooldown period between scales |

#### Scaling Metrics

- `QUEUE_LENGTH` - Scale based on queue size
- `WORKER_UTILIZATION` - Scale based on worker busy ratio
- `TOKEN_THROUGHPUT` - Scale based on token processing rate
- `COMPLETION_RATE` - Scale based on work completion rate

---

### `ScalingDecision`

Result of scaling evaluation.

```python
@dataclass
class ScalingDecision:
    action: str  # "scale_up", "scale_down", "no_action"
    current_value: float
    threshold: float
    reason: str
    recommended_count: int
```

---

## Scheduler System

### `CompositeScheduler`

Combines multiple scheduling strategies.

```python
from agent_factory.core.scheduler import CompositeScheduler, SchedulerConfig

config = SchedulerConfig(
    strategies=["token_aware", "dependency_aware"],
    weights=[0.6, 0.4]
)
scheduler = CompositeScheduler(config)
result = await scheduler.schedule(works, agent_pool)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `strategies` | `List[str]` | `["token_aware"]` | List of scheduling strategies |
| `weights` | `List[float]` | `[1.0]` | Weights for each strategy |

#### Scheduling Strategies

- `SJF` - Shortest Job First
- `TOKEN_AWARE` - Token-efficient scheduling
- `DEPENDENCY_AWARE` - Dependency-aware scheduling
- `COMPOSITE` - Combine multiple strategies

---

### `TokenAwareScheduler`

Optimizes token usage efficiency.

```python
from agent_factory.core.scheduler import TokenAwareScheduler

scheduler = TokenAwareScheduler()
result = await scheduler.schedule(works, agent_pool)
# Groups similar works to minimize redundant tokens
```

---

### `DependencyAwareScheduler`

Respects work dependencies.

```python
from agent_factory.core.scheduler import DependencyAwareScheduler

scheduler = DependencyAwareScheduler()
result = await scheduler.schedule(works, agent_pool)
# Ensures dependent works are scheduled after prerequisites
```

---

## Worker System

### `WorkerPool`

Manages multiple workers.

```python
from agent_factory.core.worker import WorkerPool, LLMWorker

pool = WorkerPool(max_workers=10)
pool.register_worker(LLMWorker(worker_id="llm_1", agent_type="design_development"))
result = await pool.execute(work)
```

#### Methods

| Method | Parameters | Returns | Description |
|--------|-----------|----------|-------------|
| `register_worker(worker)` | `worker: BaseWorker` | `None` | Register a new worker |
| `get_available_worker()` | None | `Optional[BaseWorker]` | Get next available worker |
| `execute(work)` | `work: Work` | `WorkerResult` | Execute work with best worker |
| `remove_worker(worker_id)` | `worker_id: str` | `None` | Remove worker from pool |
| `get_stats()` | None | `Dict[str, Any]` | Get pool statistics |

---

### `LLMWorker`

LLM-based AI worker.

```python
from agent_factory.core.worker import LLMWorker, LLMWorkerConfig

config = LLMWorkerConfig(
    worker_id="llm_1",
    agent_type="design_development",
    max_concurrent_tasks=3
)
worker = LLMWorker(config=config)
result = await worker.execute(work)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `worker_id` | `str` | Required | Unique worker identifier |
| `agent_type` | `str` | Required | Type of agent this worker represents |
| `max_concurrent_tasks` | `int` | 1 | Maximum concurrent tasks |

---

### `ExecutionWorker`

Code/script execution worker.

```python
from agent_factory.core.worker import ExecutionWorker, ExecutionWorkerConfig

config = ExecutionWorkerConfig(
    worker_id="exec_1",
    allowed_commands=["python", "node", "bash"],
    timeout_seconds=60.0
)
worker = ExecutionWorker(config=config)
result = await worker.execute(work)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `worker_id` | `str` | Required | Unique worker identifier |
| `allowed_commands` | `List[str]` | `["python"]` | Allowed commands to execute |
| `timeout_seconds` | `float` | 300.0 | Default timeout for execution |

---

### `ValidationWorker`

Output validation worker.

```python
from agent_factory.core.worker import ValidationWorker, ValidationWorkerConfig

config = ValidationWorkerConfig(
    worker_id="valid_1",
    strict_mode=True
)
worker = ValidationWorker(config=config)

# Register validator
worker.register_validator("design_development", lambda output: "file_count" in output)
```

#### Methods

| Method | Parameters | Returns | Description |
|--------|-----------|----------|-------------|
| `register_validator(work_type, validator)` | `work_type: str`, `validator: Callable` | `None` | Register output validator |
| `validate_work(work, output)` | `work: Work`, `output: Any` | `bool` | Validate work output |

---

## MCP Tools

### `execute_workflow`

Execute complete development workflow from problem definition to deployment.

```python
{
  "name": "execute_workflow",
  "description": "Execute complete development workflow from problem definition to deployment",
  "inputSchema": {
    "type": "object",
    "properties": {
      "user_request": {
        "type": "string",
        "description": "User's problem statement or requirements"
      }
    },
    "required": ["user_request"]
  }
}
```

#### Example

```python
tool_call = {
  "tool": "execute_workflow",
  "arguments": {
    "user_request": "Build a REST API for user management"
  }
}
```

---

### `define_problem`

Define problem scope and create project plan.

```python
{
  "name": "define_problem",
  "description": "Define problem scope and create project plan with phases and timeline",
  "inputSchema": {
    "type": "object",
    "properties": {
      "requirements": {
        "type": "string",
        "description": "Project requirements and objectives"
      }
    },
    "required": ["requirements"]
  }
}
```

---

### `collect_data`

Collect data from various sources.

```python
{
  "name": "collect_data",
  "description": "Collect data from various sources",
  "inputSchema": {
    "type": "object",
    "properties": {
      "sources": {
        "type": "array",
        "items": {"type": "string"},
        "description": "List of data sources (file paths or URLs)"
      }
    },
    "required": ["sources"]
  }
}
```

---

### `preprocess_data`

Preprocess collected data.

```python
{
  "name": "preprocess_data",
  "description": "Preprocess collected data",
  "inputSchema": {
    "type": "object",
    "properties": {
      "data_path": {
        "type": "string",
        "description": "Path to raw data file"
      }
    },
    "required": ["data_path"]
  }
}
```

---

### `design_architecture`

Design system architecture based on problem definition.

```python
{
  "name": "design_architecture",
  "description": "Design system architecture based on problem definition",
  "inputSchema": {
    "type": "object",
    "properties": {
      "problem_def": {
        "type": "object",
        "description": "Problem definition with input/output specifications"
      }
    },
    "required": ["problem_def"]
  }
}
```

---

### `generate_implementation`

Generate code implementation.

```python
{
  "name": "generate_implementation",
  "description": "Generate code implementation including core logic and scripts",
  "inputSchema": {
    "type": "object",
    "properties": {
      "architecture": {
        "type": "object",
        "description": "System architecture configuration"
      }
    },
    "required": ["architecture"]
  }
}
```

---

### `optimize_process`

Run process with configuration and optimization.

```python
{
  "name": "optimize_process",
  "description": "Run process with configuration and optimization",
  "inputSchema": {
    "type": "object",
    "properties": {
      "config": {
        "type": "object",
        "description": "Process configuration (epochs, iterations, parameters)"
      }
    },
    "required": ["config"]
  }
}
```

---

### `evaluate_results`

Evaluate performance and generate detailed report.

```python
{
  "name": "evaluate_results",
  "description": "Evaluate performance and generate detailed report",
  "inputSchema": {
    "type": "object",
    "properties": {
      "output_path": {
        "type": "string",
        "description": "Path to process output or results"
      },
      "test_data_path": {
        "type": "string",
        "description": "Path to test data (if applicable)"
      }
    },
    "required": ["output_path"]
  }
}
```

---

### `deploy_system`

Deploy system to production environment.

```python
{
  "name": "deploy_system",
  "description": "Deploy system to production environment",
  "inputSchema": {
    "type": "object",
    "properties": {
      "artifact_path": {
        "type": "string",
        "description": "Path to deployable artifact or file"
      },
      "config": {
        "type": "object",
        "description": "Deployment configuration (version, environment, endpoint)"
      }
    },
    "required": ["artifact_path"]
  }
}
```

---

### `monitor_system`

Monitor deployed system performance and metrics.

```python
{
  "name": "monitor_system",
  "description": "Monitor deployed system performance and metrics",
  "inputSchema": {
    "type": "object",
    "properties": {
      "version": {
        "type": "string",
        "description": "System version to monitor"
      }
    },
    "required": ["version"]
  }
}
```

---

### `assign_skills_to_work`

Assign skills to a work.

```python
{
  "name": "assign_skills_to_work",
  "description": "Assign skills to a work",
  "inputSchema": {
    "type": "object",
    "properties": {
      "work_id": {
        "type": "string",
        "description": "Work ID to assign skills to"
      },
      "consultant_agent_id": {
        "type": "string",
        "description": "Agent ID of the consultant making the assignment"
      }
    },
    "required": ["work_id"]
  }
}
```

---

### `get_work_skills`

Get work skill information.

```python
{
  "name": "get_work_skills",
  "description": "Get work skill information",
  "inputSchema": {
    "type": "object",
    "properties": {
      "work_id": {
        "type": "string",
        "description": "Work ID to get skills for"
      }
    },
    "required": ["work_id"]
  }
}
```

---

### `get_skill_effectiveness`

Get skill effectiveness metrics.

```python
{
  "name": "get_skill_effectiveness",
  "description": "Get skill effectiveness metrics",
  "inputSchema": {
    "type": "object",
    "properties": {
      "skill_name": {
        "type": "string",
        "description": "Specific skill name (optional, returns all if not provided)"
      }
    }
  }
}
```

---

### `analyze_work_for_skills`

Analyze work and recommend skills.

```python
{
  "name": "analyze_work_for_skills",
  "description": "Analyze work and recommend skills",
  "inputSchema": {
    "type": "object",
    "properties": {
      "work_name": {
        "type": "string",
        "description": "Name of the work"
      },
      "work_description": {
        "type": "string",
        "description": "Detailed description of the work"
      },
      "work_type": {
        "type": "string",
        "description": "Type of work (e.g., problem_definition, design_development)"
      },
      "tags": {
        "type": "array",
        "items": {"type": "string"},
        "description": "List of tags associated with the work"
      }
    },
    "required": ["work_name", "work_description", "work_type"]
  }
}
```

---

**Version**: 2.1.0
**Last Updated**: 2026-03-28
