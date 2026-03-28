# Agent-Factory - MCP Server

Work-based Multi-Agent Automation Platform - TOC (Theory of Constraints) Based Optimization, RACI Matrix, Automatic Documentation Support

## Quick Start

### Installation

**Method 1: Full Installation (Including PostgreSQL)**

```bash
cd <agent_factory_directory>
./setup-mcp.sh
```

PostgreSQL runs in following three ways:
1. **Docker Compose** (Recommended): Use `docker-compose.yml` file
2. **Docker**: Run with `docker run` command
3. **System**: System PostgreSQL service (if installed)

If PostgreSQL is not installed, a warning is displayed, and it runs without database.

---

**Method 2: Run PostgreSQL with Docker Compose (Recommended)**

```bash
cd <agent_factory_directory>

# Start PostgreSQL with Docker Compose
docker compose up -d

# Or docker-compose (old version)
docker-compose up -d

# Stop PostgreSQL
docker compose down
```

---

**Method 3: Run PostgreSQL with Docker**

```bash
docker run -d \
  --name agent-postgres \
  -e POSTGRES_PASSWORD=whiteduck \
  -e POSTGRES_DB=postgres \
  -p 5432:5432 \
  postgres:15-alpine
```

---

**Method 4: Use System PostgreSQL**

```bash
# PostgreSQL installation (Ubuntu/Debian)
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL
sudo systemctl start postgresql
```

---

**Configuration After Installation**

```bash
# Test MCP server
source venv/bin/activate
python -m agent_factory.mcp_server

# Or automatically loaded in OpenCode
```

### Using in OpenCode

The MCP server is automatically connected to OpenCode:

1. OpenCode configuration: `~/.config/opencode/mcp.json`
2. All tools are automatically loaded

## System Architecture

### Core Components

| Component | Description |
|-----------|-------------|
| **Work Queue** | Task (WORK) unit queuing and management |
| **Agent Pool** | Multi-agent deployment and management |
| **RACI Matrix** | Clarify responsibility (Responsible, Accountable, Consulted, Informed) |
| **Documentation Manager** | Automatic document generation after task completion |
| **TOC Supervisor** | Theory of Constraints-based bottleneck analysis and optimization |

### Work-Based Architecture

All tasks are defined in **Work** units:

```python
from agent_factory.core import Work, WorkPriority

work = Work(
    work_id="unique_id",
    name="Task Name",
    description="Task Description",
    work_type="design_development",
    agent_type="design_development",
    priority=WorkPriority.HIGH,
    dependencies=["other_work_id"],
    estimated_tokens=1000
)
```

### Multi-Agent Deployment

Deploy multiple agent instances for parallel processing:

```python
from agent_factory.core import AgentPool, AgentInstance

pool = AgentPool()
agent = AgentInstance(
    agent_id="dev_agent_1",
    agent_type="design_development",
    capabilities=["design", "code_generation"],
    max_concurrent_works=3
)
pool.register_agent(agent)
```

### RACI Matrix

Clear responsibility distribution:

```python
from agent_factory.core import RACI, RACIRole

raci = RACI()
raci.assign("work_1", "agent_a", RACIRole.RESPONSIBLE)
raci.assign("work_1", "agent_b", RACIRole.ACCOUNTABLE)
raci.assign("work_1", "agent_c", RACIRole.CONSULTED)
raci.assign("work_1", "agent_d", RACIRole.INFORMED)
```

## Plan Approval

A process where RESPONSIBLE agent reports plan and expected results before executing development tasks, and receives approval from ACCOUNTABLE agent.

### Plan Approval Workflow

```
1. Work creation → RACI assignment (RESPONSIBLE, ACCOUNTABLE)
2. Set require_plan_approval = True
3. RESPONSIBLE agent submits plan
4. ACCOUNTABLE agent reviews plan and approves/rejects
5. Task execution only if approved
```

### Plan Approval API

```python
# Set plan approval requirement
orchestrator.set_work_plan_approval_required(work_id, True)

# Plan submission (RESPONSIBLE agent)
plan_content = {
    "approach": "Use FastAPI",
    "steps": ["1. Initialize FastAPI app", "2. Define Pydantic models", ...],
    "estimated_files": ["main.py", "models.py"],
    "estimated_hours": 4,
    "risks": ["Database connection delay"],
    "expected_results": "Return GET /api/users response"
}
submit_result = orchestrator.submit_work_plan(
    work_id=work.work_id,
    plan_content=plan_content,
    proposed_by="dev_agent_1"
)

# Plan approval (ACCOUNTABLE agent)
approve_result = orchestrator.approve_work_plan(
    work_id=work.work_id,
    approved_by="senior_agent_1"
)

# Plan rejection (ACCOUNTABLE agent)
reject_result = orchestrator.reject_work_plan(
    work_id=work.work_id,
    rejected_by="senior_agent_1",
    reason="The plan is too insufficient."
)

# Check plan status
plan_status = orchestrator.get_work_plan_status(work_id)
```

