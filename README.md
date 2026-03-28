# Agent Factory

Work-based Multi-Agent System Architecture

## Overview

This system provides the following core functionalities:

- **Work-based Task Classification**: Define all tasks in Work units
- **Multi-Agent Deployment**: Deploy multiple agent instances for parallel processing
- **RACI Matrix**: Clarify responsibility and structure collaboration
- **Skill System**: Dynamically assign skills to each Work and monitor effectiveness
- **Automatic Documentation**: Automatically generate standardized documentation after task completion
- **TOC (Theory of Constraints) Based Optimization**: Identify bottlenecks and optimize throughput

## Skill System

### Overview

Agent Factory v2 introduces a **Dynamic Skill System** that assigns appropriate skills to each Work in real-time, and allows the Consulted role to distribute skills to RACI members.

### Skill Structure

```
.agent/skills/
├── problem-definition-skill/
│   └── SKILL.md
├── data-collection-skill/
│   └── SKILL.md
├── design-development-skill/
│   └── SKILL.md
├── training-optimization-skill/
│   └── SKILL.md
├── evaluation-validation-skill/
│   └── SKILL.md
├── deployment-monitoring-skill/
│   └── SKILL.md
└── toc-supervisor-skill/
    └── SKILL.md
```

### Available Skills

| Skill Name | Description | Use Case |
|-----------|-------------|----------|
| `problem-definition-skill` | Problem definition and requirements gathering | Project start, scope definition |
| `data-collection-skill` | Data collection and preprocessing | ML/AI data pipeline |
| `design-development-skill` | System design and code generation | Architecture design, development |
| `training-optimization-skill` | Model training and optimization | ML model training, hyperparameter tuning |
| `evaluation-validation-skill` | Model evaluation and validation | Testing, performance measurement |
| `deployment-monitoring-skill` | Deployment and monitoring | Production deployment, operations |
| `toc-supervisor-skill` | Workflow orchestration and optimization | Bottleneck analysis, throughput optimization |

### Dynamic Skill Assignment

#### Automatic Skill Assignment

When a Work is created, skills are automatically recommended:

```python
work = orchestrator.create_work(
    name="Build REST API",
    description="Create a FastAPI backend for user management",
    work_type="design_development",
    agent_type="design_development",
    inputs={"tech_stack": "FastAPI, PostgreSQL"},
    tags=["web", "api", "backend"],
    auto_assign_skills=True  # Enable automatic skill assignment
)

# Check skills assigned to Work
print(work.required_skills)
# ['design-development-skill', 'toc-supervisor-skill']

# Check skill assignments by RACI role
print(work.skill_assignments)
# {
#   "responsible": {"agent_id": "dev_1", "skills": ["design-development-skill"], ...},
#   "accountable": {"agent_id": "senior_1", "skills": ["design-development-skill", "toc-supervisor-skill"], ...},
#   ...
# }
```

#### Skill Assignment by Consulted

The Consulted role agent can review and distribute skills:

```python
# Consultant agent reviews skill assignment
assignment_result = await orchestrator.consult_and_assign_skills(
    work=work,
    consultant_agent_id="toc_supervisor_1"
)

# Check results
print(assignment_result["recommended_skills"])
# ['design-development-skill', 'deployment-monitoring-skill']

print(assignment_result["skill_assignments"])
# Skills assigned to each RACI role
```

### Skill Effectiveness Monitoring

TOC Supervisor monitors the effectiveness of each skill:

```python
# After workflow completion, automatically analyze skill effectiveness
result = await orchestrator.execute_workflow(works=works)

# Check skill effectiveness report
print(result.skill_effectiveness_analysis)
# {
#   "total_skills_loaded": 7,
#   "skills_with_metrics": 5,
#   "skill_recommendations": [
#     {"skill": "data-collection-skill", "action": "optimize", ...},
#     {"skill": "training-optimization-skill", "action": "maintain", ...}
#   ],
#   "top_performing_skill": {
#     "name": "design-development-skill",
#     "efficiency_score": 0.92,
#     "success_rate": 0.98,
#     "usage_count": 25
#   },
#   "detailed_effectiveness": {...}
# }
```

