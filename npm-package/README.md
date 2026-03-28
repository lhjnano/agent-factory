# @purpleraven/agent-factory

MCP server for Agent Factory - A work-based multi-agent system with TOC optimization, RACI matrix, and automatic documentation.

## About

This npm package is a wrapper that launches the Python-based Agent Factory MCP server. It provides an easy way to use Agent Factory with OpenCode without worrying about Python paths or virtual environments.

## Installation

### Using npx (Recommended)

No installation required! Just run:

```bash
npx -y @purpleraven/agent-factory
```

### Using npm

```bash
npm install -g @purpleraven/agent-factory
```

Then run:

```bash
agent-factory-mcp
```

## Configuration

### OpenCode Integration

Add to your `~/.config/opencode/opencode.json`:

```json
{
  "mcp": {
    "agent-factory": {
      "type": "local",
      "command": [
        "npx",
        "-y",
        "@purpleraven/agent-factory"
      ]
    }
  }
}
```

### Environment Variables

- `AGENT_FACTORY_PATH` - Path to agent-factory installation directory (optional, auto-detected)
- `AGENT_FACTORY_VENV` - Path to Python virtual environment (optional, auto-detected)

### Auto-Detection

The wrapper automatically detects Agent Factory installation in the following locations:

1. `$AGENT_FACTORY_PATH` environment variable (if set)
2. `~/source/agent-factory`
3. `~/agent-factory`
4. `~/projects/agent-factory`
5. Current directory or parent directory
6. Same directory as this npm package

### Virtual Environment

The wrapper automatically detects Python virtual environment in:

1. `$AGENT_FACTORY_VENV/bin/python` (if set)
2. `<agent-factory>/venv/bin/python`
3. `<agent-factory>/.venv/bin/python`
4. System `python3` (fallback)

## Features

Agent Factory provides 15 MCP tools for AI-assisted development:

### Workflow Tools
- `execute_workflow` - Run complete development pipeline from problem definition to deployment
- `define_problem` - Define problem scope and create project plan
- `collect_data` - Collect data from various sources
- `preprocess_data` - Clean and validate collected data
- `design_architecture` - Design system architecture
- `generate_implementation` - Generate code implementation
- `optimize_process` - Run process with configuration and optimization
- `evaluate_results` - Evaluate performance and generate report
- `deploy_system` - Deploy system to production
- `monitor_system` - Monitor deployed system performance

### Skill Management Tools
- `assign_skills_to_work` - Assign skills to a work
- `get_work_skills` - Get work skill information
- `get_skill_effectiveness` - Get skill effectiveness metrics
- `analyze_work_for_skills` - Analyze work and recommend skills

## Requirements

- Node.js 14.0.0 or higher
- Python 3.12 or higher
- Agent Factory Python package (installation or cloned repository)

## Documentation

For complete documentation, visit: https://github.com/lhjnano/agent-factory

### Key Documentation Files

- **README.md** - Complete overview and features
- **docs/NEW_FEATURES.md** - Latest features in v2.1
- **docs/API_REFERENCE.md** - Complete API documentation
- **docs/OPENCODE_USAGE_GUIDE.md** - OpenCode integration guide
- **docs/SETUP.md** - Setup and installation instructions

## Development

### Package Structure

```
npm-package/
├── package.json       # NPM package configuration
├── index.js          # Wrapper script
└── README.md         # This file
```

### Building

This package doesn't require a build step. The `index.js` wrapper is a standalone Node.js script.

### Publishing

To publish a new version:

```bash
# Update version in package.json
npm version patch  # or minor, major

# Publish to npm
npm publish --access public
```

## License

MIT

## Support

- GitHub Issues: https://github.com/lhjnano/agent-factory/issues
- Documentation: https://github.com/lhjnano/agent-factory

## Contributing

Contributions are welcome! Please read the contributing guidelines at: https://github.com/lhjnano/agent-factory

---

**Version:** 2.1.0
**Last Updated:** 2026-03-28