### TOC (Theory of Constraints) Optimization

Identify bottlenecks and optimize throughput:

```python
from agent_factory.core import TOCSupervisor

supervisor = TOCSupervisor(pool, queue, raci)
analysis = await supervisor.analyze_system()
optimization = await supervisor.optimize()
```

## Agent Types

| Agent Type | Work Type | Description |
|---------------|-----------|------|
| `problem_definition` | `problem_definition` | Problem definition and planning |
| `data_collection` | `data_collection` | Data collection and preprocessing |
| `design_development` | `design_development` | System design and code implementation |
| `training_optimization` | `training_optimization` | Model training and optimization |
| `evaluation_validation` | `evaluation_validation` | Model evaluation and validation |
| `deployment_monitoring` | `deployment_monitoring` | Deployment and operations monitoring |
| `toc_supervisor` | - | System optimization and general management |

## Workflow Templates

### ML Pipeline

```python
result = await orchestrator.execute_workflow(
    template="ml_pipeline",
    parameters={
        "requirements": "Customer churn prediction model",
        "data_sources": ["/data/customers.csv"]
    }
)
```

### Web Development

```python
result = await orchestrator.execute_workflow(
    template="web_development",
    parameters={
        "requirements": "REST API + React frontend"
    }
)
```

### API Development

```python
result = await orchestrator.execute_workflow(
    template="api_development",
    parameters={
        "api_spec": "User management API"
    }
)
```

### Data Processing

```python
result = await orchestrator.execute_workflow(
    template="data_processing",
    parameters={
        "sources": ["/data/raw", "https://api.example.com/data"]
    }
)
```

## Documentation

### Automatic Documentation

```python
config = WorkflowConfig(auto_document=True)
orchestrator = MultiAgentOrchestrator(config)
result = await orchestrator.execute_workflow(...)
print(result.documents)  # List of generated document IDs
```

### Document Types

| Document Type | Description |
|-----------|------|
| `PROBLEM_DEFINITION` | Problem definition document |
| `PROJECT_PLAN` | Project plan document |
| `DATA_SPECIFICATION` | Data specification document |
| `ARCHITECTURE_DESIGN` | Architecture design document |
| `MODEL_EVALUATION` | Model evaluation report |
| `DEPLOYMENT_GUIDE` | Deployment guide |
| `WORK_SUMMARY` | Task summary |

## TOC Optimization

### Bottleneck Detection

The system automatically detects the following bottlenecks:

- **Agent Capacity**: Insufficient agent capacity
- **Work Dependency**: Waiting due to task dependencies
- **Token Limit**: Token usage limit
- **Queue Overflow**: Queue overflow
- **Imbalanced Load**: Load imbalance

### Final Analysis and Improvement Suggestions

After all Works are completed, TOC Supervisor automatically performs final analysis.

#### Analysis Content

1. **Task Summary**: Total/Completed/Failed/Success rate
2. **Token Efficiency Analysis**:
   - Compare expected vs actual token usage
   - Analyze efficiency by task type
   - Calculate savable tokens
   - Identify inefficient task types

3. **Agent Efficiency Analysis**:
   - Analyze performance by agent
   - Aggregate by agent type
   - Success rate, average token usage, average processing time

4. **Bottleneck Analysis**:
   - Identify agent overload/underutilization
   - Recommend agent count adjustment

5. **Improvement Suggestions**:
   - Token optimization (prompt simplification, context reuse)
   - Agent scaling recommendations
   - Processing speed improvement methods
   - Process improvement suggestions

#### Final Analysis Usage Example

```python
# Automatically perform final analysis after workflow execution
result = await orchestrator.execute_workflow(
    works=works,
    template="ml_pipeline",
    parameters={"requirements": "Image classification model"}
)

# TOC final analysis report is automatically printed to console
# - Task summary
# - Token efficiency analysis
# - Bottleneck analysis
# - Improvement suggestions
# - Comparison with baseline
# - Data storage location
```

#### Data Storage Location

TOC Supervisor stores analysis data in two locations:

**Memory Storage (MCP memory server)**:
- `toc_baselines` - Baseline metrics
- `toc_bottleneck_history` - Bottleneck history
- `toc_optimization_log` - Optimization log
- `toc_work_history` - Work history

**Filesystem Storage** (`~/.agents_toc/`):
- `toc_baselines.json`
- `toc_bottleneck_history.json`
- `toc_optimization_log.json`
- `toc_work_history.json`
- `toc_final_report_<timestamp>.json`

#### Comparison with Baseline (Trend Analysis)