### Skill Effectiveness Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Usage Count | Number of times skill was used | Consistent usage |
| Success Rate | Success rate when skill is used | > 95% |
| Avg Tokens | Average tokens per skill usage | Lower is better |
| Avg Duration | Average time per skill usage | Lower is better |
| Efficiency Score | Overall efficiency score (0-1) | > 0.8 |

### Skill Recommendation Algorithm

SkillAnalyzer recommends skills by considering the following factors:

1. **Work Type**: Assign skills matching work_type by default
2. **Description Analysis**: Keyword matching in task description
3. **Tags**: Analyze skill relevance through tags
4. **Inputs**: Analyze input parameters

#### Skill Assignment by RACI Role

| Role | Skill Category | Description |
|------|---------------|-------------|
| Responsible | CORE, SPECIALIZED | Main task execution skills |
| Accountable | CORE, QUALITY | Approval and quality assurance skills |
| Consulted | SUPPORT, SPECIALIZED, QUALITY | Consulting and review skills |
| Informed | SUPPORT | Support skills for receiving information |

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    MultiAgentOrchestrator                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  WorkQueue  │  │  AgentPool  │  │   DocumentationManager  │ │
│  └──────┬──────┘  └──────┬──────┘  └─────────────┬───────────┘ │
│         │                │                       │              │
│         └────────────────┼───────────────────────┘              │
│                          │                                       │
│  ┌───────────────────────┴───────────────────────────────────┐ │
│  │                    TOCSupervisor                            │ │
│  │  - Bottleneck analysis  - Throughput calculation  - Optimization execution  - Constraint identification   │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                          │                                       │
│  ┌───────────────────────┴───────────────────────────────────┐ │
│  │                       RACI Matrix                           │ │
│  │  R(Responsible) - A(Accountable) - C(Consulted) - I(Informed)│
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
 ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
 │   Agent 1    │   │   Agent 2    │   │   Agent N    │
 │  (Instance)  │   │  (Instance)  │   │  (Instance)  │
 └──────────────┘   └──────────────┘   └──────────────┘
 ```

## Core Components

### 1. Work (Task Unit)

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
    inputs={"key": "value"},
    estimated_tokens=1000,
    require_plan_approval=True  # Require plan approval
)
```

### 2. AgentPool (Agent Pool)

```python
from agent_factory.core import AgentPool, AgentInstance, AgentStatus

pool = AgentPool()

agent = AgentInstance(
    agent_id="agent_1",
    agent_type="design_development",
    capabilities=["design", "code_generation"],
    max_concurrent_works=3
)

pool.register_agent(agent)
```

### 3. RACI Matrix

```python
from agent_factory.core import RACI, RACIRole

raci = RACI()
raci.assign("work_1", "agent_a", RACIRole.RESPONSIBLE)
raci.assign("work_1", "agent_b", RACIRole.ACCOUNTABLE)
raci.assign("work_1", "agent_c", RACIRole.CONSULTED)
raci.assign("work_1", "agent_d", RACIRole.INFORMED)
```

### 4. TOC Supervisor (General Agent)

```python
from agent_factory.core import TOCSupervisor

supervisor = TOCSupervisor(
    agent_pool=pool,
    work_queue=queue,
    raci=raci
)

analysis = await supervisor.analyze_system()
optimization = await supervisor.optimize()
report = supervisor.get_optimization_report()
```

### 5. Plan Approval

```python
# Create Work and assign RACI
work = orchestrator.create_work(
    name="Build API",
    description="Implement REST API",
    work_type="design_development",
    agent_type="design_development",
    inputs={"endpoint": "/api/users"},
    priority=WorkPriority.HIGH
)

orchestrator.assign_raci(
    work_id=work.work_id,
    responsible=["dev_agent"],      # Plan submission and task execution
    accountable="senior_agent",      # Plan approval
    consulted=[],
    informed=[]
)

# Set plan approval requirement
orchestrator.set_work_plan_approval_required(work.work_id, True)

# RESPONSIBLE agent submits plan
plan = {
    "approach": "Use FastAPI",
    "steps": [
        "1. Initialize FastAPI app",
        "2. Define Pydantic models",
        "3. Implement /api/users endpoint"
    ],
    "estimated_files": ["main.py", "models.py"],
    "estimated_hours": 4,
    "risks": ["Possible DB connection delay"],
    "expected_results": "Return JSON response"
}

submit_result = orchestrator.submit_work_plan(
    work_id=work.work_id,
    plan_content=plan,
    proposed_by="dev_agent"
)

# ACCOUNTABLE agent reviews and approves plan
approve_result = orchestrator.approve_work_plan(
    work_id=work.work_id,
    approved_by="senior_agent"
)

# Now task can be executed
```

