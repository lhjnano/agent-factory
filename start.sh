#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Start PostgreSQL if not running
if ! systemctl is-active --quiet postgresql; then
    echo "Starting PostgreSQL..."
    systemctl start postgresql
fi

# Activate virtual environment
source "$SCRIPT_DIR/venv/bin/activate"

# Load environment variables
cd "$SCRIPT_DIR"
export $(cat .env | xargs)

echo "Environment ready!"
echo "PostgreSQL: Running"
echo "Virtual Environment: Activated"
echo "DB_PASSWORD: Set"
