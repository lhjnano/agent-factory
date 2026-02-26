#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="$SCRIPT_DIR"
VENV_DIR="$AGENT_DIR/venv"

echo "================================"
echo "Multi-Agent MCP Server Setup"
echo "================================"
echo ""

check_postgres() {
    echo "Checking PostgreSQL..."
    
    # Docker Compose로 확인
    if [ -f "$AGENT_DIR/docker-compose.yml" ]; then
        if ! docker ps --format '{{.Names}}' | grep -q postgres; then
            echo "Starting PostgreSQL via Docker Compose..."
            cd "$AGENT_DIR"
            docker compose up -d postgres || docker-compose up -d postgres
        fi
        echo "✓ PostgreSQL is running (Docker Compose)"
        return
    fi
    
    # systemctl로 확인 시도 (systemd 기반 시스템)
    if command -v systemctl &> /dev/null; then
        if systemctl list-unit-files | grep -q postgresql; then
            if ! systemctl is-active --quiet postgresql; then
                echo "Starting PostgreSQL via systemctl..."
                sudo systemctl start postgresql
            fi
            echo "✓ PostgreSQL is running (systemd)"
            return
        fi
    fi
    
    # Docker로 확인 (docker run)
    if command -v docker &> /dev/null; then
        if ! docker ps --format '{{.Names}}' | grep -q postgres; then
            echo "Starting PostgreSQL via Docker..."
            docker run -d \
                --name agent-postgres \
                -e POSTGRES_PASSWORD=${DB_PASSWORD:-whiteduck} \
                -e POSTGRES_DB=postgres \
                -p 5432:5432 \
                postgres:15-alpine || true
            
            # 기존 컨테이너가 있으면 시작
            if ! docker ps | grep -q postgres; then
                docker start agent-postgres || true
            fi
        fi
        echo "✓ PostgreSQL is running (Docker)"
        return
    fi
    
    # PostgreSQL이 없으면 경고 후 계속 (선택적)
    echo "⚠ PostgreSQL not found (neither systemctl nor docker)"
    echo "  Running without database support"
    echo "  Install PostgreSQL for full functionality:"
    echo "    - System: sudo apt install postgresql postgresql-contrib"
    echo "    - Docker: docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=secret postgres:15"
    echo "    - Docker Compose: docker compose up -d (requires docker-compose.yml)"
}

setup_venv() {
    echo ""
    echo "Setting up virtual environment..."
    
    # venv 경로 확인 (이전 경로인 agents로 되어 있으면 다시 생성)
    if [ -d "$VENV_DIR" ]; then
        # pip 파일의 shebang 확인
        PIP_SHEBANG=$(head -1 "$VENV_DIR/bin/pip" 2>/dev/null || echo "")
        if [[ "$PIP_SHEBANG" == *"agents/venv"* ]]; then
            echo "  ⚠ Old venv detected (pointing to 'agents'), recreating..."
            rm -rf "$VENV_DIR"
            python3 -m venv "$VENV_DIR"
        else
            echo "  Virtual environment already exists, using existing..."
        fi
    else
        echo "  Creating new virtual environment..."
        python3 -m venv "$VENV_DIR"
    fi
    
    # venv 활성화
    source "$VENV_DIR/bin/activate"
    
    # venv의 pip 사용 (시스템 pip가 아닌)
    "$VENV_DIR/bin/pip" install --upgrade pip setuptools wheel
    "$VENV_DIR/bin/pip" install -e $SCRIPT_DIR

    echo "✓ Virtual environment ready"
}

install_dependencies() {
    echo ""
    echo "Installing dependencies..."
    
    cd "$AGENT_DIR"
    
    # venv의 pip 사용
    "$VENV_DIR/bin/pip" install "mcp>=1.0.0" "python-dotenv>=1.0.0"
    "$VENV_DIR/bin/pip" install "pandas>=2.0.0" "numpy>=2.0.0" "torch>=2.0.0" "scikit-learn>=1.5.0"
    "$VENV_DIR/bin/pip" install "psycopg2-binary>=2.9.0"
    
    for agent in problem_definition data_collection design_development training_optimization evaluation_validation deployment_monitoring coordinator; do
        req_file="$AGENT_DIR/$agent/requirements.txt"
        if [ -f "$req_file" ]; then
            "$VENV_DIR/bin/pip" install -r "$req_file" 2>/dev/null || true
        fi
    done
    
    echo "✓ Dependencies installed"
}

