# Agent-Factory Setup Complete

## Environment
- Python: 3.12
- Virtual Environment: <agent_factory_directory>/venv
- PostgreSQL: 15-alpine (Optional - for database features)
- Database Password: whiteduck (default, can be changed in .env)

**Note**: PostgreSQL is optional. You can choose from Docker Compose, Docker, or system installation. Even without installation, MCP server and agent functionality will work normally.

## PostgreSQL (Optional)

PostgreSQL is an **optional** component. MCP server and agent functionality will work normally even if not installed.

### Features Requiring PostgreSQL
- **Database Storage**: Store deployment information, performance metrics, training logs
- **Data Persistence**: Permanent storage of task results, evaluation results

### Features Working Without PostgreSQL
- ✅ MCP server operation
- ✅ Inter-agent communication
- ✅ Workflow execution
- ✅ File system access
- ✅ Memory storage

### PostgreSQL Installation Methods

#### Method 1: Docker Compose (Recommended)

```bash
cd <agent_factory_directory>

# Start PostgreSQL
docker compose up -d

# Stop PostgreSQL
docker compose down
```

**Advantages**:
- Simple and fast installation
- Data volume ensures persistence
- `docker-compose.yml` included

#### Method 2: Docker (Alternative)

```bash
docker run -d \
  --name agent-postgres \
  -e POSTGRES_PASSWORD=whiteduck \
  -e POSTGRES_DB=postgres \
  -p 5432:5432 \
  postgres:15-alpine
```

#### Method 3: System Installation

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql

# macOS
brew install postgresql
brew services start postgresql

# Configuration
sudo -u postgres psql -c "CREATE DATABASE monitoring;"
sudo -u postgres psql -c "CREATE DATABASE training;"
sudo -u postgres psql -c "CREATE DATABASE evaluation;"
```

### Running Without PostgreSQL

The system works normally even if PostgreSQL is not installed:

```bash
# Installation (without DB)
cd <agent_factory_directory>
./setup-mcp.sh

# Message displayed:
# ⚠ PostgreSQL not found (neither systemctl nor docker)
#   Running without database support
# ✓ Dependencies installed
# ✓ OpenCode MCP configuration created
```

### Database Configuration

**PostgreSQL Databases** (optional):
- `data` - Raw and processed data storage
- `training` - Processing checkpoints and logs
- `evaluation` - Evaluation metrics and results
- `monitoring` - Deployment and monitoring data

## Directory Structure
```
<home_directory>/
├── agent_factory/               # Agent source code
│   ├── mcp_server.py           # MCP Server entry point
│   ├── setup-mcp.sh            # MCP server setup
│   ├── opencode-integrate.sh    # OpenCode integration
│   └── docker-compose.yml       # PostgreSQL Docker Compose config
├── data/                       # Data files (CSV, JSON, etc.)
├── models/                      # Generated models/artifacts
├── checkpoints/                  # Processing checkpoints
├── results/                      # Experiment results
├── reports/                      # Evaluation reports
├── deployments/                  # Deployment configurations
└── logs/                         # Application logs
```

## Agents
1. **problem_definition** - Problem analysis and project planning
2. **data_collection** - Data gathering and preprocessing
3. **design_development** - System architecture design and code generation
4. **training_optimization** - Process optimization and tuning
5. **evaluation_validation** - Performance evaluation and validation
6. **deployment_monitoring** - Deployment and runtime monitoring
7. **coordinator** - Workflow orchestration

## Examples

All examples are in the `examples/` directory:

- `work_agent_statistics_example.py` - Work-Agent statistics example (New)
- `basic_usage.py` - Basic usage example
- `plan_approval_example.py` - Plan approval workflow example 1
- `plan_approval_example2.py` - Plan approval workflow example 2
- `toc_analysis_example.py` - TOC final analysis example
- `toc_optimization_example.py` - TOC optimization example
- `raci_example.py` - RACI matrix example
- `documentation_example.py` - Documentation example
- `workflow_templates_example.py` - Workflow template example

### Running Examples

```bash
cd <agent_factory_directory>
source venv/bin/activate

# Run example
python examples/work_agent_statistics_example.py
python examples/basic_usage.py
# ... other examples
```

## Usage

### Option 1: Direct Agent Execution
```bash
cd <agent_factory_directory>
source venv/bin/activate

# Run specific agent
./run.sh coordinator "Build customer management web app"

# Or run individual agents
./run.sh problem_definition
./run.sh data_collection
```

### Option 2: Plan Approval Workflow
```bash
cd <agent_factory_directory>
source venv/bin/activate

# Run plan approval example
python examples/plan_approval_example2.py
```

### Option 3: MCP Server (Recommended for OpenCode)

#### Running Without PostgreSQL (Quick Start)

```bash
cd <agent_factory_directory>
source venv/bin/activate

