#!/bin/bash

# Test script for npm package wrapper

set -e

echo "================================"
echo "Agent Factory NPM Package Test"
echo "================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR"

echo "Testing npm package wrapper..."
echo ""

# Test 1: Check package.json exists
echo "1. Checking package.json..."
if [ -f "package.json" ]; then
    echo "   ✓ package.json found"
else
    echo "   ✗ package.json not found"
    exit 1
fi

# Test 2: Check index.js exists and is executable
echo ""
echo "2. Checking index.js..."
if [ -f "index.js" ]; then
    echo "   ✓ index.js found"
    if [ -x "index.js" ]; then
        echo "   ✓ index.js is executable"
    else
        echo "   ⚠ index.js is not executable (Node.js doesn't require this)"
    fi
else
    echo "   ✗ index.js not found"
    exit 1
fi

# Test 3: Try to parse package.json
echo ""
echo "3. Parsing package.json..."
node -e "
const pkg = require('./package.json');
console.log('   Name:', pkg.name);
console.log('   Version:', pkg.version);
console.log('   ✓ Valid JSON');
"

# Test 4: Try to run wrapper (without launching MCP server)
echo ""
echo "4. Testing wrapper script..."
echo "   Checking if wrapper can be parsed..."
node -c index.js
echo "   ✓ Wrapper syntax is valid"

# Test 5: Check if Agent Factory is accessible
echo ""
echo "5. Checking Agent Factory installation..."
AGENT_DIR="$(cd .. && pwd)"
if [ -d "$AGENT_DIR/src/agent_factory" ]; then
    echo "   ✓ Agent Factory found at: $AGENT_DIR"
else
    echo "   ⚠ Agent Factory not found in expected location"
    echo "   This is OK if you have AGENT_FACTORY_PATH set"
fi

# Test 6: Check Python
echo ""
echo "6. Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "   ✓ Python found: $PYTHON_VERSION"
else
    echo "   ✗ Python3 not found"
    exit 1
fi

# Test 7: Check virtual environment
echo ""
echo "7. Checking virtual environment..."
if [ -d "$AGENT_DIR/venv" ]; then
    echo "   ✓ Virtual environment found at: $AGENT_DIR/venv"
else
    echo "   ⚠ No virtual environment found (will use system Python)"
fi

echo ""
echo "================================"
echo "All checks passed! ✓"
echo "================================"
echo ""
echo "To install this package locally:"
echo "  cd $SCRIPT_DIR"
echo "  npm link"
echo ""
echo "To test the MCP server:"
echo "  npx -y @purpleraven/agent-factory"
echo ""
echo "To publish to npm:"
echo "  npm publish --access public"
