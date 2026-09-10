#!/usr/bin/env bash
set -e

echo "=== Baidu Baike MCP Server Setup ==="

# Check Python command
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD=python
else
    echo "Error: Python 3.12+ is required but python was not found on PATH." >&2
    exit 1
fi

echo "Using Python: $($PYTHON_CMD --version)"

# Check uv
if command -v uv >/dev/null 2>&1; then
    echo "Found 'uv', setting up environment..."
    uv sync
    echo "Running tests..."
    uv run pytest tests/
    echo ""
    echo "Setup complete! Start server with: uv run python -m baidu_baike_mcp"
else
    echo "Creating standard venv..."
    $PYTHON_CMD -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -e .
    pip install pytest pytest-asyncio
    echo "Running tests..."
    pytest tests/
    echo ""
    echo "Setup complete! Start server with: .venv/bin/python -m baidu_baike_mcp"
fi