# Start MCP server (without DB)
python -m agent_factory.mcp_server
```

#### Running With PostgreSQL (Recommended)

```bash
# Method 1: Docker Compose (easiest way)
cd <agent_factory_directory>
docker compose up -d
source venv/bin/activate
python -m agent_factory.mcp_server

# Method 2: Automatic installation script
cd <agent_factory_directory>
./setup-mcp.sh
source venv/bin/activate
python -m agent_factory.mcp_server

# Method 3: OpenCode integration
cd <agent_factory_directory>
./opencode-integrate.sh
# Restart OpenCode to automatically load MCP server
```

### PostgreSQL Configuration (Optional)

If you want to use PostgreSQL, set the password in the `.env` file:

```bash
# Create or modify .env file
echo "DB_PASSWORD=your_password" >> .env

# When using Docker Compose
docker compose up -d
```

**Default Password**: `whiteduck`

## MCP Server Features

The MCP server exposes all agent functionality as tools:

- **execute_workflow** - Run complete development pipeline
- **define_problem** - Define problem scope and project plan
- **collect_data** - Collect from sources
- **preprocess_data** - Clean and validate
- **design_architecture** - Design system architecture
- **generate_implementation** - Generate implementation code
- **optimize_process** - Run process with optimization
- **evaluate_results** - Evaluate performance
- **deploy_system** - Deploy to production
- **monitor_system** - Monitor deployed system
- **submit_work_plan** - Submit work plan for approval
- **approve_work_plan** - Approve work plan
- **reject_work_plan** - Reject work plan
- **get_work_plan_status** - Get work plan status

See `MCP_README.md` for detailed documentation.

## Supported Project Types

This system supports various development workflows:

- **Web Applications** - REST APIs, Frontend, Backend
- **Data Pipelines** - ETL, Analytics, Reporting
- **Machine Learning** - Model training, optimization, deployment
- **Automation Scripts** - CI/CD, Task automation
- **Microservices** - Distributed systems, API integration

## Environment Variables

- `DB_PASSWORD=whiteduck` (set in <agent_factory_directory>/.env, Optional)
  - PostgreSQL password
  - Only needed when using PostgreSQL
  - Set in .env file or pass as environment variable

## MCP Servers Used by Agents
- **filesystem** - File system access (Always available)
- **fetch** - HTTP/Fetch API for web requests (Always available)
- **postgres** - PostgreSQL database access (Optional, requires PostgreSQL)
- **memory** - Persistent memory storage (Always available)
- **sequential-thinking** - Enhanced reasoning (processing) (Optional)
- **git** - Git version control (Optional, requires Git)

### Required vs Optional Servers

| MCP Server | Required | Description |
|------------|----------|-------------|
| filesystem | ✅ Required | File read/write |
| fetch | ✅ Required | Web requests, data download |
| memory | ✅ Required | Memory storage, cache |
| postgres | ⚠ Optional | Database storage, metrics storage |
| sequential-thinking | ⚠ Optional | Enhanced reasoning |
| git | ⚠ Optional | Version control |

## Latest Updates

### Added Features

1. **Work-Agent Statistics**
     - Provides statistics on which agents worked how much for each work
     - Token usage, task time, analysis by agent type
     - API:
         - `toc.get_work_agent_statistics(work_id)` - Specific work statistics
         - `toc.get_work_agent_statistics()` - Overall statistics
         - `toc.format_work_agent_report(work_id)` - Formatted report
     - Example: `examples/work_agent_statistics_example.py`

2. **Plan Approval**
     - Function for RESPONSIBLE agent to submit plan
     - Function for ACCOUNTABLE agent to approve/reject plan
     - Plan contents: approach, steps, estimated time, risks, expected results
     - Examples: `examples/plan_approval_example.py`, `examples/plan_approval_example2.py`

3. **TOC Final Analysis**
     - Automatic analysis after all Work completions
     - Token efficiency analysis (expected vs actual)
     - Agent efficiency analysis
     - Bottleneck analysis
     - Automatic improvement suggestions generation
     - Examples: `examples/toc_analysis_example.py`, `examples/toc_optimization_example.py`

4. **Optional PostgreSQL Support**
     - PostgreSQL is an optional component
     - MCP server and agent functionality work normally even if not installed
     - Features requiring PostgreSQL:
         - Database storage (deployment information, performance metrics)
         - Data persistence
     - Installation methods:
         - Docker Compose (recommended): `docker compose up -d`
         - Docker: `docker run -d -p 5432:5432 postgres:15-alpine`
         - System: `sudo apt install postgresql`

### Additional Examples

- `examples/work_agent_statistics_example.py` - Work-Agent statistics example
- `examples/plan_approval_example2.py` - Plan approval workflow example
- `examples/toc_analysis_example.py` - TOC final analysis example
- `examples/toc_optimization_example.py` - TOC optimization example
