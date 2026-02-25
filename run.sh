#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="$SCRIPT_DIR"
VENV_DIR="$AGENT_DIR/venv"

source "$VENV_DIR/bin/activate"

if [ -z "$1" ]; then
    echo "Usage: ./run.sh <agent_name> [args...]"
    echo "Available agents:"
    echo "  - coordinator [request]"
    echo "  - problem_definition"
    echo "  - data_collection"
    echo "  - design_development"
    echo "  - training_optimization"
    echo "  - evaluation_validation"
    echo "  - deployment_monitoring"
    exit 1
fi

AGENT_NAME=$1
shift

python3 -m agent_factory.$AGENT_NAME.agent "$@"