setup_databases() {
    echo ""
    echo "Setting up databases..."
    
    # PostgreSQL이 실행 중인지 확인
    PSQL_CMD=""
    if command -v psql &> /dev/null; then
        if command -v sudo &> /dev/null; then
            # systemd 기반 PostgreSQL
            PSQL_CMD="sudo -u postgres psql"
        else
            # Docker 기반 또는 직접 설치
            PSQL_CMD="psql -h localhost -U postgres"
        fi
    elif command -v docker &> /dev/null; then
        # Docker PostgreSQL
        PSQL_CMD="docker exec -it agent-postgres psql -U postgres"
    else
        echo "⚠ PostgreSQL not available, skipping database setup"
        return
    fi
    
    PGPASSWORD="${DB_PASSWORD:-whiteduck}"
    
    DBS=("data" "training" "evaluation" "monitoring")
    
    for db in "${DBS[@]}"; do
        $PSQL_CMD -c "CREATE DATABASE $db;" 2>/dev/null || true
        $PSQL_CMD -c "GRANT ALL PRIVILEGES ON DATABASE $db TO postgres;" 2>/dev/null || true
    done
    
    echo "✓ Databases ready"
}

setup_directories() {
    echo ""
    echo "Creating directories..."
    
    # /var/lib/agent-factory는 sudo 권한 필요
    if [ -w /var/lib ]; then
        mkdir -p /var/lib/agent-factory/{data,models,checkpoints,src,results,reports,deployments,logs}
    else
        echo "  Creating /var/lib/agent-factory (requires sudo)..."
        sudo mkdir -p /var/lib/agent-factory/{data,models,checkpoints,src,results,reports,deployments,logs}
        sudo chown -R $(whoami):$(whoami) /var/lib/agent-factory
    fi
    
    mkdir -p "$AGENT_DIR/workflows"
    echo "✓ Directories created"
}

create_env_file() {
    echo ""
    echo "Creating .env file..."
    cat > "$AGENT_DIR/.env" <<EOF
DB_PASSWORD=${DB_PASSWORD:-whiteduck}
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
EOF
    echo "✓ .env file created"
}

setup_opencode_config() {
    echo ""
    echo "Setting up OpenCode MCP configuration..."
    $SCRIPT_DIR/opencode-integrate.sh
    
    echo "✓ OpenCode MCP configuration created at $MCP_CONFIG"
}

test_mcp_server() {
    echo ""
    echo "Testing MCP server..."
    $SCRIPT_DIR/test-mcp.sh
}

print_usage() {
    echo ""
    echo "================================"
    echo "Installation Complete!"
    echo "================================"
    echo ""
    echo "Available MCP Tools:"
    echo "  - execute_workflow      : Run complete ML pipeline"
    echo "  - define_problem       : Define ML problem"
    echo "  - collect_data         : Collect data from sources"
    echo "  - preprocess_data      : Clean and preprocess data"
    echo "  - design_model         : Design model architecture"
    echo "  - generate_code        : Generate model code"
    echo "  - train_model          : Train with optimization"
    echo "  - evaluate_model       : Evaluate performance"
    echo "  - deploy_model         : Deploy to production"
    echo "  - monitor_deployment   : Monitor running model"
    echo ""
    echo "Usage in OpenCode:"
    echo "  The MCP server is automatically loaded in OpenCode"
    echo "  Access tools via MCP client or OpenCode interface"
    echo ""
    echo "Manual Testing:"
    echo "  cd $AGENT_DIR"
    echo "  source venv/bin/activate"
    echo "  python -m agent_factory.mcp_server"
    echo ""
    echo "PostgreSQL Management:"
    echo "  Docker Compose (recommended):"
    echo "    docker compose up -d"
    echo "    docker compose down"
    echo "  Docker (alternative):"
    echo "    docker run -d -p 5432:5432 --name agent-postgres -e POSTGRES_PASSWORD=secret postgres:15"
    echo "  System (requires PostgreSQL installed):"
    echo "    sudo systemctl start postgresql"
    echo ""
    echo "Configuration:"
    echo "  MCP Config: ~/.config/opencode/mcp.json"
    echo "  Agent Config: $AGENT_DIR/.env"
    echo ""
}

main() {
    check_postgres
    setup_venv
    install_dependencies
    setup_databases
    setup_directories
    create_env_file
    setup_opencode_config
    test_mcp_server
    print_usage
}

main "$@"