### 6. Documentation System

```python
from agent_factory.core import DocumentationManager, DocumentType

doc_manager = DocumentationManager()

doc = doc_manager.create_document(
    document_type=DocumentType.ARCHITECTURE_DESIGN,
    work_id="work_1",
    agent_id="agent_1",
    sections={
        "overview": "System overview",
        "components": "Components",
        "data_flow": "Data flow"
    }
)
```

## Work Type and Agent Mapping

| Work Type | Agent Type | Description |
|-----------|---------------|------|
| `problem_definition` | ProblemDefinitionAgent | Problem definition |
| `data_collection` | DataCollectionAgent | Data collection/preprocessing |
| `design_development` | DesignDevelopmentAgent | Design/development |
| `training_optimization` | TrainingOptimizationAgent | Training/optimization |
| `evaluation_validation` | EvaluationValidationAgent | Evaluation/validation |
| `deployment_monitoring` | DeploymentMonitoringAgent | Deployment/monitoring |

## Workflow Templates

### ML Pipeline

```python
orchestrator = MultiAgentOrchestrator()

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

## TOC (Theory of Constraints) Based Optimization

### Bottleneck Detection

The system automatically detects the following bottlenecks:

- **Agent Capacity**: Insufficient agent capacity
- **Work Dependency**: Waiting due to task dependencies
- **Token Limit**: Token usage limit
- **Queue Overflow**: Queue overflow
- **Imbalanced Load**: Load imbalance

### Final Analysis and Improvement Suggestions

After all Works are completed, TOC Supervisor automatically performs the following analysis:

1. **Token Efficiency Analysis**
   - Compare expected vs actual token usage
   - Analyze efficiency by task type
   - Calculate savable tokens
   - Identify inefficient task types

2. **Agent Efficiency Analysis**
   - Analyze performance by agent
   - Aggregate by agent type
   - Success rate, average token usage, average processing time

3. **Bottleneck Analysis**
   - Identify agent overload/underutilization
   - Recommend agent count adjustment

4. **Generate Improvement Suggestions**
   - Token optimization methods
   - Agent scaling recommendations
   - Processing speed improvement methods
   - Process improvement suggestions

### Final Analysis Usage Example

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
```

### Final Analysis API

```python
# Record on Work completion
toc_supervisor.record_work_completion(work, result)

# Generate final analysis
analysis = await toc_supervisor.generate_final_analysis(completed_works)

# Generate formatted report
report = toc_supervisor.format_final_report(analysis)
```

### Automatic Optimization

```python
# Enable automatic optimization
config = WorkflowConfig(
    enable_toc=True,
    optimization_interval=60.0,  # Optimize every 60 seconds
    auto_scale=True
)

orchestrator = MultiAgentOrchestrator(config)
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

## RACI Role Definitions

| Role | Description | Responsibility |
|------|------|------|
| **R**esponsible | Execution in charge | Task execution, plan submission |
| **A**ccountable | Final responsibility | Approval/rejection, plan review |
| **C**onsulted | Consulting | Provide opinions |
| **I**nformed | Information reception | Notify results |

## Plan Approval Workflow

A process where the RESPONSIBLE agent reports the plan and expected results before executing development tasks, and receives approval from the ACCOUNTABLE agent.

### Plan Approval Stages

1. **Work Creation and RACI Assignment**
   - Specify RESPONSIBLE, ACCOUNTABLE agents when creating Work
   - Set `require_plan_approval = True` to require plan approval

2. **Plan Submission (RESPONSIBLE)**
   - RESPONSIBLE agent submits plan
   - Plan contents: approach, steps, estimated files, estimated time, risks, expected results

3. **Plan Review and Approval (ACCOUNTABLE)**
   - ACCOUNTABLE agent reviews plan
   - Approve or reject decision
   - If rejected, request rewrite and provide reason

4. **Task Execution**
   - Execute tasks according to approved plan
   - If issues arise during execution, report differences from plan

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
    reason="The plan is too insufficient. More detailed steps needed."
)

# Check plan status
plan_status = orchestrator.get_work_plan_status(work_id)
```

