#!/bin/bash

set -e

echo "================================"
echo "OpenCode Integration Script"
echo "================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$HOME/.config"
OPENCODE_DIR="$CONFIG_DIR/opencode"
OPENCODE_CONFIG="$OPENCODE_DIR/opencode.json"
AGENT_DIR="$SCRIPT_DIR"

if [ ! -f "$OPENCODE_CONFIG" ]; then
    echo "Creating OpenCode config file..."
    echo '{"$schema":"https://opencode.ai/config.json","mcp":{}}' > "$OPENCODE_CONFIG"
fi

if [ -f "$OPENCODE_CONFIG" ]; then
    echo "Backing up existing MCP config..."
    cp "$OPENCODE_CONFIG" "${OPENCODE_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
fi

# agent-factory를 mcp 섹션에 추가
python3 - "$OPENCODE_CONFIG" "$AGENT_DIR" <<'PYTHON_SCRIPT'
import json
import sys

config_path = sys.argv[1]
agent_dir = sys.argv[2]

# 기존 설정 읽기
with open(config_path, 'r') as f:
    config = json.load(f)

# agent-factory MCP 서버 추가 (npx 버전 사용)
config['mcp']['agent-factory'] = {
    "type": "local",
    "command": [
        "npx",
        "-y",
        "@purpleraven/agent-factory"
    ],
}

# 저장
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print(f"Updated MCP configuration: $config_path")
PYTHON_SCRIPT

echo "OpenCode MCP configuration updated: $OPENCODE_CONFIG"
echo ""
echo "Configuration:"
echo "  File: ~/.config/opencode/opencode.json"
echo "  Server: agent-factory (added to mcp section)"
echo "  Command: npx -y @purpleraven/agent-factory"
echo ""
echo "Note: Using npx wrapper - no need to specify Python paths!"
echo ""
echo "Next steps:"
echo "  1. Restart OpenCode to load MCP server"
echo "  2. Available tools will be listed in MCP client"