```python
comparison = await toc_supervisor.compare_with_baselines()

# Result:
{
    "improvements": [...],   # Improved metrics
    "degradations": [...],  # Degraded metrics
    "stable": [...]         # Stable metrics
}
```

#### MCP Session Setup

```python
orchestrator.set_mcp_sessions(
    memory_session=memory_client,
    filesystem_session=filesystem_client
)
# - Task summary
# - Token efficiency analysis
# - Bottleneck analysis
# - Improvement suggestions
```

### Automatic Optimization

```python
config = WorkflowConfig(
    enable_toc=True,
    optimization_interval=60.0,
    auto_scale=True
)
```

### Optimization Report

```python
report = supervisor.get_optimization_report()
# {
#   "summary": {
#     "works_completed": 50,
#     "works_per_hour": 12.5,
#     "tokens_per_work": 2500,
#     "success_rate": 0.95
#   },
#   "current_constraint": {...},
#   "recommendations": [...]
# }
```

## Usage Examples

### Basic Usage

```bash
cd <agents_directory>
python examples/basic_usage.py
```

### Plan Approval

```bash
cd <agents_directory>
python examples/plan_approval_example2.py
```

### RACI Matrix

```bash
python examples/raci_example.py
```

### TOC Final Analysis

```bash
cd <agents_directory>
python examples/toc_analysis_example.py
```

### TOC Optimization

```bash
python examples/toc_optimization_example.py
```

### Documentation

```bash
python examples/documentation_example.py
```

### Workflow Templates

```bash
python examples/workflow_templates_example.py
```

## TOC General Agent

```bash
# System analysis
python -m agent_factory.toc_supervisor.agent analyze

# Run optimization
python -m agent_factory.toc_supervisor.agent optimize

# Check bottlenecks
python -m agent_factory.toc_supervisor.agent bottlenecks

# Generate TOC report
python -m agent_factory.toc_supervisor.agent report

# Automatic monitoring
python -m agent_factory.toc_supervisor.agent monitor
```

## Structure

```
<agents_directory>/
├── core/                      # Core system
│   ├── work.py                # Work, WorkQueue, WorkPlan, PlanStatus
│   ├── raci.py                # RACI matrix
│   ├── documentation.py       # Documentation system
│   ├── agent_pool.py          # Agent pool
│   ├── toc_supervisor.py      # TOC general manager (including final analysis)
│   └── orchestrator.py        # Main orchestrator
├── coordinator/               # Coordinator agent
├── problem_definition/        # Problem definition agent
├── data_collection/           # Data collection agent
├── design_development/        # Design/development agent
├── training_optimization/     # Training/optimization agent
├── evaluation_validation/     # Evaluation/validation agent
├── deployment_monitoring/     # Deployment/monitoring agent
├── toc_supervisor/           # TOC general manager agent
├── examples/                 # Usage examples
│   ├── basic_usage.py
│   ├── raci_example.py
│   ├── plan_approval_example2.py  # Plan approval example
│   ├── toc_analysis_example.py      # TOC final analysis example
│   ├── toc_optimization_example.py
│   ├── documentation_example.py
│   └── workflow_templates_example.py
├── ARCHITECTURE.md           # Architecture document (including plan approval, final analysis)
├── MCP_README.md             # MCP README
└── install-all.sh            # Installation script
```

## Performance Optimization Guide

### Agent Scaling

```python
if utilization > 0.85:
    pool.scale_up("design_development", 2, factory)
elif utilization < 0.3:
    pool.scale_down("design_development", 1)
```

### Token Cost Reduction

```python
config = WorkflowConfig(
    token_budget=500000,
    enable_toc=True
)
```

### Throughput Increase

```python
config = WorkflowConfig(
    max_concurrent_works=20,
    optimization_interval=30.0
)
```

## Environment Variables

```bash
# <agents_directory>/.env
DB_PASSWORD=whiteduck
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
```

## Requirements

- Python 3.12
- PostgreSQL 16.11
- MCP 1.0.0+
- PyTorch 2.0+ (optional, for ML projects)

## Contributing

This project is part of the OpenCode ecosystem.

## Latest Updates

- **Plan Approval**: Process where RESPONSIBLE agent submits plan and ACCOUNTABLE agent approves
- **TOC Final Analysis**: Automatic analysis of token efficiency, agent efficiency, and bottlenecks after all Work completions
- **Automatic Improvement Suggestions**: Automatic suggestions for token optimization, agent scaling, and processing speed improvement

## Requirements

- Python 3.12
- PostgreSQL 16.11
- MCP 1.0.0+
- PyTorch 2.0+ (optional, for ML projects)

## Installed Python Packages

- mcp==1.26.0
- pandas==3.0.0
- numpy==2.4.2
- torch==2.10.0+cpu
- scikit-learn==1.8.0
- python-dotenv==1.2.1