### Additional WorkStatus

- `PLAN_SUBMITTED`: Plan has been submitted (waiting for ACCOUNTABLE approval)
- `PLAN_APPROVED`: Plan has been approved (task can be executed)

### PlanStatus Enumeration

- `NOT_REQUIRED`: Plan approval not required
- `PENDING`: Waiting for approval
- `APPROVED`: Approved
- `REJECTED`: Rejected

## Documentation Standards

### Document Types

- `PROBLEM_DEFINITION`: Problem definition document
- `PROJECT_PLAN`: Project plan document
- `DATA_SPECIFICATION`: Data specification document
- `ARCHITECTURE_DESIGN`: Architecture design document
- `MODEL_EVALUATION`: Model evaluation report
- `DEPLOYMENT_GUIDE`: Deployment guide
- `WORK_SUMMARY`: Task summary

## Directory Structure

```
agents/
├── core/
│   ├── __init__.py
│   ├── work.py           # Work, WorkQueue definition
│   ├── raci.py           # RACI matrix
│   ├── documentation.py  # Documentation system
│   ├── agent_pool.py     # Agent pool management
│   ├── toc_supervisor.py # TOC general agent
│   └── orchestrator.py   # Main orchestrator
├── coordinator/
│   ├── agent.py
│   └── AGENT.md
├── problem_definition/
│   ├── agent.py
│   └── AGENT.md
├── data_collection/
│   ├── agent.py
│   └── AGENT.md
├── design_development/
│   ├── agent.py
│   └── AGENT.md
├── training_optimization/
│   ├── agent.py
│   └── AGENT.md
├── evaluation_validation/
│   ├── agent.py
│   └── AGENT.md
├── deployment_monitoring/
│   ├── agent.py
│   └── AGENT.md
└── MCP_README.md
```

### Plan Approval Functionality

- **RESPONSIBLE Agent**: Submit plan before task execution
   - Approach
   - Execution steps
   - Estimated files
   - Estimated time
   - Risk identification
   - Expected results

- **ACCOUNTABLE Agent**: Review plan and approve/reject
   - Review plan clarity
   - Verify feasibility
   - Approve: Allow task progress
   - Reject: Request revision and provide reason

### TOC Final Analysis Functionality

Automatically perform the following analysis after all Work completions:

1. **Token Efficiency Analysis**
   - Compare expected vs actual tokens
   - Analyze efficiency by task type
   - Calculate savable tokens
   - Identify inefficient task types

2. **Agent Efficiency Analysis**
   - Analyze performance by agent
   - Success rate, average token usage, average processing time
   - Identify overload/underutilization

3. **Bottleneck Analysis**
   - Recommend agent count adjustment
   - Overload: More agents needed
   - Underutilization: Reduce agents

4. **Automatically Generate Improvement Suggestions**
   - Token optimization methods (prompt simplification, context reuse)
   - Agent scaling recommendations
   - Processing speed improvement methods
   - Performance improvement suggestions

### Key Additional APIs

```python
# Plan approval
orchestrator.set_work_plan_approval_required(work_id, True)
orchestrator.submit_work_plan(work_id, plan_content, responsible_agent)
orchestrator.approve_work_plan(work_id, accountable_agent)
orchestrator.reject_work_plan(work_id, accountable_agent, reason)
plan_status = orchestrator.get_work_plan_status(work_id)

# TOC final analysis
analysis = await toc_supervisor.generate_final_analysis(completed_works)
report = toc_supervisor.format_final_report(analysis)

# Data storage
await toc_supervisor.save_final_analysis(analysis)
comparison = await toc_supervisor.compare_with_baselines()

# MCP session setup
orchestrator.set_mcp_sessions(
    memory_session=memory_client,
    filesystem_session=filesystem_client
)
```

## Additional Skill System Features

### Skill Search and Loading

```python
# Load specific skill
skill_content = await orchestrator.skill_manager.get_skill_content("design-development-skill")

# Load multiple skills
skills = await orchestrator.skill_manager.load_all_skills([
    "design-development-skill",
    "deployment-monitoring-skill"
])
```

