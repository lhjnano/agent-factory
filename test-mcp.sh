#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="$SCRIPT_DIR"
VENV_DIR="$AGENT_DIR/venv"

echo "================================"
echo "MCP Server Test Script"
echo "================================"
echo ""

if [ ! -d "$VENV_DIR" ]; then
    echo "❌ Virtual environment not found. Run ./setup-mcp.sh first."
    exit 1
fi

# PYTHONPATH 설정
export PYTHONPATH="$AGENT_DIR/src:$PYTHONPATH"

echo "Checking Python and MCP installation..."

"$VENV_DIR/bin/python" -c "import mcp; print('MCP installed successfully')" 2>/dev/null || {
    echo "❌ MCP not installed. Run ./setup-mcp.sh first."
    exit 1
}

echo ""
echo "Testing MCP server module..."
"$VENV_DIR/bin/python" -c "
import sys
try:
    from agent_factory.mcp_server import list_tools, app
    print('MCP server module loaded successfully')
except Exception as e:
    print('Failed to load MCP server:', e)
    sys.exit(1)
" || exit 1

echo ""
echo "Checking agent modules..."
for agent in problem_definition data_collection design_development training_optimization evaluation_validation deployment_monitoring; do
    if [ -f "$AGENT_DIR/src/agent_factory/$agent/agent.py" ]; then
        "$VENV_DIR/bin/python" -c "
import sys
try:
    module = __import__('agent_factory.$agent.agent', fromlist=[''])
    print('$agent')
except Exception as e:
    print('Failed: $agent:', e)
        " || true
    fi
done

echo ""
echo "================================"
echo "Test Complete!"
echo "================================"
