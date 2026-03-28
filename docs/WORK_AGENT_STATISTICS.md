# Work-Agent Statistics Feature

## Overview

Through the TOC Manager (TOCSupervisor), you can check statistics on which Agents worked how much for each Work. This feature can be queried only when the user wants.

## Main Features

### 1. Query Individual Work Statistics

Query task statistics of Agents assigned to a specific Work.

```python
from agent_factory.core import TOCSupervisor

toc = TOCSupervisor(agent_pool, work_queue, raci)

# Query statistics for a specific Work
work_stats = toc.get_work_agent_statistics("work_001")

# Formatted report
report = toc.format_work_agent_report("work_001")
print(report)
```

**Output Example:**
```
================================================================================
Work-Agent Statistics Report: work_001
================================================================================

## Summary
  Total activities: 1
  Total tokens used: 1,200
  Total task time: 45.00 seconds

## Statistics by Agent

### dev_agent_1 (design_development)
  Task count: 1
  Tokens used: 1,200
  Task time: 45.00 seconds
  Average tokens/task: 1200
  Average time/task: 45.00 seconds
```

### 2. Query All Work Statistics

Query Agent task statistics for all Works.

```python
# Overall statistics (JSON)
all_stats = toc.get_work_agent_statistics()

# Overall report
report = toc.format_work_agent_report()
print(report)
```

**Output Content:**
- Total Works and activities
- Statistics by Work (tokens used, time, agent type)
- Statistics by Agent Type (total works, distribution by work type)

### 3. JSON Format Statistics

Access statistics data programmatically.

```python
import json

# Overall statistics
stats = toc.get_work_agent_statistics()

print("Overall summary:")
print(json.dumps(stats["summary"], indent=2, ensure_ascii=False))

# Statistics by Work
print("\nStatistics by Work:")
for work_id, work_data in stats["by_work"].items():
    print(f"  {work_id}: {work_data['total_activities']} activities, {work_data['total_tokens']} tokens")

# Statistics by Agent Type
print("\nStatistics by Agent Type:")
for agent_type, type_data in stats["by_agent_type"].items():
    print(f"  {agent_type}: {type_data['total_works']} tasks, {type_data['total_tokens']} tokens")
```

## API

### `TOCSupervisor.get_work_agent_statistics(work_id: Optional[str] = None) -> Dict[str, Any]`

Returns Work-by-Agent task statistics.

**Parameters:**
- `work_id` (Optional[str]): ID of a specific Work. Returns overall statistics if `None`.

**Returns:**
- `Dict[str, Any]`: Statistics data

**Individual Work Statistics Structure:**
```json
{
  "work_id": "work_001",
  "total_activities": 2,
  "total_tokens": 3500,
  "total_duration_seconds": 125.0,
  "agents": {
    "agent_1": {
      "agent_type": "design_development",
      "work_count": 1,
      "total_tokens": 1200,
      "total_duration": 45.0,
      "activities": [...]
    },
    "agent_2": {
      "agent_type": "design_development",
      "work_count": 1,
      "total_tokens": 2300,
      "total_duration": 80.0,
      "activities": [...]
    }
  }
}
```

**Overall Statistics Structure:**
```json
{
  "summary": {
    "total_works": 4,
    "total_activities": 4,
    "total_tokens": 6200,
    "total_duration": 215.0
  },
  "by_work": {
    "work_001": {
      "work_type": "design_development",
      "total_activities": 1,
      "total_tokens": 1200,
      "total_duration_seconds": 45.0,
      "agent_types": {"design_development": 1}
    },
    ...
  },
  "by_agent_type": {
    "design_development": {
      "total_works": 2,
      "total_tokens": 3500,
      "total_duration": 125.0,
      "work_types": {"design_development": 2}
    },
    ...
  }
}
```

### `TOCSupervisor.format_work_agent_report(work_id: Optional[str] = None) -> str`

Returns Work-Agent statistics report as a formatted string.

**Parameters:**
- `work_id` (Optional[str]): ID of a specific Work. Returns overall report if `None`.

**Returns:**
- `str`: Formatted report

## Usage Example

```python
import asyncio
from agent_factory.core import (
    TOCSupervisor, AgentPool, WorkQueue, RACI,
    Work, WorkStatus, WorkPriority, WorkResult,
    AgentInstance
)

async def main():
    # Initialize
    agent_pool = AgentPool()
    work_queue = WorkQueue()
    raci = RACI()
    toc = TOCSupervisor(agent_pool, work_queue, raci)

    # Register agent
    agent = AgentInstance(
        agent_id="dev_agent_1",
        agent_type="design_development",
        capabilities=["design", "code"],
        max_concurrent_works=2
    )
    agent_pool.register_agent(agent)

    # Create Work and complete
    work = Work(
        work_id="work_001",
        name="API Design",
        description="REST API design",
        work_type="design_development",
        agent_type="design_development",
        priority=WorkPriority.HIGH
    )

    work.start("dev_agent_1")
    work.actual_tokens = 1200
    work.actual_duration_seconds = 45

    result = WorkResult(
        work_id="work_001",
        status=WorkStatus.COMPLETED,
        output={"success": True}
    )

    # Record Work completion (statistics are recorded at this time)
    toc.record_work_completion(work, result)

    # Query statistics
    print("=== Individual Work Statistics ===")
    print(toc.format_work_agent_report("work_001"))

    print("\n=== Overall Statistics ===")
    print(toc.format_work_agent_report())

if __name__ == "__main__":
    asyncio.run(main())
```

## Notes

1. **Automatic Recording**: When a Work is completed and `record_work_completion()` method is called, statistics are automatically recorded.

2. **On-Demand Query**: Statistics are only calculated when the user calls `get_work_agent_statistics()` or `format_work_agent_report()`.

3. **Memory Storage**: Statistics data are stored within the TOCSupervisor instance. Permanent storage requires separate implementation.

## Statistics Included Items

### Statistics by Work
- Work ID
- Work Type
- Total activities
- Total tokens used
- Total task time
- Participating agent types

### Statistics by Agent
- Agent ID
- Agent Type
- Task count
- Tokens used
- Task time
- Average tokens/task
- Average time/task

### Statistics by Agent Type
- Agent Type
- Total Works
- Total tokens used
- Total task time
- Distribution by work type

## Example File

You can find complete usage examples in the `examples/work_agent_statistics_example.py` file.

```bash
cd $WORKDIR/agent-factory
source venv/bin/activate
python examples/work_agent_statistics_example.py
```