### Get Work Skill Information

```python
# Get skill information assigned to Work
skill_info = await orchestrator.get_work_skills(work.work_id)

print(skill_info["required_skills"])
print(skill_info["skill_assignments"])
print(skill_info["skill_content"])
```

### Get Skill Effectiveness

```python
# All skill effectiveness
all_effectiveness = orchestrator.skill_manager.get_all_skill_effectiveness()

# Specific skill effectiveness
skill_metrics = orchestrator.skill_manager.get_skill_effectiveness("design-development-skill")

# Result
# {
#   "usage_count": 25,
#   "success_rate": 0.98,
#   "avg_tokens": 1800,
#   "avg_duration": 450.0,
#   "efficiency_score": 0.92
# }
```

### Skill Assignment via MCP Tools

The agent-factory MCP server provides the following tools:

| Tool Name | Description | Input |
|---------|------|------|
| `agent-factory_define_problem` | Define problem | requirements |
| `agent-factory_collect_data` | Collect data | sources |
| `agent-factory_preprocess_data` | Preprocess data | data_path |
| `agent-factory_design_architecture` | Design architecture | problem_def |
| `agent-factory_generate_implementation` | Generate implementation code | architecture |
| `agent-factory_optimize_process` | Optimize process | config |
| `agent-factory_evaluate_results` | Evaluate results | output_path, test_data_path |
| `agent-factory_deploy_system` | Deploy system | artifact_path, config |
| `agent-factory_monitor_system` | Monitor system | version |
| `analyze_work_for_skills` | Analyze work and recommend skills | work_name, work_description, work_type, tags |
| `assign_skills_to_work` | Assign skills to work | work_id, consultant_agent_id |
| `get_work_skills` | Get work skill information | work_id |
| `get_skill_effectiveness` | Get skill effectiveness metrics | skill_name (optional) |

These tools are restricted through allowed-tools settings of each skill.

### Introduction of Skill System

**Dynamic Skill Assignment**:
- Automatically recommend and assign appropriate skills to each Work
- Analyze Work content (description, tags, inputs) to recommend skills
- Consulted role can review and adjust skill assignments

**RACI-Based Skill Distribution**:
- Automatically assign skill categories matching each RACI role
   - **Responsible**: CORE, SPECIALIZED skills (main task execution)
   - **Accountable**: CORE, QUALITY skills (approval and quality assurance)
   - **Consulted**: SUPPORT, SPECIALIZED, QUALITY skills (consulting and review)
   - **Informed**: SUPPORT skills (information reception)

**Skill Effectiveness Monitoring**:
- TOC Supervisor monitors skill effectiveness in real-time
- Metrics: usage count, success rate, average tokens, average time, efficiency score
- Automatically generate skill improvement/optimization/maintenance recommendations

**SkillAnalyzer**:
- Analyze Work to recommend appropriate skills
- Keyword matching, work type mapping, tag analysis, inputs analysis
- Sort by confidence score

**SkillManager**:
- Load and manage SKILL.md files
- Record and track skill effectiveness
- Inject skill content into agents

### TOC Final Analysis Functionality - Skill Extension

Automatically perform the following analysis after all Work completions:

1. **Token Efficiency Analysis**
   - Compare expected vs actual tokens
   - Analyze efficiency by task type
   - Calculate savable tokens
   - Identify inefficient task types

2. **Agent Efficiency Analysis**
   - Analyze performance by agent
   - Success rate, average token usage, average processing time
   - Identify overload/underutilization

3. **Skill Effectiveness Analysis** (New)
   - Overall skill usage status
   - Success rate and efficiency score by skill
   - Identify best/worst performing skills
   - Analyze skill usage patterns by work type
   - Generate skill improvement/optimization recommendations

4. **Bottleneck Analysis**
   - Recommend agent count adjustment
   - Overload: More agents needed
   - Underutilization: Reduce agents

5. **Automatically Generate Improvement Suggestions**
   - Token optimization methods (prompt simplification, context reuse)
   - Agent scaling recommendations
   - Processing speed improvement methods
   - **Skill optimization methods** (improve inefficient skills, remove underutilized skills)
