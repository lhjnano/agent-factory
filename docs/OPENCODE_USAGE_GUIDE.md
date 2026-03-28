# OpenCode & AI Agent Usage Guide - Agent Factory

## 🎯 Overview

This guide helps OpenCode and other AI agents effectively use Agent Factory's MCP tools and new features.

---

## 📋 Quick Reference

### MCP Tools Available

| Tool | Description | Use When |
|------|-------------|----------|
| `execute_workflow` | Run complete development pipeline | Starting a new project from scratch |
| `define_problem` | Define problem scope and project plan | Beginning of any project |
| `collect_data` | Collect data from sources | Need data for ML/analytics |
| `preprocess_data` | Clean and validate data | After data collection |
| `design_architecture` | Design system architecture | Before coding starts |
| `generate_implementation` | Generate code implementation | After architecture design |
| `optimize_process` | Run with configuration | Tuning ML models or processes |
| `evaluate_results` | Evaluate performance | After implementation |
| `deploy_system` | Deploy to production | Ready to go live |
| `monitor_system` | Monitor performance | Post-deployment |
| `assign_skills_to_work` | Assign skills to work | When starting new work |
| `get_work_skills` | Get work skill info | Reviewing work assignments |
| `get_skill_effectiveness` | Get skill metrics | Optimizing skill usage |
| `analyze_work_for_skills` | Analyze and recommend skills | Planning new work |

---

## 🚀 Quick Start for OpenCode

### Step 1: Verify Installation

```bash
# Check MCP server is configured
cat ~/.config/opencode/opencode.json | grep agent-factory

# Expected output (using Python directly):
# "agent-factory": {
#   "type": "local",
#   "command": [
#     "<agent_factory_directory>/venv/bin/python",
#     "-m",
#     "agent_factory.mcp_server"
#   ]
# }

# Or using npx (recommended):
# "agent-factory": {
#   "type": "local",
#   "command": [
#     "npx",
#     "-y",
#     "@purpleraven/agent-factory"
#   ]
# }
```

### Step 2: Restart OpenCode

Restart OpenCode to load the MCP server. Available tools will appear in the MCP client.

### Step 3: First Use

Ask OpenCode to execute a workflow:

```
User: Build a simple REST API for user management
```

OpenCode will automatically use the `execute_workflow` tool.

---

## 🤖 AI Agent Usage Patterns

### Pattern 1: Full Project Development

**Use when:** Starting a complete project from scratch

**Tools to use in sequence:**
1. `define_problem` - Define scope and requirements
2. `collect_data` - Gather necessary data (if ML project)
3. `preprocess_data` - Clean and prepare data (if ML project)
4. `design_architecture` - Design system architecture
5. `generate_implementation` - Write code
6. `optimize_process` - Optimize/validate (if ML project)
7. `evaluate_results` - Test and evaluate
8. `deploy_system` - Deploy to production
9. `monitor_system` - Set up monitoring

**Example for OpenCode:**
```python
# OpenCode will handle this automatically when you say:
"Build a customer churn prediction model with web dashboard"
```

---

### Pattern 2: Incremental Development

**Use when:** Adding features to existing project

**Tools to use:**
- `define_problem` - Define new feature requirements
- `design_architecture` - Update architecture
- `generate_implementation` - Add new code
- `evaluate_results` - Test new feature
- `deploy_system` - Deploy update

**Example for OpenCode:**
```python
# OpenCode will handle this automatically when you say:
"Add user authentication to the existing REST API"
```

---

### Pattern 3: Skill-Based Work Assignment

**Use when:** Optimizing work with skill assignments

**Tools to use:**
1. `analyze_work_for_skills` - Analyze work and recommend skills
2. `assign_skills_to_work` - Assign skills to work
3. `get_work_skills` - Check skill assignments
4. `get_skill_effectiveness` - Monitor skill performance

**Example for OpenCode:**
```python
# OpenCode will automatically:
1. Analyze the work type
2. Recommend appropriate skills
3. Assign skills based on RACI roles
4. Track effectiveness
```

---

### Pattern 4: ML/Analytics Project

**Use when:** Building ML models or data analytics

**Tools to use in sequence:**
1. `define_problem` - Define ML problem
2. `collect_data` - Gather training data
3. `preprocess_data` - Clean and prepare data
4. `design_architecture` - Design model architecture
5. `generate_implementation` - Implement model
6. `optimize_process` - Train and tune hyperparameters
7. `evaluate_results` - Validate model performance
8. `deploy_system` - Deploy model to production
9. `monitor_system` - Monitor model performance

**Example for OpenCode:**
```python
# OpenCode will handle this automatically when you say:
"Build an image classification model using transfer learning"
```

---

## 🎛️ Advanced Features for AI Agents

### Queue System Integration

AI agents can leverage the multi-queue system for better work management:

```python
# OpenCode automatically uses priority queues
# High-priority work gets processed first

# Example request:
"Deploy this critical bug fix immediately"
# OpenCode will:
# 1. Set WorkPriority.CRITICAL
# 2. Enqueue in high-priority queue
# 3. Fast-track through scheduler
```

---

### Retry System Integration

AI agents benefit from automatic retry logic:

```python
# OpenCode automatically handles retries
# Failed works are retried with exponential backoff

# Example:
# If network request fails, OpenCode will:
# 1. Retry after 1 second
# 2. Retry after 2 seconds
# 3. Retry after 4 seconds
# 4. Give up after max_retries
```

---

### Auto-scaling Integration

AI agents benefit from dynamic resource allocation:

```python
# OpenCode automatically scales worker pool
# More workers when queue is long, fewer when idle

# Example:
# When you say "Process 100 files":
# OpenCode will:
# 1. Detect heavy workload
# 2. Scale up worker pool
# 3. Process files in parallel
# 4. Scale down when complete
```

---

### Smart Scheduling Integration

AI agents benefit from intelligent work scheduling:

```python
# OpenCode uses token-aware scheduling
# Minimizes token usage and cost

# Example:
# When processing multiple works:
# OpenCode will:
# 1. Group similar works
# 2. Reuse context across works
# 3. Minimize redundant tokens
# 4. Save up to 20% on costs
```

---

## 📊 Best Practices for AI Agents

### 1. Always Define Problem First

```python
# ❌ Bad: Jump straight to implementation
"Write a Python script for data analysis"

# ✅ Good: Start with problem definition
"Define the problem: I need to analyze customer sales data to identify trends"
# Then let OpenCode determine the best approach
```

---

### 2. Leverage Skill System

```python
# ❌ Bad: Manually manage skills
"I'll use the design-development-skill for this"

# ✅ Good: Let OpenCode analyze and assign
"Analyze this work and assign appropriate skills"
# OpenCode will:
# 1. Use analyze_work_for_skills
# 2. Recommend best skills
# 3. Assign based on RACI roles
```

---

### 3. Use Workflow for Complex Tasks

```python
# ❌ Bad: Break down manually
"First design, then code, then test, then deploy"

# ✅ Good: Use execute_workflow
"Execute complete workflow for building a web app"
# OpenCode will handle all steps automatically
```

---

### 4. Monitor Skill Effectiveness

```python
# Periodically check skill effectiveness
"Get skill effectiveness metrics"

# OpenCode will show:
# - Which skills are performing well
# - Which skills need optimization
# - Usage statistics
```

---

### 5. Use Priority for Critical Work

```python
# For urgent work, explicitly mention priority
"Deploy this hotfix with CRITICAL priority"

# OpenCode will:
# 1. Set WorkPriority.CRITICAL
# 2. Fast-track through all systems
```

---

## 🔧 Troubleshooting for AI Agents

### Issue: Tools Not Available

**Symptom:** OpenCode doesn't show MCP tools

**Solution:**
```bash
# 1. Check MCP server is running
ps aux | grep "agent_factory.mcp_server"

# 2. Check configuration
cat ~/.config/opencode/opencode.json

# 3. Restart OpenCode
# OpenCode needs to reload MCP configuration
```

---

### Issue: Work Not Completing

**Symptom:** Work stuck in queue

**Solution:**
```python
# Check skill assignments
"Get work skills for work_123"

# Check skill effectiveness
"Get skill effectiveness"

# If needed, reassign skills
"Reassign skills to work_123"
```

---

### Issue: High Token Usage

**Symptom:** Token costs are high

**Solution:**
```python
# Check skill effectiveness
"Get skill effectiveness"

# Identify low-efficiency skills
# Optimize or refine them

# Next works will automatically use optimized skills
```

---

## 🎓 Examples for AI Agents

### Example 1: Building a REST API

```python
# User request:
"Build a REST API for user management with FastAPI"

# OpenCode automatically:
# 1. Calls define_problem
# 2. Analyzes work type: design_development
# 3. Assigns skills: design-development-skill
# 4. Calls design_architecture
# 5. Calls generate_implementation
# 6. Calls evaluate_results
# 7. Calls deploy_system

# Result: Complete REST API deployed and running
```

---

### Example 2: Training ML Model

```python
# User request:
"Train a customer churn prediction model"

# OpenCode automatically:
# 1. Calls define_problem
# 2. Analyzes work type: training_optimization
# 3. Assigns skills: training-optimization-skill
# 4. Calls collect_data (for training data)
# 5. Calls preprocess_data
# 6. Calls design_architecture (model architecture)
# 7. Calls generate_implementation (model code)
# 8. Calls optimize_process (train model)
# 9. Calls evaluate_results (validate model)
# 10. Calls deploy_system (deploy model)

# Result: Trained model deployed and monitored
```

---

### Example 3: Monitoring Skills

```python
# User request:
"How are my skills performing?"

# OpenCode automatically:
# 1. Calls get_skill_effectiveness

# Returns:
{
  "design-development-skill": {
    "usage_count": 25,
    "success_rate": 0.98,
    "avg_tokens": 1800,
    "efficiency_score": 0.92
  },
  "training-optimization-skill": {
    "usage_count": 15,
    "success_rate": 0.93,
    "avg_tokens": 2500,
    "efficiency_score": 0.85
  }
}

# Result: Clear view of skill performance
```

---

## 📚 Additional Resources

- **New Features**: `docs/NEW_FEATURES.md`
- **API Reference**: `docs/API_REFERENCE.md`
- **Examples**: `examples/`
- **Tests**: `tests/`

---

## 🤝 Tips for AI Agent Developers

### When Implementing New MCP Tools

1. **Follow Existing Patterns**
   - All tools use `@app.call_tool()` decorator
   - Return structured results
   - Handle errors gracefully

2. **Integrate with New Systems**
   - Use `MultiQueueManager` for work queuing
   - Use `RetryManager` for error handling
   - Use `AutoScaler` for resource management

3. **Provide Clear Descriptions**
   - Tool descriptions should be clear
   - Input parameters should be well-documented
   - Include examples in docstrings

4. **Test Thoroughly**
   - Write unit tests
   - Test with OpenCode integration
   - Verify error handling

---

**Version**: 2.1.0
**Last Updated**: 2026-03-28
