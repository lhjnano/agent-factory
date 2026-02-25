#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="$SCRIPT_DIR"
VENV_DIR="$AGENT_DIR/venv"

create_venv() {
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip
}

install_agent_deps() {
    local agent=$1
    local req_file="$AGENT_DIR/$agent/requirements.txt"
    
    if [ -f "$req_file" ]; then
        echo "Installing dependencies for $agent..."
        pip install -r "$req_file"
    fi
}

create_venv

for agent in problem_definition data_collection design_development training_optimization evaluation_validation deployment_monitoring coordinator; do
    install_agent_deps "$agent"
done

echo "Installation complete!"
echo "Activate virtual environment: source $VENV_DIR/bin/activate"
