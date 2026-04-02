---
name: workflow
description: Decompose complex tasks into Work units and execute them with parallel/sequential agents (agent-factory pattern)
---

Execute the given task using the **agent-factory pattern**.

## Core Principles

- **1 run = max 4~5 Works** — split into Phases automatically if more are needed
- **Independent Works run in parallel** — call multiple Agents simultaneously in a single response
- **Plan and first execution in the same response** — never output a plan and wait

---

## Execution Protocol

### Step 1: Work Decomposition + Phase Plan

Decompose the task into Works, grouped by Phase:

```
[Phase 1 — this run]
W1: <name> — <output> (independent)
W2: <name> — <output> (independent)
W3: <name> — <output> (after W1, W2)

[Phase 2 — next run]
W4: <name> — <output> (after W3)
W5: <name> — <output> (after W4)
```

If total Works ≤ 5, execute in a single run without phases.

### Step 2: Execute Phase 1

Start executing Phase 1 Works **in the same response** immediately after the plan.

**Independent Works (parallel)**: Call multiple Agents simultaneously in a single response.

**Dependent Works (sequential)**: Compress the previous result into 3~7 lines and pass only that to the next Agent.

### Step 3: Phase 1 Completion

When Phase 1 finishes:
1. Save each Work result to `/tmp/wf_<task>/W<n>.md`
2. Print a short summary (1~2 lines per Work)
3. If Phase 2 exists, show the resume command:

```
Phase 1 complete.
Saved to: /tmp/wf_<task>/

Continue with:
/workflow --resume /tmp/wf_<task>/
```

### Step 4: --resume (Phase 2+)

When `--resume <path>` is provided:
1. Read previous result files from the given path to restore context
2. Execute the next Phase immediately
3. Save results and show the next resume command if more phases remain

---

## Agent Prompt Guidelines

Structure each subagent prompt as follows:
1. **Role in one sentence**: "You are a [role]. Produce [specific output]."
2. **Step budget**: "Complete using ≤20 tool calls. Prefer Grep/Glob; use Read only for needed sections."
3. **Save output**: "Write results to `/tmp/wf_<task>/W<n>.md` and report only the path."
4. **Context**: Include only 3~7 lines of key results from the previous step.
5. **Scope limit**: Explicitly forbid work outside this Work's scope.
6. **Research vs Write**: Clearly state whether code writing is required.

### File creation is mandatory for implementation Works

If the Work involves creating or modifying code/config files, the Agent **must** use Write/Edit tools to produce actual files on disk. Design data returned by MCP tools (e.g., `execute_workflow`, `design_architecture`) is input context only — the Agent is still responsible for writing the actual files.

Include this in every implementation Work's prompt:
```
This Work requires writing actual files. Use Write/Edit tools to create each file.
Do NOT stop after producing a design or plan — produce the files.
```

---

## Token Reduction Rules

When passing context between Agents:
- Never copy the previous Agent's full output
- Extract only key results: file names, function names, decisions, numbers
- Save intermediate results to `/tmp/wf_<task>/` and pass only the path

### Parallel external API calls

Independent external API calls (REST, WebFetch, etc.) must always be made in parallel within a single message:

```
# Bad (sequential)
WebFetch(project_a) → wait → WebFetch(project_b)

# Good (parallel)
WebFetch(project_a) + WebFetch(project_b)  ← single message
```

If MCP tools are unavailable, fall back to direct REST API calls:
- Extract connection info (host, api_key) from `~/.claude.json` mcpServers env vars
- Skip pre-lookup steps using params like `assigned_to_id=me`

---

## Start

Receive `$ARGUMENTS` and begin Work decomposition and Phase 1 execution **in the same response**.

If `--resume <path>` is provided, read previous results from that path and continue with the next Phase.
